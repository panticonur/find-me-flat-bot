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
REQUEST_UPDATES_TIMEOUT = 5
PARSER_DELAY = 500


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

debug = True
debug2 = False
restart = 0


if not os.path.exists(data_dir):
    os.makedirs(data_dir)


def add_chat(chat_id, tag, url):
    chats[chat_id] = {'url': url, 'tag': tag}
    save_json(chats_path, chats)
    log(u"Added chat {}: #{} {}".format(chat_id, tag, url))


def set_delay(chat_id, time):
    time = int(time)
    chats[chat_id]['delay'] = time
    save_json(chats_path, chats)
    log(u"Set chat delay {}: {}".format(chat_id, time))


def remove_chat(chat_id):
    if chat_id in chats:
        tag = chats[chat_id]['tag']
        del chats[chat_id]
        save_json(chats_path, chats)
        log(u"Chat {}: Removed from queue".format(str(chat_id)))
        return tag


def load_telegram_method(method, params):
    global debug
    unicode_params = {}
    for k, v in params.items():
        val = v.encode("utf8") if isinstance(v, str) else v
        unicode_params[k] = val

    params_str = urllib.parse.urlencode(unicode_params)
    url = u"https://api.telegram.org/bot{}/{}?{}".format(BOT_TOKEN,
                                                         method,
                                                         params_str)
    if debug:
        log(url)
    readed = opener.open(url).read()
    if debug:
        log("load_telegram_method {}".format(method))
    jsn = json.loads(readed)#, encoding="utf-8")
    if debug:
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
    global debug, debug2
    log(u"Bot started")
    offset = 0

    while True:

        if debug:
            log(u"Updating {}".format(offset))
        try:
            updates_response = request_updates(offset)
            updates = updates_response.get("result", [])
        except Exception as e: # urllib2.HTTPError, e:
            log("EXCEPTION updater:")
            print(e) #print "Unexpected error:", sys.exc_info()[0]
            if debug:
                raise
            continue

        if debug2:
            log("bot_updater() new responce:")
            print(updates)

        if len(updates) > 0:
            offset = updates[-1].get("update_id", offset) + 1
            message_updates = filter(
                lambda u: "message" in u and "text" in u["message"],
                updates)
            for upd in message_updates:
                text = upd["message"]["text"]
                chat_id = str(upd["message"]["chat"]["id"])
                log("got message (chat:{}): {}".format(chat_id, text))
                try:
                    handle_message(chat_id, text)
                except Exception as e:
                    log("EXCEPTION handle_message (chat:{})".format(chat_id))
                    print(e)
                    if debug:
                        raise


def handle_message(chat_id, message):
    global parser_countdown
    global parser_delay
    global debug

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
            parser_countdown = 2
        else:
            send_message(chat_id, "Usage: /start <tag> <cian_url>")

    elif message == "/stop":
        log("Stop")
        chat = chats.get(chat_id, False)
        tag = remove_chat(chat_id)
        send_message(chat_id, "Stop scanning #{}\n{}".format(tag, chat['url']))

    if message == "/stat":
        log("Stat")
        chat = chats.get(chat_id, False)
        msg = "chat not found!"
        if chat:
            msg = "#{}  delay: {} {}".format(
                chat['tag'], parser_delay, parser_countdown)
        log(msg)
        send_message(chat_id, msg)
    if message == "/status":
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
        send_message(chat_id, u"files removed")
    if message == u"/debug":
        debug = not debug
        cian.debug = not cian.debug
        msg = u"Debug " + (u"enabled" if debug else u"disabled")
        log(msg)
        send_message(chat_id, msg)

    if message == u"/scan":
        parser_countdown = 1
        log("Scan")

    if message == u"/restart":
        log(u"Restart")
        global restart
        restart += 1
        if restart>1:
            send_message(chat_id, u"restarting")
            python = sys.executable
            os.execl(python, python, * sys.argv)
            raise SystemExit
        else:
            log(u"  skip restart")
            send_message(chat_id, u"try again")
    if message.find(u"/delay") == 0:
        log(u"Delay")
        parts = message.split(u" ")
        if len(parts) == 2:
            parser_delay = int(parts[1])
            parser_countdown = parser_delay
            log(u"  parser_delay set to {}".format(parser_delay))
            #set_delay(chat_id, parts[1])
            send_message(chat_id, u"Scanning delay is set to {}s".format(parts[1]))
        else:
            send_message(chat_id, u"Usage: /delay <seconds>")                 


def cian_parser_thread():
    global parser_countdown
    global parser_delay

    while True:
        chats_copy = chats.copy()

        if len(chats_copy)==0:
            log(u"sleep: {}s".format(parser_delay))
            parser_countdown = parser_delay
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1

        for chat_id, chat in chats_copy.items():
            parser_countdown = parser_delay
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1

            log("{ parsing {} {}".format(chat_id, chat['url' if debug else 'tag']))
            hata_refs, onpage_links_count = cian.parse(known_path, chat['url'])
            log("} parsed {}, total_onpage_links {}".format(len(hata_refs), onpage_links_count))
            if debug:
                print(hata_refs)
            if hata_refs is None: # fail
                continue

            if len(hata_refs) > 0:
                for ref in hata_refs:
                    send_message(chat_id, ref)
                    log("  parser: "+ref)

            elif debug:
                msg = "no new hata-refs #"+chats[chat_id]['tag']
                send_message(chat_id, msg)
                log("  parser: "+msg)

            if onpage_links_count<1:
                msg = "Warning!\nGot no links on the page #{}\nCheck CIAN captcha!".format(
                                chats[chat_id]['tag'])
                send_message(chat_id, msg)
                log(u"  parser: "+msg)


def main():
    gevent.joinall([
        gevent.spawn(bot_updater_thread),
        gevent.spawn(cian_parser_thread),
    ])

if __name__ == "__main__":
    main()
