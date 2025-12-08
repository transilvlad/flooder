# Flooder

Flooder is a flexible, multi-threaded HTTP request tool for stress testing APIs and web servers.
It supports GET, POST, PUT, DELETE, and optionally more HTTP methods, parallel requests, configurable timeouts, and system resource monitoring.

## Features

- Multi-threaded HTTP flooding
- Configurable requests, payloads, file uploads
- Supports GET, POST, PUT, DELETE (and more)
- Shuffling, logging, and monitoring
- Resource usage reporting for PIDs (CPU, memory)
- User-Agent rotation
- Rich metrics reporting
- CLI integration
- Example configs
- Well-tested with pytest
- CI/Release workflows for reliability

## Installation

Open a command prompt and run:

    git clone https://github.com/transilvlad/flooder.git
    cd flooder
    pip install .

Note: `psutil` is recommended on Windows for accurate per-PID CPU/memory monitoring. It is available as an optional extra; to install with monitoring support run:

    pip install .[monitoring]

(If you already ran `pip install .` without extras, install `psutil` separately: `pip install psutil`.)

## Usage

Run Flooder with a JSON configuration file describing the requests to make. The JSON file is a list of request descriptors (see "Example Configuration" below).

Basic command (Windows cmd.exe example):

    python -m flooder --json examples\config_example.json --threads 5 --requests 20 --wait 30

Or using the top-level script shim:

    python flooder.py --json examples\config_example.json --threads 5 --requests 20 --wait 30

What the command does:
- Loads the JSON configuration file specified by `--json`.
- Starts the specified number of worker threads (see `--threads`).
- Each thread will sequentially perform the configured requests `--requests` times (requests per thread).
- Each HTTP request will time out after `--wait` seconds if no response is received.
- If `--pid` is provided, Flooder will sample that process's CPU and memory usage while running (psutil is preferred on Windows).
- Logging is written to the `logs/` directory inside the package; a timestamped logfile is created per run.

All CLI options

- `-j, --json <path>` (required): Path to the JSON file containing the requests list.
- `-t, --threads <int>` (default: 10): Number of worker threads to run in parallel.
- `-r, --requests <int>` (default: 10): Number of request iterations per thread.
- `-w, --wait <int>` (default: 30): Per-request timeout in seconds.
- `-p, --pid <int>` (default: 0): Optional PID to monitor (CPU/MEM usage). Set to `0` to disable monitoring.
- `-ns, --no-shuffle`: Disable shuffling of the requests list. By default the requests list is shuffled per thread to better simulate varied traffic.
- `-nl, --no-log`: Disable writing to the logfile. Output will still be printed to stdout.
- `-e, --export`: Export the run report to the package `logs/` directory as a `results_<timestamp>.<ext>` file (enabled by default). Use `--no-export` to disable.
- `--export-format` (choices: `json`, `csv`, `txt`, default: `txt`): When used with `--export`, controls the output format of the results file.
- `-v, --version`: Print application version.
- `-h, --help`: Show help and exit.

Note: Running `python flooder.py` or `python -m flooder` with no command-line parameters will print the help/usage information and exit (no error), so it's safe to call without flags.

Example invocation and behavior

1) Small run to sanity-check config (single thread, single request):

    python -m flooder --json examples\config_example.json --threads 1 --requests 1

Expected terminal output:

```commandline
[14:21:17] Flood gates opening..
[14:21:17] Flood gates open.
[14:21:17] Flooding with 100 requests via 5 threads
[14:21:47] Progress: 98 requests of 100
-----------------------------------------
Threads:                                5
Requests per thread:                   20
-----------------------------------------
Execution time:                  00:00:32
-----------------------------------------
```

A logfile will be created in `logs/` (for example `logs\\flooder_08-12-2025_12-34-56.log`) containing detailed debug information per request when logging is enabled.

If you pass `--export` (enabled by default), the run's structured metrics are also written to a separate file inside `logs/` named `results_<YYYYMMDD_HHMMSS>.<ext>` where `<ext>` is the requested export format (json/csv/txt). By default the exporter writes a human-readable `txt` file.

Example (explicit export to JSON):

    python -m flooder --json examples\config_example.json --threads 5 --requests 100 --export --export-format json

After a successful run and export, Flooder prints:

```text
Report exported to: logs/results_20251208_142230.json
```

If you do not use `--export`, the report is printed to stdout in human-readable text only.

2) Larger run with PID monitoring (Windows example):

    python -m flooder --json examples\\config_example.json --threads 5 --requests 100 --pid 12345

While running, periodically Flooder prints progress and (if `--pid` is set) sampled CPU/MEM for the target PID. Final report includes:

- Threads/Requests summary
- Counts for successful, error and failed requests
- Fastest/slowest/average timings per category
- CPU/MEM high/low/average (if PID monitoring enabled)

Example final summary output:

```commandline
-----------------------------------------
Threads:                                5
Requests:                             100
-----------------------------------------
Requests total:                       500
Requests successful:                  480
Requests error:                        15
Requests failed:                        5
-----------------------------------------
Successful fastest:              0.002345
Successful slowest:              1.234567
Successful average:              0.123456
-----------------------------------------
CPU:                  45.3%  23.5%   5.0%
MEM:                 512.0M 480.0M 460.0M
-----------------------------------------
Execution time:                  00:03:42
Time total:                      00:12:34
```

### Logging

- A `logs/` directory is created inside the package root when a run uses logging. The file name contains a timestamp.
- Logs include a debug entry for each request (URL, payload, response status, elapsed time, and response content when available).
- To disable logs, use `--no-log`.

### Configuration file format

The `--json` file must be a JSON array of request objects. Each object supports the following keys:

- `url` (string, required): The full URL to call (including scheme, host, and path).
- `type` (string, required): One of `GET`, `POST`, `PUT`, `DELETE` (case-insensitive). Additional HTTP verbs are handled by the implementation where applicable.
- `params` (array of {name, value}, optional): Form fields to submit with the request.
- `files` (array of {name, value}, optional): File upload fields where `value` is a path to the file on disk.

Example (from `examples/config_example.json`):

```json
[
  {
    "url": "https://httpbin.org/post",
    "type": "POST",
    "params": [
      {"name": "foo", "value": "bar"}
    ],
    "files": [
      {"name": "datafile", "value": "examples/sample_data.txt"}
    ]
  }
]
```

### Troubleshooting

- If PID monitoring on Windows reports zeros or fails, ensure `psutil` is installed (`pip install psutil`) or run the process as an account with permissions to query the target PID.
- If file uploads fail, confirm paths in the `files` array are correct and that the running user has read permission for the files.
- For heavy load tests, ensure the target service and your client machine can handle the requested concurrency; use small `--threads` and `--requests` to iterate quickly.

### Development

- See `tests/` for test cases. The project includes unit tests for utilities and CPU/memory helpers.
- Run tests via `pytest`.

### Contributions

Contributions of any kind (bug fixes, new features...) are welcome!
This is a development tool and as such it may not be perfect and may be lacking in some areas.

Certain future functionalities are marked with TODO comments throughout the code.
This however does not mean they will be given priority or ever be done.

Any merge request made should align to existing coding style and naming convention.
Before submitting a merge request please run a comprehensive code quality analysis (IntelliJ, SonarQube).

CI runs automated tests on PRs and releases on tags.

Read more [here](contributing.md).

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).
See the repository `LICENSE` file for the full license text (SPDX: `GPL-2.0`).

In short: you may use, modify, and redistribute this software under the terms of GPL-2.0;
redistributed derivative works must also be licensed under GPL-2.0.
The software is provided without any warranty to the extent permitted by law.
