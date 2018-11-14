import datetime
import json

import pytest

from dropbox_upload import hassio


@pytest.fixture
def cfg():
    return {
        "dropbox_dir": "snapshots",
        "access_token": "token",
        "debug": True,
        "keep": 100,
        "filename": "snapshot_slug",
    }


@pytest.fixture
def snapshot():
    return {
        "slug": "dbaa2add",
        "name": "Automated Backup 2018-09-14",
        "date": "2018-09-14T01:00:00.873481+00:00",
        "type": "full",
        "protected": True,
    }


@pytest.fixture
def snapshot_unprotected(snapshot):
    snapshot["protected"] = False
    return snapshot


@pytest.fixture
def snapshots(requests_mock):

    now = datetime.datetime.now()
    days_ago = lambda days: (now - datetime.timedelta(days=days)).isoformat()

    snapshots = [
        # Intentionally out of order.
        {"date": days_ago(3), "slug": "slug3", "name": "name3", "protected": True},
        {"date": days_ago(1), "slug": "slug1", "name": "name1", "protected": True},
        {"date": days_ago(2), "slug": "slug2", "name": "name2", "protected": False},
        {"date": days_ago(0), "slug": "slug0", "name": "name0", "protected": True},
    ]
    data = {"data": {"snapshots": snapshots}}
    requests_mock.get("http://hassio/snapshots", text=json.dumps(data))
    return hassio.list_snapshots()


@pytest.fixture
def dropbox_fake():
    class DropboxAPI:
        def __init__(self, *args, **kwargs):
            pass

        def users_get_current_account(self):
            pass

        def files_delete(self, path):
            pass

        def files_upload(self, f, path):
            pass

    return DropboxAPI
