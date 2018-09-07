import json
import logging
import pathlib

import upload
from dropbox import exceptions


def test_bytes_to_human():
    assert upload.bytes_to_human(1024) == "1 KB"


def test_compute_dropbox_hash(tmpdir):
    p = tmpdir.join("fake-snapshot.txt")
    p.write("fake content")
    assert upload.compute_dropbox_hash(p.strpath).startswith("de92bfc3d2")


def test_load_config(tmpdir):
    p = tmpdir.join("config.json")
    p.write(json.dumps({}))
    assert upload.load_config(p.strpath) == {}


def test_local_path():
    expected = pathlib.Path("/backup/SLUG.tar")
    assert upload.local_path({"slug": "SLUG"}) == expected


def test_dropbox_path():
    dropbox_dir = pathlib.Path("/dropbox_dir/")
    expected = pathlib.Path("/dropbox_dir/SLUG.tar")
    assert upload.dropbox_path(dropbox_dir, {"slug": "SLUG"}) == expected


def test_setup_logging_normal():
    logger = upload.setup_logging({})
    assert logger.level == logging.INFO


def test_setup_logging_debug():
    logger = upload.setup_logging({"debug": True})
    assert logger.level == logging.DEBUG


def test_hassio_api(requests_mock):
    requests_mock.get("http://hassio/snapshots", text=json.dumps({"data": {}}))
    assert upload.hassio_get("snapshots") == {}


def test_list_snapshots(requests_mock):
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))
    assert upload.list_snapshots() == []


def test_backup_no_snapshots(tmpdir, requests_mock, caplog):

    # Create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))
    config = upload.load_config(p.strpath)

    upload.backup(config, [])

    assert (
        "docker_upload",
        logging.WARNING,
        "No snapshots found to backup",
    ) in caplog.record_tuples


def test_backup_invalid_token(tmpdir, requests_mock, caplog):

    # create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))
    config = upload.load_config(p.strpath)

    # Mock hassio
    data = {
        "data": {
            "snapshots": [
                {
                    "slug": "ce27de75",
                    "name": "Automated Backup 2018-09-05",
                    "date": "2018-09-05T01:00:00.171676+00:00",
                    "type": "full",
                    "protected": False,
                }
            ]
        }
    }
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))

    requests_mock.post(
        "https://api.dropboxapi.com/2/users/get_current_account",
        exc=exceptions.AuthError("Request ID", "Invalid token"),
    )

    assert (
        "docker_upload",
        logging.WARNING,
        "No snapshots found to backup",
    ) not in caplog.record_tuples

    snapshots = upload.list_snapshots()
    upload.backup(config, snapshots)

    assert (
        "docker_upload",
        logging.ERROR,
        "Invalid access token",
    ) in caplog.record_tuples


def test_main(tmpdir, requests_mock, caplog):

    # create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

    # Mock hass API
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))

    upload.main(p.strpath, lambda x: True)

    assert (
        "docker_upload",
        logging.INFO,
        "Starting Snapshot backup",
    ) in caplog.record_tuples

    assert ("docker_upload", logging.INFO, "Uploads complete") in caplog.record_tuples
