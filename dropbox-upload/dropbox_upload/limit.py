import logging

import arrow

from . import backup, hassio

LOG = logging.getLogger(__name__)


def limit_snapshots(dbx, config, snapshots):

    keep = config.get("keep")

    if not keep:
        LOG.warning("keep not set. We wont remove old snapshots")
        return

    if len(snapshots) <= keep:
        LOG.info("Not reached the maximum number of snapshots")
        return

    LOG.info(f"Limiting snapshots to the {keep} most recent")

    snapshots.sort(key=lambda x: arrow.get(x["date"]))
    snapshots.reverse()

    expired_snapshots = snapshots[keep:]

    LOG.info(f"Deleting {len(expired_snapshots)} snapshots")

    for snapshot in expired_snapshots:
        LOG.info(f"Deleting {snapshot['name']} (slug: {snapshot['slug']}")
        hassio.hassio_delete(f"backups/{snapshot['slug']}")
        path = str(backup.dropbox_path(config, snapshot))
        dbx.files_delete(path)
