import logging
import time

import dropbox
from dropbox import exceptions

from . import backup, config, hassio, limit

LOG = logging.getLogger("dropbox_upload.__main__")


def main(config_file, sleeper=time.sleep, DropboxAPI=dropbox.Dropbox):

    cfg = config.load_config(config_file)
    copy = cfg.copy()
    copy["access_token"] = "HIDDEN"
    LOG.debug(copy)
    config.setup_logging(cfg)

    try:
        dbx = DropboxAPI(cfg["access_token"])
        dbx.users_get_current_account()
    except exceptions.AuthError:
        LOG.error("Invalid access token")
        return

    while True:
        try:
            LOG.info("Starting Snapshot backup")
            snapshots = hassio.list_snapshots()

            stats = backup.backup(dbx, cfg, snapshots)
            stats  # make pyflakes think stats is used. It doesn't detect fstring usage.
            LOG.info("Uploads complete")
            LOG.info(f"Total size: {stats['size_human']}")

            limit.limit_snapshots(dbx, cfg, snapshots)
            LOG.info("Snapshot cleanup complete")
        except Exception:
            LOG.exception("Unhandled error")

        sleep = cfg.get("mins_between_backups", 10)
        LOG.info(f"Sleeping for {sleep} minutes")
        if sleeper(sleep * 60):
            return


if __name__ == "__main__":
    main(config.DEFAULT_CONFIG)
