import hashlib
import json
import logging
import os
import pathlib
import sys

import arrow
import dropbox
import requests
import retrace
from dropbox import exceptions

LOG = logging.getLogger("docker_upload")
BACKUP_DIR = pathlib.Path("/backup/")
CHUNK_SIZE = 4 * 1024 * 1024
AUTH_HEADERS = {"X-HASSIO-KEY": os.environ["HASSIO_TOKEN"]}


def load_config(path="/data/options.json"):
    with open(path) as f:
        return json.load(f)


def setup_logging(config):
    log = logging.getLogger("docker_upload")
    log.setLevel(logging.DEBUG if config.get("debug") else logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log


def bytes_to_human(nbytes):
    suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def hassio_get(path):
    r = requests.get(f"http://hassio/{path}", headers=AUTH_HEADERS).json()
    LOG.debug(r)
    return r["data"]


def list_snapshots():
    snapshots = hassio_get("snapshots")["snapshots"]
    # Sort them by creation date, and reverse. We want to backup the most recent first
    snapshots.sort(key=lambda x: arrow.get(x["date"]))
    snapshots.reverse()
    return snapshots


def local_path(snapshot):
    return BACKUP_DIR / f"{snapshot['slug']}.tar"


def dropbox_path(dropbox_dir, snapshot):
    return dropbox_dir / f"{snapshot['slug']}.tar"


@retrace.retry(limit=4)
def upload_file(dbx, file_path, dest_path):

    f = open(file_path, "rb")
    file_size = os.path.getsize(file_path)
    if file_size <= CHUNK_SIZE:
        return dbx.files_upload(f, dest_path)

    upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
    cursor = dropbox.files.UploadSessionCursor(
        session_id=upload_session_start_result.session_id, offset=f.tell()
    )
    commit = dropbox.files.CommitInfo(path=dest_path)
    prev = None
    while f.tell() < file_size:
        percentage = round((f.tell() / file_size) * 100)

        if not prev or percentage > prev + 5:
            LOG.info(f"{percentage:3} %")
            prev = percentage

        if (file_size - f.tell()) <= CHUNK_SIZE:
            dbx.files_upload_session_finish(f.read(CHUNK_SIZE), cursor, commit)
        else:
            dbx.files_upload_session_append(
                f.read(CHUNK_SIZE), cursor.session_id, cursor.offset
            )
            cursor.offset = f.tell()
    LOG.info("100 %")


def compute_dropbox_hash(filename):

    with open(filename, "rb") as f:
        block_hashes = b""
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            block_hashes += hashlib.sha256(chunk).digest()
        return hashlib.sha256(block_hashes).hexdigest()


def file_exists(dbx, file_path, dest_path):
    try:
        metadata = dbx.files_get_metadata(dest_path)
    except Exception:
        LOG.info("No existing snapshot in dropox with this name")
        return False

    dropbox_hash = metadata.content_hash
    local_hash = compute_dropbox_hash(file_path)
    if local_hash == dropbox_hash:
        return True

    # If the hash doesn't match, delete the file so we can re-upload it.
    # We might want to make this optional? a safer mode might be to
    # add a suffix?
    LOG.warn(
        "The snapshot conflicts with a file name in dropbox, the contents "
        "are different. The dropbox file will be deleted and replaced. "
        "Local hash: %s, Dropbox hash: %s",
        local_hash,
        dropbox_hash,
    )
    dbx.files_delete(dest_path)
    return False


def main():

    config = load_config()
    dropbox_dir = pathlib.Path(config["dropbox_dir"])

    LOG.info("Starting Snapshot backup")
    snapshots = list_snapshots()
    LOG.info(f"Backing up {len(snapshots)} snapshots")
    LOG.info(f"Backing up to Dropbox directory: {dropbox_dir}")

    dbx = dropbox.Dropbox(config["access_token"])
    try:
        dbx.users_get_current_account()
    except exceptions.AuthError:
        LOG.error("Invalid access token")

    for i, snapshot in enumerate(snapshots, start=1):
        path = local_path(snapshot)
        created = arrow.get(snapshot["date"])
        size = bytes_to_human(os.path.getsize(path))
        target = str(dropbox_path(dropbox_dir, snapshot))
        LOG.info(f"Snapshot: {snapshot['name']} ({i}/{len(snapshots)})")
        LOG.info(f"Slug: {snapshot['slug']}")
        LOG.info(f"Created: {created}")
        LOG.info(f"Size: {size}")
        LOG.info(f"Uploading to: {target}")
        try:
            if file_exists(dbx, path, target):
                LOG.info("Already found in Dropbox with the same hash")
                continue
            upload_file(dbx, path, target)
        except Exception:
            LOG.exception("Upload failed")

    LOG.info("Uploads complete")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        LOG.exception("Unhandled error")
