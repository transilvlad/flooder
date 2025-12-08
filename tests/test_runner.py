import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_runner_init():
    from flooder.runner import FloodRunner
    config = [{'url': 'http://localhost', 'type': 'GET'}]
    runner = FloodRunner(config_list=config, threads=1, requests_per_thread=1)
    assert runner.threads == 1
    assert runner.requests_per_thread == 1


def test_runner_run_uses_threads(monkeypatch):
    """Ensure FloodRunner.run starts worker threads (mocked) and collects results."""
    from flooder.runner import FloodRunner

    # Create a fake FloodThread class to avoid real threading and network.
    class FakeThread:
        def __init__(self, request_list, requests_per_thread, shuffle, log, timeout):
            self.results = [{'url': 'http://x', 'status': 200, 'time': 0.1}]
            self.errors = []
            self.count = 1
            self._started = False

        def start(self):
            self._started = True

        def is_alive(self):
            return False

    # Monkeypatch the FloodThread used by runner.
    monkeypatch.setattr('flooder.runner.FloodThread', FakeThread)

    config = [{'url': 'http://localhost', 'type': 'GET'}]
    runner = FloodRunner(config_list=config, threads=2, requests_per_thread=1)
    # This should finish quickly since threads are mocked.
    runner.run()

    # After run, internal totals should have been computed; at least ensure runner._total set.
    assert runner._total is not None
