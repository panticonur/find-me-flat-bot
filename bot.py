from time import sleep
import gevent
import json
import os
import sys
import socket
import socks
from gevent.monkey import patch_all
import cian
from utils import log, save_json, load_json
import urllib
from sockshandler import SocksiPyHandler


BOT_TOKEN='5712465853:AAEh9ewqzcrLwFw8PA90MAKKowR_TtpTqGk'
# pnt_flat_bot PntFlatBot

PROXY_HOST = 'pryatki.dev'
PROXY_PORT = 31337
PROXY_USER = 'vasya'
PROXY_PSWRD = '123123123'
REQUEST_UPDATES_TIMEOUT = 45
PARSER_DELAY = 600


#proxy_handler = SocksiPyHandler(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PSWRD)
https_handler = urllib.request.HTTPSHandler()
opener = urllib.request.build_opener(https_handler)
patch_all()
messages_queue = []
data_dir = os.path.join(os.path.dirname(__file__), "data")
CHATS_FILE = "chats.json"
KNOWN_FILE = "known.json"
PAGE_FILE = "page.html"
chats_path = os.path.join(data_dir, CHATS_FILE)
known_path = os.path.join(data_dir, KNOWN_FILE)
page_path = os.path.join(data_dir, PAGE_FILE)
chats = load_json(chats_path, {})
parser_delay = PARSER_DELAY
parser_countdown = PARSER_DELAY

debug = False
verbose = False
restart = 0

cian.debug = debug
cian.verbose = verbose
cian.page_path = page_path


if not os.path.exists(data_dir):
    os.makedirs(data_dir)


def add_chat(chat_id, tag, url):
    chats[chat_id] = {'url': url, 'tag': tag}
    save_json(chats_path, chats)
    log("    add chat {}: #{} {}".format(chat_id, tag, url))


def set_delay(chat_id, time): # NOT WORKING
    time = int(time)
    chats[chat_id]['delay'] = time
    save_json(chats_path, chats)
    log("    set chat delay {}: {}".format(chat_id, time))


def remove_chat(chat_id):
    if chat_id in chats:
        tag = chats[chat_id]['tag']
        del chats[chat_id]
        save_json(chats_path, chats)
        log("    remove chat {}: #{}".format(str(chat_id, tag)))
        return tag


def load_telegram_method(method, params):
    global debug, verbose
    unicode_params = {}
    for k, v in params.items():
        val = v.encode("utf8") if isinstance(v, str) else v
        unicode_params[k] = val

    params_str = urllib.parse.urlencode(unicode_params)
    url = u"https://api.telegram.org/bot{}/{}?{}".format(BOT_TOKEN,
                                                         method,
                                                         params_str)
    if verbose:
        print("  *( load telegram method: {}".format(method))
    if debug:
        print(url)
    readed = opener.open(url).read()
    if verbose:
        print("  *) done {}".format(method))
    jsn = json.loads(readed)#, encoding="utf-8")
    if debug:
        print("  *: readed")
        print(jsn)
    return jsn


def request_updates(offset):
    params = {u"offset": offset,
              u"timeout": REQUEST_UPDATES_TIMEOUT}
    return load_telegram_method("getUpdates", params)


def send_message(chat_id, message):
    params = {u"chat_id": chat_id,
              u"text": message}
    return load_telegram_method("sendMessage", params)


def bot_updater_thread():
    global debug, verbose
    log("Bot thread started")
    offset = 0

    while True:

        if verbose:
            log("Bot updating {}".format(offset))
        try:
            updates_response = request_updates(offset)
            updates = updates_response.get("result", [])
        except Exception as e: # urllib2.HTTPError, e:
            log("EXCEPTION Bot updater:")
            print(e) #print "Unexpected error:", sys.exc_info()[0]
            if debug:
                raise
            continue

        if debug:
            print("Bot updates:")
            print(updates)

        if len(updates) > 0:
            offset = updates[-1].get("update_id", offset) + 1
            message_updates = filter(
                lambda u: "message" in u and "text" in u["message"],
                updates)
            for upd in message_updates:
                text = upd["message"]["text"]
                chat_id = str(upd["message"]["chat"]["id"])
                if verbose:
                    log("Got message (chat:{}): {}".format(chat_id, text))
                try:
                    handle_message(chat_id, text)
                except Exception as e:
                    log("EXCEPTION handle_message (chat:{})".format(chat_id))
                    print(e)
                    if debug:
                        raise


