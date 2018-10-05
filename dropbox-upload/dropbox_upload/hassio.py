import logging
import os

import requests

import arrow

LOG = logging.getLogger(__name__)


def hassio_req(method, path):
    auth_headers = {"X-HASSIO-KEY": os.environ.get("HASSIO_TOKEN")}
    LOG.debug(f"Auth headers: {auth_headers}")
    r = method(f"http://hassio/{path}", headers=auth_headers)
    LOG.debug(r)
    r.raise_for_status()
    j = r.json()
    LOG.debug(j)
    return j["data"]


def hassio_get(path):
    return hassio_req(requests.get, path)


def hassio_post(path):
    return hassio_req(requests.post, path)


def list_snapshots():
    snapshots = hassio_get("snapshots")["snapshots"]
    # Sort them by creation date, and reverse.
    # We want to backup the most recent first
    snapshots.sort(key=lambda x: arrow.get(x["date"]))
    snapshots.reverse()
    return snapshots
