import json
import logging
import sys

DEFAULT_CONFIG = "/data/options.json"


def load_config(path=DEFAULT_CONFIG):
    with open(path) as f:
        return json.load(f)


def setup_logging(config):
    log = logging.getLogger("dropbox_upload")
    log.setLevel(logging.DEBUG if config.get("debug") else logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    # Remove existing handlers. This should be an issue in unit tests.
    log.handlers = []
    log.addHandler(ch)
    return log