def handle_message(chat_id, message):
    global debug, verbose
    global parser_countdown, parser_delay

    if message == "/help":
        log("Help")
        send_message(chat_id,
                     "/start <tag> <url>\n/stop\n/stat[us]\n/scan")

    if message.find("/start") == 0:
        log("Start")
        parts = message.split(" ")
        if len(parts) == 3:
            add_chat(chat_id, parts[1], parts[2])
            send_message(chat_id, "Start scanning #"+parts[1])
            parser_countdown = 3
        else:
            send_message(chat_id, "Usage: /start <tag> <cian_url>")

    elif message == "/stop":
        log("Stop")
        chat = chats.get(chat_id, False)
        tag = remove_chat(chat_id)
        send_message(chat_id, "Stop scanning #{}\n{}".format(tag, chat['url']))

    if message == "/stat":  # NOT WORKING
        log("Stat")
        chat = chats.get(chat_id, False)
        msg = "chat not found!"
        if chat:
            msg = "#{}  delay: {} {}".format(
                chat['tag'], parser_delay, parser_countdown)
        log(msg)
        send_message(chat_id, msg)

    if message == "/status":  # NOT WORKING
        if debug:
            log("Status  {}".format(json.dumps(chats)))
        else:
            log("Status")
        chat = chats.get(chat_id, False)
        msg = "chat not found!\ndebug:"+str(debug)
        if chat:
            msg = "#{}  delay: {} {}  debug: {}\n{}".format(
                chat['tag'], parser_delay, parser_countdown, debug, chat['url'])
        log(msg)
        send_message(chat_id, msg)

    if message == "/clear":
        log("Clear")
        try:
            os.remove(chats_path)
        except:
            log("error remove "+chats_path)
        try:
            os.remove(known_path)
        except:
            log("error remove "+known_path)
        try:
            os.remove(page_path)
        except:
            log("error remove "+page_path)
        send_message(chat_id, "files removed")

    if message == "/debug":
        debug = not debug
        cian.debug = not cian.debug
        msg = "Debug " + ("enabled" if debug else "disabled")
        log(msg)
        send_message(chat_id, msg)

    if message == "/scan":
        parser_countdown = 1
        log("Scan")

    if message == "/restart":
        log("Restart")
        global restart
        restart += 1
        if restart>1:
            send_message(chat_id, u"restarting")
            python = sys.executable
            os.execl(python, python, * sys.argv)
            raise SystemExit
        else:
            log("  skip restart")
            send_message(chat_id, u"try again")

    if message.find("/delay") == 0: 
        log("Delay")
        parts = message.split(" ")
        if len(parts) == 2:
            parser_delay = int(parts[1])
            parser_countdown = parser_delay
            log("  parser_delay set to {}".format(parser_delay))
            #set_delay(chat_id, parts[1])  # NOT WORKING
            send_message(chat_id, "Scanning delay is set to {}s".format(parts[1]))
        else:
            send_message(chat_id, u"Usage: /delay <seconds>")


def cian_parser_thread():
    global debug, verbose
    global parser_countdown, parser_delay
    log("Cian page parser thread started")

    while True:
        chats_copy = chats.copy()

        if len(chats_copy)==0:
            log("Sleep: {}s".format(parser_delay))
            parser_countdown = parser_delay
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1

        for chat_id, chat in chats_copy.items():
            parser_countdown = parser_delay
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1

            log("{{ parsing {} {}".format(chat_id, chat['url' if debug else 'tag']))
            new_cian_refs, onpage_links_count = cian.parse(known_path, chat['url'])
            if new_cian_refs is None: # fail
                log("}}")
                continue
            log("}} parsed {}, onpage_links_count {}".format(len(new_cian_refs), onpage_links_count))

            if debug:
                print(new_cian_refs)
            if len(new_cian_refs) > 0:
                for ref in new_cian_refs:
                    send_message(chat_id, ref)
                    if verbose:
                        log(ref)
                    gevent.sleep(1)

            elif debug:
                msg = "no new cian refs #"+chat['tag']
                send_message(chat_id, msg)
                if verbose:
                    log(msg)

            if onpage_links_count<2:
                msg = "Warning!\nGot no links on the page #{}\nCheck CIAN captcha!".format(chat['tag'])
                send_message(chat_id, msg)
                log(msg)


def main():
    global debug, verbose
    
    verbose = bool(os.getenv('VERBOSE', verbose))
    log("VERBOSE = {}".format(verbose))
    
    debug = bool(os.getenv('DEBUG', debug))
    log("DEBUG = {}".format(debug))

    gevent.joinall([
        gevent.spawn(cian_parser_thread),
        gevent.spawn(bot_updater_thread),
    ])

if __name__ == "__main__":
    main()
