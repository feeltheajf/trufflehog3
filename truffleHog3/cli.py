#!/usr/bin/env python3

import argparse
import git
import logging
import os
import shutil
import sys

from distutils import dir_util
from io import IOBase
from itertools import chain
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from urllib import parse

from truffleHog3.lib import log, utils
from truffleHog3.lib.source import Simple, Git, SELF
from truffleHog3.lib.search import Regex, Entropy
from truffleHog3.lib.render import TEXT, JSON, YAML, HTML
from truffleHog3.types import Config, File, Issues, Rules


_RULES = os.path.join(os.path.dirname(__file__), "rules.yaml")


def run():
    args = _get_cmdline_args()
    log.setLevel(logging.ERROR - args.verbose * 10)

    if args.render_html:
        issues = []
        for src in args.source:
            log.info(f"loading '{src}'")
            issues.extend(utils.load(src))

        write(issues, file=args.output, format="html")
        return 0

    if args.config:
        config = _load_config(args.config)

    rules = utils.load(args.rules)
    issues = []

    for src in args.source:
        with TemporaryDirectory() as tmp:
            copy(src, tmp)
            if not args.config:
                config = _search_config(tmp)
            issues.extend(scan(tmp, config, rules))

    write(issues, file=args.output, format=args.format)
    return bool(issues)


def copy(source: str, destination: str):
    log.info(f"copying '{source}' to '{destination}'")
    if parse.urlparse(source).scheme in ("http", "https"):
        git.Repo.clone_from(source, destination)
    else:
        if os.path.isdir(source):
            dir_util.copy_tree(source, destination, preserve_symlinks=True)
        else:
            shutil.copy2(source, destination)


def scan(path: str, config: Config, rules: Rules = None) -> Issues:
    g = []
    if not config.no_history:
        try:
            g.append(
                Git(
                    path,
                    branch=config.branch,
                    since_commit=config.since_commit,
                    max_depth=config.max_depth,
                    skip=config.skip_paths,
                )
            )
        except Exception:  # pragma: no cover
            log.warning("not a Git repository")

    if not config.no_current:
        g.append(Simple(path, skip=config.skip_paths))

    engine_config = dict(
        skip=config.skip_strings, line_numbers=config.line_numbers
    )
    engines = []
    if not config.no_entropy:
        engines.append(Entropy(**engine_config))
    if not config.no_regex:
        engines.append(Regex(rules, **engine_config))

    issues = []
    for meta in chain(*g):
        for engine in engines:
            issues.extend(engine.process(meta))

    return issues


def write(issues: Issues, file: File = None, format: str = "text"):
    if format == "text":
        f = TEXT
    elif format == "json":
        f = JSON
    elif format == "yaml":
        f = YAML
    elif format == "html":
        f = HTML
    else:
        raise NotImplementedError(f"unknown format: {format}")

    log.info(f"writing {format.upper()} to '{_name(file)}'")
    utils.dump(f(issues), file)


def _search_config(path: str) -> Config:
    for config_name in SELF:
        config_path = os.path.join(path, config_name)
        if os.path.exists(config_path):
            return _load_config(open(config_path))
    return _load_config()


def _load_config(file: File = None) -> Config:
    config = Config()
    if file:
        user_config = utils.load(file)
        if user_config:
            config.update(**user_config)
        else:
            log.warning(f"empty config supplied: '{_name(file)}'")

    args = _get_cmdline_args(**config.raw)
    config.update(**args.__dict__)
    log.info(f"using config\n\n{config}")
    return config


def _name(file: File = None) -> str:  # pragma: no cover
    if isinstance(file, IOBase):
        return file.name
    return file


def _graceful_keyboard_interrupt():  # pragma: no cover
    def exit_on_keyboard_interrupt():
        sys.stdout.write("\r")
        log.critical("Keyboard interrupt. Exiting")
        sys.exit(0)

    signal(SIGINT, lambda signal, frame: exit_on_keyboard_interrupt())


class _HelpFormatter(argparse.HelpFormatter):  # pragma: no cover
    def _format_action_invocation(self, action):
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        return ", ".join(action.option_strings)


def _get_cmdline_args(**defaults) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find secrets in your codebase.",
        usage="trufflehog3 [options] source",
        formatter_class=_HelpFormatter,
    )
    parser.add_argument(
        "source",
        help="URLs or paths to local folders for secret searching",
        nargs="+",
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
        "-c",
        "--config",
        help="path to config file",
        dest="config",
        type=argparse.FileType("r"),
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write report to file",
        dest="output",
        type=argparse.FileType("w"),
    )
    parser.add_argument(
        "-f",
        "--format",
        help="output format {text, json, yaml, html}",
        dest="format",
        type=lambda f: f.lower(),
        choices=["text", "json", "yaml", "html"],
        default="text",
    )
    parser.add_argument(
        "-r",
        "--rules",
        help="ignore default regexes and source from file",
        dest="rules",
        type=argparse.FileType("r"),
        default=_RULES,
    )
    parser.add_argument(
        "-R",
        "--render-html",
        help="render HTML report from JSON or YAML",
        dest="render_html",
        action="store_true",
    )
    parser.add_argument(
        "--branch",
        help="name of the repository branch to be scanned",
        dest="branch",
    )
    parser.add_argument(
        "--since-commit",
        help="scan starting from a given commit hash",
        dest="since_commit",
    )
    parser.add_argument(
        "--skip-strings",
        help="skip matching strings",
        dest="skip_strings",
        nargs="*",
    )
    parser.add_argument(
        "--skip-paths",
        help="skip paths matching regex",
        dest="skip_paths",
        nargs="*",
    )
    parser.add_argument(
        "--line-numbers",
        help="include line numbers in match",
        dest="line_numbers",
        action="store_true",
    )
    parser.add_argument(
        "--max-depth",
        help="max commit depth for searching",
        dest="max_depth",
        type=int,
    )
    parser.add_argument(
        "--no-regex",
        help="disable high signal regex checks",
        dest="no_regex",
        action="store_true",
    )
    parser.add_argument(
        "--no-entropy",
        help="disable entropy checks",
        dest="no_entropy",
        action="store_true",
    )
    parser.add_argument(
        "--no-history",
        help="disable commit history check",
        dest="no_history",
        action="store_true",
    )
    parser.add_argument(
        "--no-current",
        help="disable current status check",
        dest="no_current",
        action="store_true",
    )
    parser.set_defaults(**defaults)
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    _graceful_keyboard_interrupt()
    sys.exit(run())
