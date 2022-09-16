import logging
import os

import arrow
import requests

LOG = logging.getLogger(__name__)

def hassio_token():
    return os.environ.get("SUPERVISOR_TOKEN")

def hassio_req(method, path):
    auth_headers = {'Authorization': f'Bearer {hassio_token()}'}
    LOG.debug(f"Auth headers: {auth_headers}")
    r = method(f"http://supervisor/{path}", headers=auth_headers)
    LOG.debug(r)
    r.raise_for_status()
    j = r.json()
    LOG.debug(j)
    return j["data"]


def hassio_get(path):
    return hassio_req(requests.get, path)


def hassio_post(path):
    return hassio_req(requests.post, path)

def hassio_delete(path):
    return hassio_req(requests.delete, path)

def list_snapshots():
    snapshots = hassio_get("backups")["backups"]
    # Sort them by creation date, and reverse.
    # We want to backup the most recent first
    snapshots.sort(key=lambda x: arrow.get(x["date"]))
    snapshots.reverse()
    return snapshots
