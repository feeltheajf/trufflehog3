#!/usr/bin/env python3
"""truffleHog3 scanner cli."""

import argparse
import git
import os
import shutil
import sys

from distutils import dir_util
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from urllib import parse

from truffleHog3 import core


def run(**kwargs):
    graceful_keyboard_interrupt()
    args = get_cmdline_args()
    args.__dict__.update(**kwargs)
    core.config.update(**args.__dict__)
    issues = []

    with TemporaryDirectory() as tmp:
        if args.no_history:
            source = args.source.split("://")[-1]
            if os.path.isdir(source):
                dir_util.copy_tree(source, tmp, preserve_symlinks=True)
            else:
                shutil.copy2(source, tmp)
        else:
            try:
                git.Repo.clone_from(args.source, tmp)
            except Exception:  # pragma: no cover
                error = "Failed to clone repository: {}".format(args.source)
                raise RuntimeError(error)

            issues = core.search_history(tmp)

        issues += core.search_current(tmp)

    core.log(issues, output=args.output, json_output=args.json_output)
    return bool(issues)


def graceful_keyboard_interrupt():
    def exit_on_keyboard_interrupt():  # pragma: no cover
        sys.stdout.write("\rKeyboard interrupt. Exiting\n")
        sys.exit(0)

    signal(SIGINT, lambda signal, frame: exit_on_keyboard_interrupt())


class HelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:  # pragma: no cover
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            return ", ".join(action.option_strings)


def check_source(source):
    if not parse.urlparse(source).scheme:
        source = "file://{}".format(os.path.abspath(source))
    return source


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description="Find secrets in your codebase.",
        usage="trufflehog3 [options] source",
        formatter_class=HelpFormatter
    )
    parser.add_argument(
        "source", help="URL or local path for secret searching",
        type=check_source
    )
    parser.add_argument(
        "-c", "--config", help="path to config file",
        dest="config", type=argparse.FileType("r")
    )
    parser.add_argument(
        "-r", "--rules", help="ignore default regexes and source from json",
        dest="rules", type=argparse.FileType("r"), default=argparse.SUPPRESS
    )
    parser.add_argument(
        "-o", "--output", help="write report to file",
        dest="output", type=argparse.FileType("w")
    )
    parser.add_argument(
        "-b", "--branch", help="name of the branch to be scanned",
        dest="branch"
    )
    parser.add_argument(
        "-m", "--max-depth", help="max commit depth for searching",
        dest="max_depth", type=int
    )
    parser.add_argument(
        "-s", "--since-commit", help="scan starting from a given commit hash",
        dest="since_commit"
    )
    parser.add_argument(
        "--json", help="output in JSON",
        dest="json_output", action="store_true"
    )
    parser.add_argument(
        "--exclude", help="exclude paths from scan",
        dest="exclude", nargs="*"
    )
    parser.add_argument(
        "--whitelist", help="skip matching strings",
        dest="whitelist", nargs="*"
    )
    parser.add_argument(
        "--no-regex", help="disable high signal regex checks",
        dest="no_regex", action="store_true"
    )
    parser.add_argument(
        "--no-entropy", help="disable entropy checks",
        dest="no_entropy", action="store_true"
    )
    parser.add_argument(
        "--no-history", help="disable commit history check",
        dest="no_history", action="store_true"
    )

    args, _ = parser.parse_known_args()
    default_config_path = os.path.join(
        args.source.split("://")[-1],
        core.DEFAULT_CONFIG
    )
    if args.config:
        core.config.load(args.config)
    elif os.path.exists(default_config_path):  # pragma: no cover
        core.config.load(open(default_config_path))

    parser.set_defaults(**core.config.as_dict)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(run())  # pragma: no cover
