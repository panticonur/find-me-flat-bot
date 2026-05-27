import json
from datetime import datetime
import os.path
# import time


def log(message):
    print("[{}] {}".format(str(datetime.now()), message))
    # print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Open Chrome")

def load_json(fname, default_value):
    log("load_json({})".format(fname))
    if not os.path.isfile(fname):
        return default_value
    with open(fname, "r") as fp:
        try:
            data = json.load(fp)
        except ValueError as e:
            print("EXCEPTION load json:")
            print(e)
            data = default_value
        return data


def save_json(fname, data):
    with open(fname, "w") as fp:
        json.dump(data, fp)
