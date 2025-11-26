from __future__ import annotations

import argparse

from .core.models import CaptureMode


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="linsnipper")

    parser.add_argument(
        "--snip",
        action="store_true",
        help="Inicia diretamente em modo de captura (overlay).",
    )
    parser.add_argument(
        "--mode",
        choices=["rect", "freeform", "window", "fullscreen"],
        default="rect",
        help="Modo inicial de captura.",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help="Delay em segundos antes da captura (0, 3, 5, 10).",
    )
    parser.add_argument(
        "--log-console",
        action="store_true",
        help="Também logar no console (debug).",
    )

    return parser


def parse_args(argv=None):
    parser = build_arg_parser()
    return parser.parse_args(argv)


def mode_from_str(s: str) -> CaptureMode:
    mapping = {
        "rect": CaptureMode.RECTANGLE,
        "freeform": CaptureMode.FREEFORM,
        "window": CaptureMode.WINDOW,
        "fullscreen": CaptureMode.FULLSCREEN,
    }
    return mapping.get(s, CaptureMode.RECTANGLE)
