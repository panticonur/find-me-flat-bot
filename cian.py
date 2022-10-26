import urllib
from bs4 import BeautifulSoup
from utils import log, save_json, load_json
import os

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
debug = True
debug2 = True
page_path = ""

def get_known_refs(known_path):
    return set(load_json(known_path, set()))


def save_known_refs(known_path, data):
    save_json(known_path, list(data))


def get_page(url):
    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "User-Aget": USER_AGENT}
    request = urllib.request.Request(url, headers=headers)
    page = urllib.request.urlopen(request)
    data = page.read()
    return data


def get_local_page():
    with open(page_path, "r") as f:
        return f.read()

def save_to_local_page(data):
    with open(page_path, "w") as f:
        return f.write(str(data))

def has_class(el, str):
    classes = el.attrs.get("class", [])
    for cls in classes:
        if str in cls:
            return True
    return False


def is_flat_link(el):
    href = get_link_href(el)
    if href is None:
        return False

    if href.find("https://www.cian.ru/rent/flat/") != 0:
        return False

    parent = el.parent
    while parent:
        if has_class(parent, "wrapper"):
            break
        parent = parent.parent

    if parent is None:
        return False
    for ch in  parent.children:
        if has_class(ch, "moreSuggestionsButtonContainer") or \
                has_class(ch, "title"):
            return False
    return True


def get_link_href(el):
    return el.attrs.get("href", None)


def get_flat_refs(data):
    global debug
    soup = BeautifulSoup(data, 'html.parser')
    links = soup.find_all('a')
    if debug:
        log("get_flat_refs() total links "+str(len(links)))
    flat_links = filter(is_flat_link, links)

    flat_refs = map(get_link_href, flat_links)
    return set(filter(lambda h: h is not None, flat_refs)), len(links)



def parse(known_path, url):
    global debug, debug2
    try:
        page_data = get_page(url)
    except Exception as e: # urllib2.HTTPError, e:
        log("EXCEPTION get_page:")
        print(e) #print "Unexpected error:", sys.exc_info()[0]
        if debug:
            raise
        return None, None
    if debug2:
        print(page_data)
    save_to_local_page(page_data)
    #page_data = get_local_page()
    refs, links_count = get_flat_refs(page_data)
    if debug:
        print("cian.parse() refs:")
        print(refs)
    known_refs = get_known_refs(known_path)
    new_refs = refs - known_refs
    log("    {} cian refs(new: {}, known: {})  links: {}".format(len(refs),
                                                                 len(new_refs),
                                                                 len(known_refs),
                                                                 links_count))
    if len(new_refs) > 0:
        new_known_refs = known_refs.union(new_refs)
        save_known_refs(known_path, new_known_refs)
        return list(new_refs), links_count
    return [], links_count
