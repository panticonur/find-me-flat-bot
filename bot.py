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


TOKEN='5712465853:AAEh9ewqzcrLwFw8PA90MAKKowR_TtpTqGk'
# pnt_flat_bot PntFlatBot
PROXY_HOST = 'pryatki.dev'
PROXY_PORT = 31337
PROXY_USER = 'vasya'
PROXY_PSWRD = '123123123'
REQUEST_UPDATES_TIMEOUT = 45
PARSER_DELAY = 500


opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PSWRD))
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
    #global debug
    unicode_params = {}
    for k, v in params.items():
        val = v.encode("utf8") if isinstance(v, str) else v
        unicode_params[k] = val

    params_str = urllib.parse.urlencode(unicode_params)
    #token = os.environ["TG_BOT_TOKEN"]
    url = u"https://api.telegram.org/bot{}/{}?{}".format(TOKEN,
                                                         method,
                                                         params_str)
    readed = opener.open(url).read()
    #if debug:
    #    log(u"load_telegram_method {} raw:\n".format(method)+readed)
    return json.loads(readed, encoding="utf-8")
    #return json.load(urllib2.urlopen(url), encoding="utf-8")


def request_updates(offset):
    params = {u"offset": offset,
              u"timeout": REQUEST_UPDATES_TIMEOUT}
    return load_telegram_method("getUpdates", params)


def send_message(chat_id, message):
    params = {u"chat_id": chat_id,
              u"text": message}
    return load_telegram_method("sendMessage", params)


def updater():
    global debug
    log(u"Bot started")
    offset = 0
    while True:
        if debug:
            log(u"Updating {}".format(offset))
        try:
            updates_response = request_updates(offset)
            updates = updates_response.get("result", [])
        except Exception as e: # urllib2.HTTPError, e:
            log(u"EXCEPTION updater:")
            print(e) #print "Unexpected error:", sys.exc_info()[0]
            if debug:
                raise
            continue
        #log(u"updater new data")
        #print(updates)
        if len(updates) > 0:
            offset = updates[-1].get("update_id", offset) + 1
            message_updates = filter(
                lambda u: "message" in u and "text" in u["message"],
                updates)
            for upd in message_updates:
                text = upd["message"]["text"]
                chat_id = str(upd["message"]["chat"]["id"])
                #log(u"got message (chat:{}): {}".format(chat_id, text))
                try:
                    handle_message(chat_id, text)
                except Exception as e:
                    log(u"EXCEPTION handle_message (chat:{})".format(chat_id))
                    print(e)
                    if debug:
                        raise


def handle_message(chat_id, message):
    global parser_countdown
    global parser_delay
    global debug
    if message == u"/help":
        log(u"Help")
        send_message(chat_id,
                     u"/start <tag> <url>\n/stop\n/stat[us]\n/scan")
    if message.find(u"/start") == 0:
        log(u"Start")
        parts = message.split(u" ")
        if len(parts) == 3:
            add_chat(chat_id, parts[1], parts[2])
            send_message(chat_id, u"Start scanning #"+parts[1])
            parser_countdown = 2
        else:
            send_message(chat_id, u"Usage: /start <tag> <cian_url>")
    elif message == u"/stop":
        log(u"Stop")
        chat = chats.get(chat_id, False)
        tag = remove_chat(chat_id)
        if tag:
            send_message(chat_id, u"Stop scanning #{}\n{}".format(tag, chat['url']))
    if message == u"/stat":
        log(u"Stat")
        chat = chats.get(chat_id, False)
        msg = u"chat not found!"
        if chat:
            msg = u"#{}  delay: {} {}".format(
                chat['tag'], parser_delay, parser_countdown)
        log(msg)
        send_message(chat_id, msg)
    if message == u"/status":
        if debug:
            log(u"Status  {}".format(json.dumps(chats)))
        else:
            log(u"Status")
        chat = chats.get(chat_id, False)
        msg = u"chat not found!\ndebug:"+str(debug)
        if chat:
            msg = u"#{}  delay: {} {}  debug: {}\n{}".format(
                chat['tag'], parser_delay, parser_countdown, debug, chat['url'])
        log(msg)
        send_message(chat_id, msg)
    if message == u"/clear":
        log(u"Clear")
        try:
            os.remove(chats_path)
        except:
            log(u"error remove "+chats_path)
        try:
            os.remove(known_path)
        except:
            log(u"error remove "+known_path)
        try:
            os.remove(page_path)
        except:
            log(u"error remove "+page_path)
        send_message(chat_id, u"files removed")
    if message == u"/debug":
        debug = not debug
        cian.debug = not cian.debug
        msg = u"Debug " + (u"enabled" if debug else u"disabled")
        log(msg)
        send_message(chat_id, msg)
    if message == u"/scan":
        parser_countdown = 1
        log(u"Scan")
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


def parser():
    global parser_countdown
    global parser_delay
    while True:
        chats_copy = chats.copy()
        if len(chats_copy)==0:
            log(u"sleep: {}s".format(parser_delay))
            parser_countdown = parser_delay
            while parser_countdown>0:
                if len(chats)!=0:
                    break
                gevent.sleep(1)
                parser_countdown -= 1
        for chat_id, chat in chats_copy.items():
            parser_countdown = parser_delay
            while parser_countdown>0:
                gevent.sleep(1)
                parser_countdown -= 1
            log(u"Parsing {} {}".format(chat_id, chat['url' if debug else 'tag']))
            refs, page_links = cian.parse(known_path, chat['url'])
            if refs is None:
                continue
            #log(u"  parsed {}, page_links {}".format(len(refs), page_links))
            if debug:
                print(refs)
            msg = False
            if len(refs) > 0:
                for ref in refs:
                    #msg = u"#"+chat['tag']+u"\n"+ref
                    msg = ref
                    send_message(chat_id, msg)
                    log(u"  parser: "+msg)
            elif debug:
                msg = u"no new refs #"+chats[chat_id]['tag']
                send_message(chat_id, msg)
                log(u"  parser: "+msg)
            if page_links<1:
                msg = u"Warning!\nGot no links on the page #{}\nCheck CIAN captcha!".format(
                                chats[chat_id]['tag'])
                send_message(chat_id, msg)
                log(u"  parser: "+msg)


def main():
    gevent.joinall([
        gevent.spawn(updater),
        gevent.spawn(parser),
    ])

if __name__ == "__main__":
    main()
