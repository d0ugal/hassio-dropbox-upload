import logging
import pathlib
from unittest import mock

from dropbox_upload import backup


def test_local_path():
    expected = pathlib.Path("/backup/SLUG.tar")
    assert backup.local_path({"slug": "SLUG"}) == expected


def test_dropbox_path(cfg):
    cfg["dropbox_dir"] = "/dropbox_dir"
    expected = pathlib.Path("/dropbox_dir/SLUG.tar")
    assert backup.dropbox_path(cfg, {"slug": "SLUG"}) == expected


def test_backup_no_snapshots(cfg, caplog):
    backup.backup(None, cfg, [])

    assert (
        "dropbox_upload.backup",
        logging.WARNING,
        "No snapshots found to backup",
    ) in caplog.record_tuples


def test_snapshot_deleted(cfg, snapshot, caplog):
    backup.process_snapshot(cfg, None, snapshot)
    assert (
        "dropbox_upload.backup",
        logging.WARNING,
        "The snapshot no longer exists",
    ) in caplog.record_tuples


def test_backup_keep_limit(cfg, dropbox_fake, snapshots, caplog):
    caplog.set_level(logging.DEBUG)
    cfg["keep"] = 2
    with mock.patch("dropbox_upload.backup.local_path") as local_path:
        local_path.return_value = __file__
        backup.backup(dropbox_fake(), cfg, snapshots)
    assert (
        "dropbox_upload.backup",
        logging.INFO,
        "Only backing up the first 2 snapshots",
    ) in caplog.record_tuples


def test_backup_file_exists(cfg, dropbox_fake, snapshot, caplog):
    caplog.set_level(logging.DEBUG)
    with mock.patch("dropbox_upload.dropbox.file_exists") as file_exists:
        with mock.patch("dropbox_upload.backup.local_path") as local_path:
            local_path.return_value = __file__
            file_exists.return_value = True
            backup.backup(dropbox_fake(), cfg, [snapshot])
    assert (
        "dropbox_upload.backup",
        logging.INFO,
        "Already found in Dropbox with the same hash",
    ) in caplog.record_tuples
