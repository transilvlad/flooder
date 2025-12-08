import sys
from pathlib import Path
from types import SimpleNamespace

import flooder.threader as threader_mod

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_floodthread_run_get(monkeypatch, tmp_path):
    """Test FloodThread.run with GET requests and no files."""
    # Prepare a simple request list.
    req_list = [{"url": "http://example.local/test", "type": "GET"}]

    # Fake requests.get response.
    fake_resp = SimpleNamespace()
    fake_resp.status_code = 200
    fake_resp.elapsed = SimpleNamespace(microseconds=250000)  # 0.25s
    fake_resp.text = "OK"

    class FakeRequests:
        def get(self, url, timeout=None):
            return fake_resp

    monkeypatch.setattr(threader_mod, 'requests', FakeRequests())

    t = threader_mod.FloodThread(
        req_list, requests_per_thread=2, shuffle=False, log=False, timeout=1
    )
    # Run synchronously.
    t.run()

    assert len(t.results) == 2
    for r in t.results:
        assert r['status'] == 200
        assert r['url'] == "http://example.local/test"
        assert 'time' in r


def test_floodthread_run_post_with_files(monkeypatch, tmp_path):
    """Test FloodThread.run with POST requests including file uploads."""
    # Create a temp file to upload.
    data_file = tmp_path / "sample.txt"
    data_file.write_text("hello")

    req_list = [{
        "url": "http://example.local/upload",
        "type": "POST",
        "params": [{"name": "f", "value": "v"}],
        "files": [{"name": "file", "value": str(data_file)}]
    }]

    fake_resp = SimpleNamespace()
    fake_resp.status_code = 201
    fake_resp.elapsed = SimpleNamespace(microseconds=100000)  # 0.1s
    fake_resp.text = "CREATED"

    class FakeRequests:
        def post(self, url, data=None, files=None, timeout=None):
            # Ensure file handle is present.
            assert files and 'file' in files
            return fake_resp

    monkeypatch.setattr(threader_mod, 'requests', FakeRequests())

    t = threader_mod.FloodThread(
        req_list, requests_per_thread=2, shuffle=False, log=False, timeout=1
    )
    t.run()

    assert len(t.results) == 2
    for r in t.results:
        assert r['status'] == 201
        assert r['url'] == "http://example.local/upload"
        assert 'time' in r
