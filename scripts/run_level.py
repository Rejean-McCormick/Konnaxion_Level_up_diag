from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from levelupdiag_core.commands import find_executable
from levelupdiag_core.config import AppConfig, load_config
from levelupdiag_core.manifest import LevelInfo, get_level, list_levels, normalize_level_id
from levelupdiag_core.verdicts import exit_code

CAMPAIGN_PRESETS: dict[str, list[str]] = {
    "developer-fast": [f"N{i:02d}" for i in range(1, 6)],
    "bundle-validation": [f"N{i:02d}" for i in range(1, 6)],
    "merge-validation": [f"N{i:02d}" for i in range(1, 6)],
    "nightly": [f"N{i:02d}" for i in range(1, 11)],
    "release-preparation": [f"N{i:02d}" for i in range(1, 11)],
    "delivery-check": ["N01", "N11"],
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run LevelUpDiag-Koali levels through the shared runner."
    )
    parser.add_argument("level", nargs="?", help="level id or number, for example N04 or 4")
    parser.add_argument("--list", action="store_true", help="list manifest levels and exit")
    parser.add_argument("--all", action="store_true", help="run all enabled levels")
    parser.add_argument(
        "--campaign",
        choices=tuple(CAMPAIGN_PRESETS),
        help="run one built-in campaign preset",
    )
    parser.add_argument("--from", dest="from_level", metavar="LEVEL", help="first level in an inclusive range")
    parser.add_argument("--to", dest="to_level", metavar="LEVEL", help="last level in an inclusive range")
    parser.add_argument("--wait", action="store_true", help="wait for a directly launched windowed level")
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--windowed", action="store_true", help="launch a single level directly with a windowed interpreter")
    display.add_argument("--console", action="store_true", help="run through the canonical console runner")
    return parser


def _print_levels(levels: Sequence[LevelInfo]) -> None:
    for level in levels:
        state = "enabled" if level.enabled else "disabled"
        required = "required" if level.required else "optional"
        deps = ",".join(level.depends_on) if level.depends_on else "-"
        print(f"{level.id}  {level.name:<16} {state:<8} {required:<8} deps={deps}")


def _runner_module():
    runner_path = ROOT / "levelupdiag_core" / "runner.py"
    if not runner_path.is_file():
        raise RuntimeError(
            "levelupdiag_core.runner is unavailable; merge the Wave A runner bundle first"
        )
    from levelupdiag_core import runner

    return runner


def _load_config() -> AppConfig:
    return load_config(root=ROOT)


def _range_ids(levels: Sequence[LevelInfo], start: str | None, end: str | None) -> list[str]:
    enabled = [level.id for level in levels if level.enabled]
    if not enabled:
        raise ValueError("manifest contains no enabled levels")

    first = normalize_level_id(start) if start is not None else enabled[0]
    last = normalize_level_id(end) if end is not None else enabled[-1]
    if first not in enabled:
        raise ValueError(f"range start is not an enabled level: {first}")
    if last not in enabled:
        raise ValueError(f"range end is not an enabled level: {last}")

    start_index = enabled.index(first)
    end_index = enabled.index(last)
    if start_index > end_index:
        raise ValueError(f"invalid descending range: {first}..{last}")
    return enabled[start_index : end_index + 1]


def _windowed_interpreter() -> str:
    if sys.platform.startswith("win"):
        return find_executable("pythonw.exe") or find_executable("pythonw") or sys.executable
    return sys.executable


def _run_windowed(level: LevelInfo, *, wait: bool) -> int:
    path = level.file_path(ROOT).resolve()
    if not path.is_file():
        print(f"CONFIG_ERROR: missing level file: {path}", file=sys.stderr)
        return 4

    try:
        process = subprocess.Popen(
            [_windowed_interpreter(), str(path)],
            cwd=str(ROOT),
            shell=False,
        )
    except OSError as exc:
        print(f"INFRA_ERROR: unable to launch {level.id}: {exc}", file=sys.stderr)
        return 3

    if not wait:
        print(f"launched {level.id} — {level.name}")
        return 0
    return int(process.wait())


def _print_level_result(result: object) -> None:
    print(f"{result.level} — {result.name}: {result.verdict}")


def _print_campaign_result(result: object) -> None:
    print(f"campaign {result.campaign}: {result.verdict}")
    for level in result.levels:
        print(f"  {level.level} — {level.name}: {level.verdict}")


def _validate_mode(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    selections = int(args.level is not None) + int(args.all) + int(args.campaign is not None) + int(
        args.from_level is not None or args.to_level is not None
    )
    if args.list:
        if selections or args.windowed or args.console or args.wait:
            parser.error("--list cannot be combined with execution options")
        return
    if selections != 1:
        parser.error("choose exactly one of LEVEL, --all, --campaign, or --from/--to")
    if args.windowed and args.level is None:
        parser.error("--windowed is supported only for a single LEVEL")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_mode(parser, args)

    try:
        levels = list_levels(ROOT)
    except (OSError, ValueError) as exc:
        print(f"CONFIG_ERROR: {exc}", file=sys.stderr)
        return 4

    if args.list:
        _print_levels(levels)
        return 0

    if args.level is not None and args.windowed:
        try:
            level = get_level(args.level, ROOT)
        except (KeyError, ValueError) as exc:
            print(f"CONFIG_ERROR: {exc}", file=sys.stderr)
            return 4
        return _run_windowed(level, wait=args.wait)

    try:
        config = _load_config()
        runner = _runner_module()

        if args.level is not None:
            level = get_level(args.level, ROOT)
            result = runner.run_level(level, config, wait=True)
            _print_level_result(result)
            return exit_code(result.verdict)

        if args.all:
            result = runner.run_levels(None, config)
            _print_campaign_result(result)
            return exit_code(result.verdict)

        if args.campaign is not None:
            selected = CAMPAIGN_PRESETS[args.campaign]
            result = runner.run_campaign(args.campaign, selected, config)
            _print_campaign_result(result)
            return exit_code(result.verdict)

        selected = _range_ids(levels, args.from_level, args.to_level)
        result = runner.run_levels(selected, config)
        _print_campaign_result(result)
        return exit_code(result.verdict)
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        print(f"CONFIG_ERROR: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
