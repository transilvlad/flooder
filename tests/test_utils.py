import sys
from pathlib import Path

from flooder.utils import format_seconds

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_format_seconds():
    assert format_seconds(0) == "00:00:00"
    assert isinstance(format_seconds(123.4), str)


def test_get_logs_dir(tmp_path):
    # Monkeypatch the package root to tmp_path.
    import importlib
    import inspect
    import flooder.utils as utils_mod
    pkg_root = tmp_path / "flooder"
    pkg_root.mkdir()
    (pkg_root / "__init__.py").write_text("")
    # Create a fake utils.py in tmp package copy.
    (pkg_root / "utils.py").write_text(inspect.getsource(utils_mod))
    import sys
    sys.path.insert(0, str(tmp_path))
    try:
        mod = importlib.import_module("flooder.utils")
        logs = mod.get_logs_dir()
        assert logs.exists()
        assert logs.is_dir()
    finally:
        sys.path.pop(0)
