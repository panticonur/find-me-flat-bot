import json
from datetime import datetime
import os
import os.path


TRUE_VALUES = ("1", "true", "yes", "on")


def log(message):
    print("[{}] {}".format(str(datetime.now()), message))


def env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES

def load_json(fname, default_value):
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
