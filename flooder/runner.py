import logging
import time
from typing import List, Optional

from flooder.cpumem import get_cpumem
from flooder.threader import FloodThread
from flooder.utils import format_seconds, print_report, get_logs_dir, export_report


class FloodRunner:
    def __init__(
            self, config_list: List[dict], threads: int = 10, requests_per_thread: int = 10,
            wait: int = 30, pid: int = 0, shuffle: bool = True, log: bool = True,
            export: bool = False, export_format: str = 'json'
    ) -> None:
        self.config_list = config_list
        self.threads = threads
        self.requests_per_thread = requests_per_thread
        self.wait = wait
        self.pid = pid
        self.shuffle = shuffle
        self.log = log
        self.export = export
        self.export_format = export_format
        self.thread_list: List[FloodThread] = []
        self.cpu: List[float] = []
        self.mem: List[float] = []
        self._start: Optional[float] = None
        self._stop: Optional[float] = None
        self._total: Optional[float] = None

    def run(self) -> None:
        logformat = '%(asctime)-26s %(threadName)-12s %(message)s'
        if self.log:
            logs_dir = get_logs_dir()
            logfile = logs_dir / time.strftime("flooder_%d-%m-%Y_%H-%M-%S.log")
            logging.basicConfig(filename=str(logfile), format=logformat, level=logging.DEBUG)

        self._start = time.time()
        print(f"[{format_seconds(int(time.time()))}] Flood gates opening..")
        for c in range(self.threads):
            t = FloodThread(self.config_list, self.requests_per_thread, self.shuffle, self.log, self.wait)
            t.daemon = False
            self.thread_list.append(t)
            t.start()
        print(f"[{format_seconds(int(time.time()))}] Flood gates open.")
        print(
            f"[{format_seconds(int(time.time()))}] Flooding with {self.requests_per_thread * self.threads} requests via {self.threads} threads")

        if self.pid > 0:
            time.sleep(0.2)
            usage = get_cpumem(self.pid)
            self.cpu.append(usage.cpu_percent)
            self.mem.append(usage.mem_mb)

        wait = True
        loop = 0
        while wait:
            wait = False
            time.sleep(0.1)
            loop += 1
            if loop == 300:
                total = sum(t.count for t in self.thread_list)
                if self.pid > 0:
                    usage = get_cpumem(self.pid)
                    self.cpu.append(usage.cpu_percent)
                    self.mem.append(usage.mem_mb)
                    print(
                        f"[{format_seconds(int(time.time()))}] PID {self.pid} usage: CPU: {usage.cpu_percent}%   MEM: {usage.mem_mb}M")
                print(
                    f"[{format_seconds(int(time.time()))}] Progress: {total} requests of {self.threads * self.requests_per_thread}")
                loop = 0
            for t in self.thread_list:
                if t.is_alive():
                    wait = True
        self._stop = time.time()
        # Ensure start/stop are defined before computing total (type-checker safe).
        if self._start is not None:
            self._total = self._stop - self._start
        else:
            self._total = 0.0
        report = print_report(self)

        # export report if requested
        if self.export:
            logs_dir = get_logs_dir()
            fname = f"results_{time.strftime('%Y%m%d_%H%M%S')}.{self.export_format}"
            path = logs_dir / fname
            out = export_report(report, path, fmt=self.export_format)
            if out:
                print(f"Report exported to: {out}")
