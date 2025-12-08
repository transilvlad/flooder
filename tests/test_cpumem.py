import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_get_cpumem_with_psutil(monkeypatch):
    """When psutil is available, get_cpumem should use it and return CpuMemInfo with expected values."""
    # Create fake psutil.Process that returns deterministic values.
    fake_process = SimpleNamespace()
    fake_process.cpu_percent = lambda interval=None: 12.3
    fake_process.memory_info = lambda: SimpleNamespace(rss=1500 * 1024 * 1024)

    class FakePsutil:
        def Process(self, pid):
            return fake_process

    monkeypatch.setitem(sys.modules, 'psutil', FakePsutil())

    mod = importlib.import_module('flooder.cpumem')
    importlib.reload(mod)
    info = mod.get_cpumem(1)

    assert hasattr(info, 'cpu_percent')
    assert hasattr(info, 'mem_mb')
    assert isinstance(info.cpu_percent, float)
    assert isinstance(info.mem_mb, float)
    # Expect the mocked values.
    assert abs(info.cpu_percent - 12.3) < 1e-6
    assert abs(info.mem_mb - 1500.0) < 1e-6


def test_get_cpumem_posix_fallback(monkeypatch):
    """When psutil is not available, POSIX fallback should parse `ps` output and return values."""
    # Simulate ImportError for psutil by ensuring it's not in sys.modules and monkeypatching import.
    monkeypatch.delitem(sys.modules, 'psutil', raising=False)

    # Force platform to Linux.
    monkeypatch.setattr('platform.system', lambda: 'Linux')

    # Provide a predictable ps output: cpu 5.0, rss 204800 (KB).
    monkeypatch.setattr('subprocess.getoutput', lambda cmd: "  5.0  204800 ")

    mod = importlib.import_module('flooder.cpumem')
    importlib.reload(mod)
    info = mod.get_cpumem(1234)

    assert isinstance(info.cpu_percent, float)
    assert isinstance(info.mem_mb, float)
    assert abs(info.cpu_percent - 5.0) < 1e-6
    # 204800 KB -> 200.0 MB
    assert abs(info.mem_mb - 200.0) < 1e-6


def test_get_cpumem_posix_fallback_malformed(monkeypatch):
    """If ps output is malformed the fallback should return safe zeroed CpuMemInfo values."""
    monkeypatch.delitem(sys.modules, 'psutil', raising=False)
    monkeypatch.setattr('platform.system', lambda: 'Linux')
    # Malformed output that will cause parsing to fail.
    monkeypatch.setattr('subprocess.getoutput', lambda cmd: "not-a-number")

    mod = importlib.import_module('flooder.cpumem')
    importlib.reload(mod)
    info = mod.get_cpumem(9999)

    assert isinstance(info.cpu_percent, float)
    assert isinstance(info.mem_mb, float)
    # On failure the fallback returns zeros.
    assert info.cpu_percent == 0.0
    assert info.mem_mb == 0.0
