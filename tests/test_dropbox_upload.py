import upload

def test_bytes_to_human():

    assert upload.bytes_to_human(1024) == "1 KB"
