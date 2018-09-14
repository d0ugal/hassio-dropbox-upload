import logging
import os
import pathlib

import arrow
import jinja2

from . import dropbox, util

LOG = logging.getLogger(__name__)
BACKUP_DIR = pathlib.Path("/backup/")


def local_path(snapshot):
    return BACKUP_DIR / f"{snapshot['slug']}.tar"


def dropbox_path(config, snapshot):
    dropbox_dir = pathlib.Path(config["dropbox_dir"])
    if config.get("filename_fmt"):
        ctx = snapshot.copy()
        ctx["date"] = arrow.get(ctx["date"]).strftime("%Y-%m-%d %H.%M.%S")
        template = jinja2.Template(config["filename_fmt"])
        name = template.render(**ctx)
    else:
        name = snapshot["slug"]
    return dropbox_dir / f"{name}.tar"


def backup(dbx, config, snapshots):

    LOG.info(f"Backing up {len(snapshots)} snapshots")
    LOG.info(f"Backing up to Dropbox directory: {config['dropbox_dir']}")

    if not snapshots:
        LOG.warning("No snapshots found to backup")
        return

    if config.get("keep") and len(snapshots) > config.get("keep"):
        LOG.info(f"Only backing up the first {config['keep']} snapshots")
        snapshots = snapshots[: config["keep"]]

    for i, snapshot in enumerate(snapshots, start=1):
        LOG.info(f"Snapshot: {snapshot['name']} ({i}/{len(snapshots)})")
        process_snapshot(config, dbx, snapshot)


def process_snapshot(config, dbx, snapshot):
    path = local_path(snapshot)
    created = arrow.get(snapshot["date"])
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
