#!/usr/bin/env python3
"""truffleHog scanner core."""

import argparse
import git
import os
import shutil
import sys

from distutils import dir_util
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from urllib import parse

from truffleHog3 import scanner


def main(args=None):
    graceful_keyboard_interrupt()
    args = args or get_cmdline_args()
    issues = []

    with TemporaryDirectory() as tmp:
        if args.no_history:
            source = args.source.split(":")[-1]
            if os.path.isdir(source):
                dir_util.copy_tree(source, tmp)
            else:
                shutil.copy2(source, tmp)
        else:
            try:
                git.Repo.clone_from(args.source, tmp)
            except Exception:
                error = f"Failed to clone repository: {args.source}"
                raise RuntimeError(error)

            issues = scanner.search_history(
                tmp, args.rules,
                since_commit=args.since_commit,
                max_depth=args.max_depth, branch=args.branch,
                no_regex=args.no_regex, no_entropy=args.no_entropy
            )

        issues += scanner.search(
            tmp, args.rules,
            no_regex=args.no_regex, no_entropy=args.no_entropy
        )

    for issue in issues:
        scanner.log(issue, output=args.output, json_output=args.json_output)

    return bool(issues)


def graceful_keyboard_interrupt():
    def exit_on_keyboard_interrupt():
        sys.stdout.write("\rKeyboard interrupt. Exiting\n")
        sys.exit(0)

    signal(SIGINT, lambda signal, frame: exit_on_keyboard_interrupt())


def check_source(source):
    if not parse.urlparse(source).scheme:
        source = f"file://{os.path.abspath(source)}"
    return source


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description="Find secrets hidden in the depths of git.",
    )
    parser.add_argument(
        "-r", "--rules", help="ignore default regexes and source from json",
        dest="rules", type=scanner.load, default=scanner.DEFAULT
    )
    parser.add_argument(
        "-o", "--output", help="write report to file",
        dest="output", type=argparse.FileType("w")
    )
    parser.add_argument(
        "--json", help="output in JSON",
        dest="json_output", action="store_true"
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
    parser.add_argument(
        "--since-commit", help="only scan starting from a given commit hash",
        dest="since_commit"
    )
    parser.add_argument(
        "--max-depth", help="max commit depth when searching for secrets",
        dest="max_depth", default=1000000
    )
    parser.add_argument(
        "--branch", help="name of the branch to be scanned", dest="branch"
    )
    parser.add_argument(
        "source", help="URL or local path for secret searching",
        type=check_source
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
