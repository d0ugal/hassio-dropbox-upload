import logging
import os
import pathlib

import arrow

from . import dropbox, util

LOG = logging.getLogger(__name__)
BACKUP_DIR = pathlib.Path("/backup/")


def local_path(snapshot):
    return BACKUP_DIR / f"{snapshot['slug']}.tar"


def dropbox_path(dropbox_dir, snapshot):
    return dropbox_dir / f"{snapshot['slug']}.tar"


def backup(dbx, config, snapshots):

    dropbox_dir = pathlib.Path(config["dropbox_dir"])

    LOG.info(f"Backing up {len(snapshots)} snapshots")
    LOG.info(f"Backing up to Dropbox directory: {dropbox_dir}")

    if not snapshots:
        LOG.warning("No snapshots found to backup")
        return

    if config.get("keep") and len(snapshots) > config.get("keep"):
        LOG.info(f"Only backing up the first {config['keep']} snapshots")
        snapshots = snapshots[: config["keep"]]

    for i, snapshot in enumerate(snapshots, start=1):
        LOG.info(f"Snapshot: {snapshot['name']} ({i}/{len(snapshots)})")
        process_snapshot(dropbox_dir, dbx, snapshot)


def process_snapshot(dropbox_dir, dbx, snapshot):
    path = local_path(snapshot)
    created = arrow.get(snapshot["date"])
    size = util.bytes_to_human(os.path.getsize(path))
    target = str(dropbox_path(dropbox_dir, snapshot))
    LOG.info(f"Slug: {snapshot['slug']}")
    LOG.info(f"Created: {created}")
    LOG.info(f"Size: {size}")
    LOG.info(f"Uploading to: {target}")
    try:
        if dropbox.file_exists(dbx, path, target):
            LOG.info("Already found in Dropbox with the same hash")
            return
        dropbox.upload_file(dbx, path, target)
    except Exception:
        LOG.exception("Upload failed")
