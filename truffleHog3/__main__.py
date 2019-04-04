"""truffleHog scanner cli."""

import argparse
import git
import os
import re
import shutil
import sys

from distutils import dir_util
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from urllib import parse

from truffleHog3 import scanner


def main():
    graceful_keyboard_interrupt()
    args = get_cmdline_args()
    scanner.config.update(**args.__dict__)
    issues = []

    with TemporaryDirectory() as tmp:
        if args.no_history:
            source = args.source.split("://")[-1]
            if os.path.isdir(source):
                dir_util.copy_tree(source, tmp)
            else:
                shutil.copy2(source, tmp)
        else:
            try:
                git.Repo.clone_from(args.source, tmp)
            except Exception:
                error = "Failed to clone repository: {}".format(args.source)
                raise RuntimeError(error)

            issues = scanner.search_history(tmp)

        issues += scanner.search(tmp)

    scanner.log(issues, output=args.output, json_output=args.json_output)
    return bool(issues)


def graceful_keyboard_interrupt():
    def exit_on_keyboard_interrupt():
        sys.stdout.write("\rKeyboard interrupt. Exiting\n")
        sys.exit(0)

    signal(SIGINT, lambda signal, frame: exit_on_keyboard_interrupt())


def check_source(source):
    if not parse.urlparse(source).scheme:
        source = "file://{}".format(os.path.abspath(source))
    return source


def exclude_path_regex(regex):
    return re.compile(regex)


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description="Find secrets hidden in the depths of git.",
    )
    parser.add_argument(
        "source", help="URL or local path for secret searching",
        type=check_source
    )
    parser.add_argument(
        "-r", "--rules", help="ignore default regexes and source from json",
        dest="rules", type=scanner.load
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
        "--max-depth", help="max commit depth for searching", dest="max_depth"
    )
    parser.add_argument(
        "--branch", help="name of the branch to be scanned", dest="branch"
    )
    parser.add_argument(
        "--exclude", help="exclude paths from scanning", dest="exclude",
        type=exclude_path_regex, nargs="*", metavar=""
    )
    parser.set_defaults(**scanner.config.as_dict)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
