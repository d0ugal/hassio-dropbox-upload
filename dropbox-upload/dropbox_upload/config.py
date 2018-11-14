import json
import logging
import sys

from dropbox_upload import exceptions

DEFAULT_CONFIG = "/data/options.json"
LOG = logging.getLogger(__name__)


def load_config(path=DEFAULT_CONFIG):
    with open(path) as f:
        return json.load(f)


def validate(cfg):
    global errored
    errored = False

    def _e(message):
        global errored
        LOG.error(message)
        errored = True

    if not cfg["dropbox_dir"]:
        _e("The dropbox_dir can't be an empty string, it must be at least '/'")

    if "filename" not in cfg:
        cfg["filename"] = "snapshot_slug"

    if not cfg["filename"] in ["snapshot_name", "snapshot_slug"]:
        _e(
            "The `filename` config setting must equal either 'snapshot_name' "
            "or 'snapshot_slug'. This is what it will use for the filename in "
            "dropbox."
        )

    if errored:
        raise exceptions.InvalidConfig()


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
