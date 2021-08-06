#!/usr/bin/env python3
"""Trufflehog3 CLI."""

import argparse
import git
import logging
import multiprocessing
import os
import sys

from pathlib import Path
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from typing import Callable
from urllib.parse import urlparse

from trufflehog3 import __NAME__, __VERSION__
from trufflehog3 import DEFAULT_RULES_FILE
from trufflehog3 import log

from trufflehog3.core import diff, load, load_config, load_rules, render, scan
from trufflehog3.models import (
    Config,
    Exclude,
    Format,
    Issue,
    Severity,
)

MORE = f"""
learn more:
  https://github.com/feeltheajf/{__NAME__}

version:
  {__VERSION__}
"""

try:
    CPU_COUNT = multiprocessing.cpu_count()
except NotImplementedError:  # pragma: no cover
    CPU_COUNT = 1


def run(**kwargs):
    """Run CLI."""
    args = _get_cmdline_args(**kwargs)
    log.setLevel(logging.ERROR - args.verbose * 10)

    if args.render_html:  # pragma: no cover
        issues = []
        for f in args.targets:
            issues.extend(load(Issue, f))
        render(issues, format=Format.HTML, file=args.output)
        return 0

    kw = {k: v for k, v in args.__dict__.items() if hasattr(Config(), k) and v}
    if args.config:  # pragma: no cover
        config = load_config(args.config, **kw)

    rules = load_rules(args.rules, args.severity)
    issues = []

    for target in args.targets:
        if urlparse(target).scheme in ("http", "https"):  # pragma: no cover
            with TemporaryDirectory(prefix=f"{__NAME__}-") as tmp:
                git.Repo.clone_from(target, tmp)
                target = tmp

        if not args.config:
            config = load_config(target, **kw)

        issues.extend(scan(target, config, rules, args.processes))

    if args.incremental:  # pragma: no cover
        issues = diff(load(Issue, args.incremental), issues, only_new=True)

    render(issues, format=args.format, file=args.output)
    return 0 if args.zero else bool(issues)


class _HelpFormatter(argparse.RawTextHelpFormatter):  # pragma: no cover
    def __init__(self, prog):
        super().__init__(prog, max_help_position=26)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)

        options = ", ".join(action.option_strings)
        if action.choices:
            options += " {%s}" % ", ".join(str(c) for c in action.choices)
        elif action.metavar:
            options += " " + action.metavar

        return options


def _exclude(s: str) -> Exclude:
    """Convert string to exclude rule.

    Examples
    --------
    Basic usage examples

    >>> _exclude("p1,p2")
    Exclude(message='p1,p2', id=None, pattern=None, paths=['p1', 'p2'])

    >>> _exclude("re:p")
    Exclude(message='re:p', id=None, pattern=re.compile('re'), paths=['p'])
    """
    if ":" in s:
        pattern, paths = s.split(":", 1)
    else:
        pattern, paths = None, s
    return Exclude(message=s, pattern=pattern, paths=paths.split(","))


def _file(mode: str = "r") -> Callable[[str], Path]:  # pragma: no cover
    def validate(filepath: str) -> Path:
        path = Path(filepath)
        file = path.open(mode)
        file.close()
        return path

    return validate


def _get_cmdline_args(**defaults) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find secrets in your codebase",
        epilog=MORE,
        usage=f"{__NAME__} [arguments] targets",
        formatter_class=_HelpFormatter,
    )
    parser.add_argument(
        "targets",
        help="Search targets, defaults to current directory",
        nargs=argparse.ZERO_OR_MORE,
        default=[os.curdir],
    )
    parser.add_argument(
        "-z",
        "--zero",
        help="always exit with zero status code",
        dest="zero",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="enable verbose logging {-v, -vv, -vvv}",
        dest="verbose",
        action="count",
        default=0,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="path to output file",
        dest="output",
        metavar="file",
        type=_file("w"),
    )
    parser.add_argument(
        "-c",
        "--config",
        help="path to config file",
        dest="config",
        metavar="file",
        type=_file("r"),
    )
    parser.add_argument(
        "-r",
        "--rules",
        help="path to rules file",
        dest="rules",
        metavar="file",
        type=_file("r"),
        default=DEFAULT_RULES_FILE,
    )
    parser.add_argument(
        "-i",
        "--incremental",
        help="path to previous scan",
        dest="incremental",
        metavar="file",
        type=_file("r"),
    )
    parser.add_argument(
        "-p",
        "--processes",
        help="number of subprocesses to run (%(default)s)",
        dest="processes",
        metavar="int",
        type=int,
        default=CPU_COUNT,
    )
    search = parser.add_argument_group("search arguments")
    search.add_argument(
        "-e",
        "--exclude",
        help="exclude matching issues",
        dest="exclude",
        metavar="str",
        type=_exclude,
        nargs=argparse.ZERO_OR_MORE,
    )
    search.add_argument(
        "-s",
        "--severity",
        help="minimum severity filter (%(default)s)",
        dest="severity",
        metavar="str",
        type=Severity,
        choices=[Severity.LOW, Severity.MEDIUM, Severity.HIGH],
        default=Severity.LOW,
    )
    search.add_argument(
        "--ignore-nosecret",
        help="ignore inline 'nosecret' annotations",
        dest="ignore_nosecret",
        action="store_true",
    )
    mgroup = search.add_mutually_exclusive_group()
    mgroup.add_argument(
        "--no-entropy",
        help="disable entropy checks",
        dest="no_entropy",
        action="store_true",
    )
    mgroup.add_argument(
        "--no-pattern",
        help="disable pattern checks",
        dest="no_pattern",
        action="store_true",
    )
    source = parser.add_argument_group("source arguments")
    source.add_argument(
        "--branch",
        help="name of the repo branch to scan",
        dest="branch",
        metavar="str",
    )
    commit = source.add_mutually_exclusive_group()
    commit.add_argument(
        "--depth",
        help="max commits depth for searching (%(default)s)",
        dest="depth",
        type=int,
        metavar="int",
        default=10000,
    )
    commit.add_argument(
        "--since",
        help="scan from the given commit hash",
        dest="since",
    )
    mgroup = source.add_mutually_exclusive_group()
    mgroup.add_argument(
        "--no-current",
        help="disable current status check",
        dest="no_current",
        action="store_true",
    )
    mgroup.add_argument(
        "--no-history",
        help="disable commit history check",
        dest="no_history",
        action="store_true",
    )
    render = parser.add_argument_group("render arguments")
    render.add_argument(
        "-f",
        "--format",
        help="output format (%(default)s)",
        dest="format",
        metavar="str",
        type=Format,
        choices=[Format.TEXT, Format.JSON, Format.HTML],
        default=Format.TEXT,
    )
    render.add_argument(
        "--context",
        help="number of context lines to include",
        dest="context",
        metavar="int",
        type=int,
        default=0,
    )
    helper = parser.add_argument_group("other commands")
    others = helper.add_mutually_exclusive_group()
    others.add_argument(
        "-R",
        "--render-html",
        help="render HTML report from JSON",
        dest="render_html",
        action="store_true",
    )
    parser.set_defaults(**defaults)
    return parser.parse_args()


def _exit_on_keyboard_interrupt(*args, **kwargs):  # pragma: no cover
    sys.stdout.write("\r")
    log.fatal("Keyboard interrupt. Exiting")
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    signal(SIGINT, _exit_on_keyboard_interrupt)
    sys.exit(run())
