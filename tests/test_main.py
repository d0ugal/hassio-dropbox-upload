import json
import logging

from dropbox_upload import __main__


def test_main(tmpdir, requests_mock, caplog, dropbox_fake):

    # create config file
    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "snapshots", "access_token": "token"}))

    # Mock hass API
    data = {"data": {"snapshots": []}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))

    __main__.main(p.strpath, sleeper=lambda x: True, DropboxAPI=dropbox_fake)

    assert (
        "dropbox_upload.__main__",
        logging.INFO,
        "Starting Snapshot backup",
    ) in caplog.record_tuples

    assert (
        "dropbox_upload.__main__",
        logging.INFO,
        "Uploads complete",
    ) in caplog.record_tuples
