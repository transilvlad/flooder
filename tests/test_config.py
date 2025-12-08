import json
import sys
from pathlib import Path

from flooder.config import load_config

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_load_config(tmp_path):
    cfg = [
        {"url": "http://localhost/", "type": "GET"}
    ]
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))

    loaded = load_config(str(p))
    assert isinstance(loaded, list)
    assert loaded[0]['url'] == "http://localhost/"
