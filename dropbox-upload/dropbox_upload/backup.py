import logging
import os
import pathlib

import arrow

from . import dropbox, util

LOG = logging.getLogger(__name__)
BACKUP_DIR = pathlib.Path("/backup/")


def local_path(snapshot):
    return BACKUP_DIR / f"{snapshot['slug']}.tar"


def dropbox_path(config, snapshot):
    dropbox_dir = pathlib.Path(config["dropbox_dir"])
    name = snapshot["slug"]
    return dropbox_dir / f"{name}.tar"


def backup(dbx, config, snapshots):

    LOG.info(f"Found {len(snapshots)} snapshots")
    LOG.info(f"Backing up to Dropbox directory: {config['dropbox_dir']}")

    if not snapshots:
        LOG.warning("No snapshots found to backup")
        return

    if config.get("keep") and len(snapshots) > config.get("keep"):
        LOG.info(f"Only backing up the first {config['keep']} snapshots")
        snapshots = snapshots[: config["keep"]]

    for i, snapshot in enumerate(snapshots, start=1):
        LOG.info(f"Snapshot: {snapshot['name']} ({i}/{len(snapshots)})")
        try:
            process_snapshot(config, dbx, snapshot)
        except Exception:
            LOG.exception(
                "Snapshot backup failed. If this happens after the addon is "
                "restarted, please open a bug."
            )


def process_snapshot(config, dbx, snapshot):
    path = local_path(snapshot)
    created = arrow.get(snapshot["date"])
    if not os.path.isfile(path):
        LOG.warning("The snapshot no longer exists")
        return
    size = util.bytes_to_human(os.path.getsize(path))
    target = str(dropbox_path(config, snapshot))
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
