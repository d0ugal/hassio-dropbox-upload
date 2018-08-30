import datetime
import glob
import hashlib
import json
import logging
import os
import pathlib
import sys

import dropbox
from dropbox import exceptions
import retrace


def setup_logging():
    log = logging.getLogger("docker_upload")
    log.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)
    return log


def load_config(path="/data/options.json"):
    with open(path) as f:
        return json.load(f)


LOG = setup_logging()
BACKUP_DIR = pathlib.Path("/backup/")
CHUNK_SIZE = 4 * 1024 * 1024
CONFIG = load_config()

DROPBOX_DIR = pathlib.Path(CONFIG["dropbox_dir"])


def bytes_to_human(nbytes):
    suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def list_snapshots():
    snapshots = list(filter(os.path.isfile, glob.glob(str(BACKUP_DIR / "*"))))
    # Sort them by creation date, and reverse. We want to backup the most recent first
    snapshots.sort(key=lambda x: os.path.getmtime(x))
    snapshots.reverse()
    return snapshots


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
    while f.tell() < file_size:
        LOG.info(f"{round((f.tell() / file_size)*100,1)}%")
        if (file_size - f.tell()) <= CHUNK_SIZE:
            dbx.files_upload_session_finish(f.read(CHUNK_SIZE), cursor, commit)
        else:
            dbx.files_upload_session_append(
                f.read(CHUNK_SIZE), cursor.session_id, cursor.offset
            )
            cursor.offset = f.tell()


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
        return

    if compute_dropbox_hash(file_path) == metadata.content_hash:
        return True

    # If the hash doesn't match, delete the file so we can re-upload it.
    LOG.warn(
        "The snapshot conflicts with a file name in dropbox, the contents "
        "are different. The dropbox file will be deleted and replaced."
    )
    dbx.files_delete(dest_path)
    return False


def main():
    LOG.info("Starting Snapshot backup")
    snapshots = list_snapshots()
    LOG.info(f"Backing up {len(snapshots)} snapshots\n")

    dbx = dropbox.Dropbox(CONFIG["access_token"])
    try:
        dbx.users_get_current_account()
    except exceptions.AuthError:
        LOG.error("Invalid access token")

    for i, snapshot in enumerate(snapshots, start=1):
        LOG.info(f"Snapshot: {snapshot} ({i}/{len(snapshots)})")
        created = os.path.getmtime(snapshot)
        created = datetime.datetime.fromtimestamp(created).isoformat()
        LOG.info(f"Created: {created}")
        size = bytes_to_human(os.path.getsize(snapshot))
        LOG.info(f"Size: {size}")
        target = str(DROPBOX_DIR / snapshot)
        LOG.info(f"Uploading to: {target}")
        try:
            if file_exists(dbx, snapshot, target):
                LOG.info("Already found the upload with the same contents")
                continue
            upload_file(dbx, snapshot, target)
            LOG.info("Done")
        except Exception:
            LOG.exception("Upload failed")

    LOG.info("Uploads complete")


if __name__ == "__main__":
    main()
