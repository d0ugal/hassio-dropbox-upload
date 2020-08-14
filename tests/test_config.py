import json

import pytest
from dropbox_upload import config, exceptions


def test_config_dropbox_dir(tmpdir):

    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": "/"}))

    cfg = config.load_config(p.strpath)
    assert cfg["dropbox_dir"] == "/"


def test_config_dropbox_dir_invalid(tmpdir):

    p = tmpdir.join("config.json")
    p.write(json.dumps({"dropbox_dir": ""}))

    cfg = config.load_config(p.strpath)

    with pytest.raises(exceptions.InvalidConfig):
        config.validate(cfg)
