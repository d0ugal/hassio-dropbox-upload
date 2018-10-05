import hashlib
import logging
import os

import dropbox
import retrace

LOG = logging.getLogger(__name__)
CHUNK_SIZE = 4 * 1024 * 1024


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
    LOG.debug(f"Dropbox hash: {dropbox_hash}")
    LOG.debug(f"Local hash: {local_hash}")
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
