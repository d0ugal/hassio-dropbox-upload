import datetime
import json
import logging
import pathlib

import pytest

import upload
from dropbox import exceptions


@pytest.fixture
def config():
    return {
        "dropbox_dir": "snapshots",
        "access_token": "token",
        "debug": True,
        "keep": 100,
    }


@pytest.fixture
def snapshots(requests_mock):

    now = datetime.datetime.now()
    days_ago = lambda days: (now - datetime.timedelta(days=days)).isoformat()

    snapshots = [
        # Intentionally out of order.
        {"date": days_ago(3), "slug": "slug3", "name": "name3"},
        {"date": days_ago(1), "slug": "slug1", "name": "name1"},
        {"date": days_ago(2), "slug": "slug2", "name": "name2"},
        {"date": days_ago(0), "slug": "slug0", "name": "name0"},
    ]
    data = {"data": {"snapshots": snapshots}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))
    return upload.list_snapshots()


@pytest.fixture
def dropbox_fake():
    class DropboxAPI:
        def __init__(self, *args, **kwargs):
            pass

        def users_get_current_account(self):
            pass

        def files_delete(self, path):
            pass

    return DropboxAPI


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

    upload.backup(None, config, [])

    assert (
        "docker_upload",
        logging.WARNING,
        "No snapshots found to backup",
    ) in caplog.record_tuples


def test_main_invalid_token(tmpdir, requests_mock, caplog):

    # create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

    requests_mock.post(
        "https://api.dropboxapi.com/2/users/get_current_account",
        exc=exceptions.AuthError("Request ID", "Invalid token"),
    )

    upload.main(p.strpath)

    assert (
        "docker_upload",
        logging.ERROR,
        "Invalid access token",
    ) in caplog.record_tuples


def test_main(tmpdir, requests_mock, caplog, dropbox_fake):

    # create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

    # Mock hass API
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))

    upload.main(p.strpath, sleeper=lambda x: True, DropboxAPI=dropbox_fake)

    assert (
        "docker_upload",
        logging.INFO,
        "Starting Snapshot backup",
    ) in caplog.record_tuples

    assert ("docker_upload", logging.INFO, "Uploads complete") in caplog.record_tuples


def test_limit_snapshots_no_setting(config, caplog):
    config["keep"] = None
    upload.limit_snapshots(None, config, [])
    assert (
        "docker_upload",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots_zero(config, caplog):
    config["keep"] = 0
    upload.limit_snapshots(None, config, [])
    assert (
        "docker_upload",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots_not_reached(config, caplog):
    upload.limit_snapshots(None, config, [])
    assert (
        "docker_upload",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) not in caplog.record_tuples
    assert (
        "docker_upload",
        logging.INFO,
        "Not reached the maximum number of snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots(config, caplog, snapshots, requests_mock, dropbox_fake):
    requests_mock.post("http://hassio/snapshots/slug2/remove", text='{"data":null}')
    requests_mock.post("http://hassio/snapshots/slug3/remove", text='{"data":null}')
    config["keep"] = 2
    upload.limit_snapshots(dropbox_fake(), config, snapshots)
    assert (
        "docker_upload",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) not in caplog.record_tuples
    assert (
        "docker_upload",
        logging.INFO,
        "Not reached the maximum number of snapshots",
    ) not in caplog.record_tuples
    assert (
        "docker_upload",
        logging.INFO,
        "Deleting 2 snapshots",
    ) in caplog.record_tuples
