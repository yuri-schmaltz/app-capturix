from __future__ import annotations

from .cli import parse_args, mode_from_str
from .app import run_app, run_snip_mode


def main():
    args = parse_args()

    if args.snip:
        run_snip_mode(
            initial_mode=mode_from_str(args.mode),
            delay=args.delay,
            log_to_console=args.log_console,
        )
    else:
        run_app(log_to_console=args.log_console)


if __name__ == "__main__":
    main()
