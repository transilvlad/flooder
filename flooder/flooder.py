from flooder.config import parse_args, load_config
from flooder.runner import FloodRunner


def main():
    args = parse_args()
    config_list = load_config(args.json)
    runner = FloodRunner(
        config_list=config_list,
        threads=args.threads,
        requests_per_thread=args.requests,
        wait=args.wait,
        pid=args.pid,
        shuffle=not args.no_shuffle,
        log=not args.no_log,
        export=args.export,
        export_format=args.export_format,
    )
    runner.run()
