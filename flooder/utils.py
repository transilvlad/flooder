import csv
import json
import time
from pathlib import Path
from typing import Any, Tuple, List, Dict, Optional


def format_seconds(val: float) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(float(str(val))))


def get_logs_dir() -> Path:
    """Return the project's logs directory, ensuring it exists.

    The logs directory is created relative to the package root so it is
    independent of the current working directory.
    """
    pkg_root = Path(__file__).resolve().parents[1]
    logs_dir = pkg_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _safe_mean(values: List[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def print_report(runner: Any) -> Dict[str, Any]:
    """Aggregate and print a human-friendly report from a FloodRunner instance.

    Returns a structured dictionary with the aggregated metrics which can be
    exported to JSON or CSV by `export_report`.
    """
    sep = "-" * 35

    # Aggregate results from threads
    requests_total = 0
    successful_times: List[float] = []
    error_times: List[float] = []
    failed_times: List[float] = []

    errors: List[str] = []

    for t in getattr(runner, 'thread_list', []):
        requests_total += len(getattr(t, 'results', []))
        for r in getattr(t, 'results', []):
            status = r.get('status', 0)
            elapsed = float(r.get('time') or 0.0)
            if status == 200:
                successful_times.append(elapsed)
            elif status == 0:
                failed_times.append(elapsed)
            else:
                error_times.append(elapsed)
        for e in getattr(t, 'errors', []):
            if e not in errors:
                errors.append(e)

    # Counts
    requests_successful = len(successful_times)
    requests_error = len(error_times)
    requests_failed = len(failed_times)

    # Timing stats helper
    def _stats(times: List[float]) -> Tuple[float, float, float]:
        if not times:
            return 0.0, 0.0, 0.0
        fastest = round(min(times), 6)
        slowest = round(max(times), 6)
        average = round(sum(times) / len(times), 6)
        return fastest, slowest, average

    s_fast, s_slow, s_avg = _stats(successful_times)
    e_fast, e_slow, e_avg = _stats(error_times)
    f_fast, f_slow, f_avg = _stats(failed_times)

    # Throughput
    total_time = getattr(runner, '_total', None) or 0.0
    throughput = round((requests_total / total_time), 2) if total_time and requests_total else 0.0

    # CPU / MEM summary
    cpu_vals = getattr(runner, 'cpu', []) or []
    mem_vals = getattr(runner, 'mem', []) or []
    cpu_min = round(min(cpu_vals), 1) if cpu_vals else 0.0
    cpu_max = round(max(cpu_vals), 1) if cpu_vals else 0.0
    cpu_avg = round(sum(cpu_vals) / len(cpu_vals), 1) if cpu_vals else 0.0
    mem_min = round(min(mem_vals), 1) if mem_vals else 0.0
    mem_max = round(max(mem_vals), 1) if mem_vals else 0.0
    mem_avg = round(sum(mem_vals) / len(mem_vals), 1) if mem_vals else 0.0

    # Build report dict
    report = {
        "threads": getattr(runner, 'threads', 0),
        "requests_per_thread": getattr(runner, 'requests_per_thread', getattr(runner, 'requests', 0)),
        "requests_total": requests_total,
        "successful": requests_successful,
        "errors": requests_error,
        "failed": requests_failed,
        "successful_times": successful_times,
        "error_times": error_times,
        "failed_times": failed_times,
        "timings": {
            "successful": {"fastest": s_fast, "slowest": s_slow, "average": s_avg},
            "errors": {"fastest": e_fast, "slowest": e_slow, "average": e_avg},
            "failed": {"fastest": f_fast, "slowest": f_slow, "average": f_avg},
        },
        "throughput": throughput,
        "execution_time_seconds": total_time,
        "cpu": {"min": cpu_min, "avg": cpu_avg, "max": cpu_max},
        "mem": {"min": mem_min, "avg": mem_avg, "max": mem_max},
        "errors_list": errors,
    }

    # Extract typed locals to satisfy static type checks and avoid indexing Any-typed dicts.
    # Prefer pulling typed values straight from the runner to avoid mypy issues
    threads_typed: int = int(getattr(runner, 'threads', 0))
    rpt_per_thread: int = int(getattr(runner, 'requests_per_thread', getattr(runner, 'requests', 0)))
    rpt_total: int = requests_total
    rpt_successful: int = int(len(successful_times))
    rpt_errors: int = int(len(error_times))
    rpt_failed: int = int(len(failed_times))
    exec_time: float = total_time

    # Print the human readable report to stdout (keeps previous output)
    print(sep)
    print(f"Threads:             {threads_typed:>6}")
    print(f"Requests per thread: {rpt_per_thread:>6}")
    print(f"Requests total:      {rpt_total:>6}")
    print(sep)
    print(f"Successful: {rpt_successful:>6}  | fastest: {s_fast:>8}  slowest: {s_slow:>8}  avg: {s_avg:>8}")
    if rpt_errors > 0:
        print(f"Errors:     {rpt_errors:>6}  | fastest: {e_fast:>8}  slowest: {e_slow:>8}  avg: {e_avg:>8}")
    if rpt_failed > 0:
        print(f"Failed:     {rpt_failed:>6}  | fastest: {f_fast:>8}  slowest: {f_slow:>8}  avg: {f_avg:>8}")

    print(sep)
    print(f"Throughput (req/s): {report['throughput']}")
    print(f"Execution time:     {format_seconds(exec_time)}")

    if cpu_vals:
        print(sep)
        print(f"CPU (max/avg/min): {cpu_max}%  {cpu_avg}%  {cpu_min}%")
    if mem_vals:
        print(f"MEM (max/avg/min): {mem_max}M  {mem_avg}M  {mem_min}M")

    if errors:
        print(sep)
        print("Errors encountered:")
        for e in errors:
            print(f" - {e}")

    return report


def export_report(report: Dict[str, Any], path: Path, fmt: str = 'json') -> Optional[Path]:
    """Export the report to the given path in the requested format (json|csv|txt).

    Returns the path to the written file or None on failure.
    """
    try:
        if fmt == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return path
        elif fmt == 'csv':
            # Flatten a few key metrics to CSV (rows: metric, value)
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['metric', 'value'])
                writer.writerow(['threads', report['threads']])
                writer.writerow(['requests_per_thread', report['requests_per_thread']])
                writer.writerow(['requests_total', report['requests_total']])
                writer.writerow(['successful', report['successful']])
                writer.writerow(['errors', report['errors']])
                writer.writerow(['failed', report['failed']])
                writer.writerow(['throughput', report['throughput']])
                writer.writerow(['execution_time_seconds', report['execution_time_seconds']])
            return path
        else:  # txt
            with open(path, 'w', encoding='utf-8') as f:
                f.write('Report:\n')
                for k, v in report.items():
                    f.write(f"{k}: {v}\n")
            return path
    except Exception:
        return None
