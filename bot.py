from time import sleep
import gevent
import json
import os
import sys
from dotenv import load_dotenv
import urllib.request
import urllib.parse
import cian
from utils import log, save_json, load_json
from gevent.monkey import patch_all
# Apply gevent monkey patch before importing or initializing network state.
patch_all()

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
chats = load_json(chats_path, [])
url_path = os.path.join(data_dir, "url.json")
url = load_json(url_path, "")
print("url: "+url)
parser_gap = int(PARSER_GAP)
parser_countdown = int(PARSER_GAP)
restart = 0
cian.verbose = verbose
cian.debug = debug
cian.page_path = page_path
print("chats: "+str(chats))
https_handler = urllib.request.HTTPSHandler()
opener = urllib.request.build_opener(https_handler)


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
    global debug, verbose, url
    global parser_countdown, parser_gap

    if message == "/help":
        log("Help")
        send_message(chat_id,
                     "/start\n/url <url>\n/stop\n/status\n/scan\ngap <seconds>")

    if message.find("/start") == 0:
        log("Start "+chat_id)
        chats.append(chat_id)
        save_json(chats_path, chats)
        log("    add chat "+chat_id)
        send_message(chat_id, "Started")
        parser_countdown = 3

    if message.find("/url") == 0:
        
        parts = message.split(" ")
        if len(parts) == 2:
            url = parts[1]
            save_json(url_path, url)
            log("Url "+url)
            for chat in chats:
                send_message(chat, "Url\n"+url)
            parser_countdown = 3
        else:
            log("Url")
            send_message(chat_id, 
                         "Set url: /url <cian_url>\nCurrent url: "+url)

    elif message == "/stop":
        log("Stop")
        if chat_id in chats:
            chats.remove(chat_id)
            save_json(chats_path, chats)
            log("    remove chat "+chat_id)
        send_message(chat_id, "Stopped")

    if message == "/status":
        if debug:
            log("Status  {}".format(json.dumps(chats)))
        else:
            log("Status")
        msg = "gap: {}/{}\ndebug: {}".format(
            parser_countdown, parser_gap, debug)
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

    if message.find("/gap") == 0: 
        log("Gap")
        parts = message.split(" ")
        if len(parts) == 2:
            parser_gap = int(parts[1])
            parser_countdown = parser_gap
            log("  parser_gap set to {}".format(parser_gap))
            send_message(chat_id, "Scanning gap is set to {}s".format(parser_gap))
        else:
            send_message(chat_id, u"Usage: /gap <seconds>")


def cian_parser_thread():
    global debug, verbose
    global parser_countdown, parser_gap
    log("Cian page parser thread started")

    while True:
        chats_copy = chats.copy()

        log("Sleep: {}s".format(parser_gap))
        parser_countdown = parser_gap
        while parser_countdown>0:
            gevent.sleep(1)
            parser_countdown -= 1

        if len(chats_copy)==0:
            continue

        log("{{ parsing: \"{}\"".format(url))
        new_cian_refs, onpage_links_count = cian.parse(known_path, url)
        if new_cian_refs is None:
            log("}}")
        else:
            log("}} parsed {}, onpage_links_count {}".format(
                len(new_cian_refs), onpage_links_count))

        if debug:
            print(new_cian_refs)
        if new_cian_refs is not None and len(new_cian_refs)>0:
            for ref in new_cian_refs:
                for chat in chats_copy:
                    send_message(chat, ref)
                if verbose:
                    log(ref)
                gevent.sleep(1)

        elif debug:
            msg = "no new cian refs"
            for chat in chats_copy:
                send_message(chat, msg)
            if verbose:
                log(msg)

            if onpage_links_count is None or onpage_links_count<5:
                msg = "Warning!\nGot no links on the page!\nCheck CIAN captcha!"
                for chat in chats_copy:
                    send_message(chat, msg)
                log(msg)


def main():
    gevent.joinall([
        gevent.spawn(cian_parser_thread),
        gevent.spawn(bot_updater_thread),
    ])

if __name__ == "__main__":
    main()
