import logging
import time

import dropbox
import retrace

from . import backup, config, hassio, limit

LOG = logging.getLogger("dropbox_upload.__main__")


def init_sentry(cfg):
    LOG.info("Sentry configured")
    import sentry_sdk

    sentry_sdk.init(cfg["sentry_dsn"])


def main(config_file, sleeper=time.sleep, DropboxAPI=dropbox.Dropbox):

    cfg = config.load_config(config_file)

    config.setup_logging(cfg)

    if "sentry_dsn" in cfg:
        init_sentry(cfg)

    copy = cfg.copy()
    copy["access_token"] = "HIDDEN"
    copy["sentry_dsn"] = "HIDDEN"
    LOG.debug(copy)

    config.validate(cfg)

    dbx = DropboxAPI(cfg["access_token"])
    dbx.users_get_current_account()

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
        except (retrace.RetraceException, Exception):
            LOG.exception("Unhandled error")

        sleep = cfg.get("mins_between_backups", 10)
        LOG.info(f"Sleeping for {sleep} minutes")
        if sleeper(sleep * 60):
            return


if __name__ == "__main__":
    main(config.DEFAULT_CONFIG)
