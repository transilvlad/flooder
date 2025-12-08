import platform
import subprocess
from decimal import Decimal
from typing import NamedTuple, Any, Optional


class CpuMemInfo(NamedTuple):
    cpu_percent: float
    mem_mb: float


def _ps_get_cpumem(pid: int) -> CpuMemInfo:
    us = list(subprocess.getoutput(f"ps -p {pid} -o pcpu= -o rss=").split())
    cpu = round(Decimal(str(us[0])), 1)
    mem = round(Decimal(str(us[1])) / 1024, 1)
    return CpuMemInfo(float(cpu), float(mem))


def get_cpumem(pid: int) -> CpuMemInfo:
    """Return CPU percent and memory (MB) for a given PID.

    Tries to use psutil (recommended). Falls back to platform-specific
    implementations (ps on POSIX, ctypes/Windows APIs on Windows).
    """
    # Import psutil if available; declare psutil as Any to satisfy static typing when we set None on failure.
    psutil: Optional[Any] = None
    try:
        import psutil as _psutil  # type: ignore
        psutil = _psutil
    except Exception:
        psutil = None

    # Prefer psutil when available.
    if psutil is not None:
        try:
            p = psutil.Process(pid)
            cpu = p.cpu_percent(interval=0.1)
            mem = round(p.memory_info().rss / 1024 / 1024, 1)
            return CpuMemInfo(float(round(cpu, 1)), float(mem))
        except Exception:
            # Fall through to platform fallback.
            pass

    system = platform.system()
    if system == "Windows":
        try:
            # Minimal Windows fallback using psutil-like values via ctypes.
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            # Access windll safely since static types may not expose it.
            windll = getattr(ctypes, 'windll', None)
            if windll is not None:
                windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            else:
                raise RuntimeError("ctypes.windll not available")
            used = stat.ullTotalPhys - stat.ullAvailPhys
            mem_mb = round(used / 1024 / 1024, 1)
        except Exception:
            mem_mb = 0.0

        # CPU percent fallback: best-effort using wmi via subprocess (may require permissions).
        try:
            out = subprocess.check_output(
                ["wmic", "path", "Win32_PerfFormattedData_PerfProc_Process", "where", f"IDProcess={pid}", "get",
                 "PercentProcessorTime"], stderr=subprocess.DEVNULL, text=True)
            # Extract numbers.
            nums = [float(s) for s in out.split() if s.replace('.', '', 1).isdigit()]
            cpu = round(nums[-1], 1) if nums else 0.0
        except Exception:
            cpu = 0.0

        return CpuMemInfo(cpu, mem_mb)

    # POSIX fallback: use ps output.
    try:
        return _ps_get_cpumem(pid)
    except Exception:
        return CpuMemInfo(0.0, 0.0)
