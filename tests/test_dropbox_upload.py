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


def test_main_no_snapshots(tmpdir, requests_mock, caplog):

    # Create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

    # Mock hassio
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))

    upload.main(p.strpath)

    assert (
        "docker_upload",
        logging.WARNING,
        "No snapshots found to backup",
    ) in caplog.record_tuples


def test_main_invalid_token(tmpdir, requests_mock, caplog):

    # Create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

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

    upload.main(p.strpath)

    assert (
        "docker_upload",
        logging.ERROR,
        "Invalid access token",
    ) in caplog.record_tuples
