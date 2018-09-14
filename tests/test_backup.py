import datetime
import logging
import pathlib

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


def test_dropbox_path_date_filenames(cfg):
    cfg["filename_fmt"] = "{{date}} {{slug}} {{name}}"
    cfg["dropbox_dir"] = "/dropbox_dir"
    expected = pathlib.Path(
        "/dropbox_dir/2018-09-13 19.50.22 SLUG Automated backup.tar"
    )
    snapshot = {
        "slug": "SLUG",
        "name": "Automated backup",
        "date": datetime.datetime(2018, 9, 13, 19, 50, 22).isoformat(),
    }
    result = backup.dropbox_path(cfg, snapshot)
    assert result == expected
