import json
import logging

from dropbox_upload import config, dropbox, hassio, limit, util


def test_bytes_to_human():
    assert util.bytes_to_human(1024) == "1 KB"


def test_compute_dropbox_hash(tmpdir):
    p = tmpdir.join("fake-snapshot.txt")
    p.write("fake content")
    assert dropbox.compute_dropbox_hash(p.strpath).startswith("de92bfc3d2")


def test_load_config(tmpdir):
    p = tmpdir.join("config.json")
    p.write(json.dumps({}))
    assert config.load_config(p.strpath) == {}


def test_setup_logging_normal():
    logger = config.setup_logging({})
    assert logger.level == logging.INFO


def test_setup_logging_debug():
    logger = config.setup_logging({"debug": True})
    assert logger.level == logging.DEBUG


def test_hassio_api(requests_mock):
    requests_mock.get("http://hassio/snapshots", text=json.dumps({"data": {}}))
    assert hassio.hassio_get("snapshots") == {}


def test_list_snapshots(requests_mock):
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))
    assert hassio.list_snapshots() == []


def test_limit_snapshots_no_setting(cfg, caplog):
    cfg["keep"] = None
    limit.limit_snapshots(None, cfg, [])
    assert (
        "dropbox_upload.limit",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots_zero(cfg, caplog):
    cfg["keep"] = 0
    limit.limit_snapshots(None, cfg, [])
    assert (
        "dropbox_upload.limit",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots_not_reached(cfg, caplog):
    limit.limit_snapshots(None, cfg, [])
    assert (
        "dropbox_upload.limit",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) not in caplog.record_tuples
    assert (
        "dropbox_upload.limit",
        logging.INFO,
        "Not reached the maximum number of snapshots",
    ) in caplog.record_tuples


def test_limit_snapshots(cfg, caplog, snapshots, requests_mock, dropbox_fake):
    requests_mock.post("http://hassio/snapshots/slug2/remove", text='{"data":null}')
    requests_mock.post("http://hassio/snapshots/slug3/remove", text='{"data":null}')
    cfg["keep"] = 2
    limit.limit_snapshots(dropbox_fake(), cfg, snapshots)
    assert (
        "dropbox_upload.limit",
        logging.WARNING,
        "keep not set. We wont remove old snapshots",
    ) not in caplog.record_tuples
    assert (
        "dropbox_upload.limit",
        logging.INFO,
        "Not reached the maximum number of snapshots",
    ) not in caplog.record_tuples
    assert (
        "dropbox_upload.limit",
        logging.INFO,
        "Deleting 2 snapshots",
    ) in caplog.record_tuples
