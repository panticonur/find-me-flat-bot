from time import sleep
import gevent
import json
import os
import sys
from dotenv import load_dotenv
import urllib.request
import urllib.parse
from gevent.monkey import patch_all
import cian
from utils import log, save_json, load_json

load_dotenv()
debug = bool(os.getenv('DEBUG', 0))
verbose = bool(os.getenv('VERBOSE', 0))
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
REQUEST_UPDATES_INTERVAL = os.getenv("REQUEST_UPDATES_INTERVAL", 45)
PARSER_GAP = os.getenv("REQUEST_UPDATES_INTERVAL", 600)
log("DEBUG = {}".format(debug))
log("VERBOSE = {}".format(verbose))
log("TG_BOT_TOKEN = {}".format(TG_BOT_TOKEN))
log("REQUEST_UPDATES_INTERVAL = {}".format(REQUEST_UPDATES_INTERVAL))
log("PARSER_GAP = {}".format(PARSER_GAP))
data_dir = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
known_path = os.path.join(data_dir, "known.json")
page_path = os.path.join(data_dir, "page.html")
chats_path = os.path.join(data_dir, "chats.json")
chats = load_json(chats_path, {})
url = ""
parser_gap = int(PARSER_GAP)
parser_countdown = int(PARSER_GAP)
restart = 0
cian.verbose = verbose
cian.debug = debug
cian.page_path = page_path
print(chats)
https_handler = urllib.request.HTTPSHandler()
opener = urllib.request.build_opener(https_handler)
patch_all()


def load_telegram_method(method, params):
    global debug, verbose
    params_str = urllib.parse.urlencode(params)
    url = "https://api.telegram.org/bot{}/{}?{}".format(TG_BOT_TOKEN,
                                                        method, params_str)
    if debug:
        print("  *( load telegram method: {}".format(method))
        print(url)
    readed = opener.open(url).read()
    if debug:
        print("  *) done {}".format(method))
    jsn = json.loads(readed.decode("utf-8"))
    if debug:
        print("  *: readed")
        print(jsn)
    return jsn


def request_updates(offset):
    params = {u"offset": offset,
              u"timeout": REQUEST_UPDATES_INTERVAL}
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
    global parser_countdown, parser_gap

    if message == "/help":
        log("Help")
        send_message(chat_id,
                     "/start\n/url <tag> <url>\n/stop\n/stat[us]\n/scan\ngap <seconds>")

    if message.find("/start") == 0:
        log("Start")
        add_chat(chat_id, "tag", "url")
        send_message(chat_id, "Start")
        parser_countdown = 3

    if message.find("/url") == 0:
        log("Url")
        parts = message.split(" ")
        if len(parts) == 2:
            url = parts[1]
            for chat in chats:
            send_message(chat_id, "Url\n"+url)
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
                chat['tag'], parser_gap, parser_countdown)
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
                chat['tag'], parser_gap, parser_countdown, debug, chat['url'])
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
            parser_gap = int(parts[1])
            parser_countdown = parser_gap
            log("  parser_delay set to {}".format(parser_gap))
            #set_delay(chat_id, parts[1])  # NOT WORKING
            send_message(chat_id, "Scanning delay is set to {}s".format(parts[1]))
        else:
            send_message(chat_id, u"Usage: /delay <seconds>")


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
        log("    remove chat {}: #{}".format(chat_id, tag))
        return tag


def cian_parser_thread():
    global debug, verbose
    global parser_countdown, parser_gap
    log("Cian page parser thread started")

    while True:
        chats_copy = chats.copy()

        if len(chats_copy)==0:
            log("Sleep: {}s".format(parser_gap))
            parser_countdown = parser_gap
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1

        for chat_id, chat in chats_copy.items():
            parser_countdown = parser_gap
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
    gevent.joinall([
        gevent.spawn(cian_parser_thread),
        gevent.spawn(bot_updater_thread),
    ])

if __name__ == "__main__":
    main()
