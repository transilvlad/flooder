import argparse
import json
import sys
from typing import Any, List


def parse_args():
    # Disable the automatic -h/--help to provide a custom help message string.
    parser = argparse.ArgumentParser(
        prog="Flooder",
        description="Python HTTP flooding tool — multi-threaded requests with optional PID monitoring and report export.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,
    )

    parser.add_argument('-j', '--json', type=str, required=True,
                        help='Path to requests config JSON (required). JSON must be an array of request objects.')
    parser.add_argument('-t', '--threads', default=10, type=int,
                        help='Number of concurrent worker threads to start.')
    parser.add_argument('-w', '--wait', default=30, type=int,
                        help='Per-request timeout in seconds.')
    parser.add_argument('-r', '--requests', default=10, type=int,
                        help='Number of request iterations each thread should perform.')
    parser.add_argument('-p', '--pid', default=0, type=int,
                        help='Optional PID to sample CPU/MEM usage for during the run (0 = disabled).')
    parser.add_argument('-ns', '--no-shuffle', default=False, action='store_true',
                        help='Disable per-thread shuffling of the request list (enabled by default).')
    parser.add_argument('-nl', '--no-log', default=False, action='store_true',
                        help='Disable writing to the logfile in the package `logs/` folder (stdout still used).')

    # Mutually exclusive group to allow disabling export explicitly while export remains the default.
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--export', dest='export', action='store_true',
                       help='Export run report to the package `logs/` directory (enabled by default).')
    group.add_argument('--no-export', dest='export', action='store_false',
                       help='Disable exporting the run report to the logs folder.')
    parser.set_defaults(export=True)

    parser.add_argument('--export-format', default='txt', choices=['json', 'csv', 'txt'],
                        help='Export format for the run report (txt = human-readable text).')

    # Provide a custom help flag text instead of the default message.
    parser.add_argument('-h', '--help', action='help', help='Show help message.')

    # Show help and exit (cleanly) when no arguments are provided.
    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit(0)

    return parser.parse_args()


def load_config(json_path: str) -> List[Any]:
    with open(json_path, 'r') as f:
        data = json.load(f)
    assert isinstance(data, list), "Config must be a list of requests"
    return data
