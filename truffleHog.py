#!/usr/bin/env python3
"""Enhanced version of truffleHog scanner."""

import argparse
import git
import hashlib
import json
import math
import os
import shutil
import string
import sys

from datetime import datetime
from distutils import dir_util
from glob import glob
from signal import signal, SIGINT
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import regexes


MAX_LINE_LENGTH = 160
MAX_MATCH_LENGTH = 1000

BASE64_CHARS = string.ascii_letters + string.digits + "+/="
HEX_CHARS = string.hexdigits


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def main():
    graceful_keyboard_interrupt()
    args = get_cmdline_args()
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

            issues = search_history(
                tmp, args.rules,
                since_commit=args.since_commit,
                max_depth=args.max_depth, branch=args.branch,
                no_regex=args.no_regex, no_entropy=args.no_entropy
            )

        issues += search(
            tmp, args.rules,
            no_regex=args.no_regex, no_entropy=args.no_entropy
        )

    for issue in issues:
        log_issue(issue, output=args.output, json_output=args.json_output)

    return 1 if issues else 0


def search(path, regexes, no_regex=False, no_entropy=False):
    issues = []

    for file in glob(os.path.join(path, "**"), recursive=True):
        if not os.path.isfile(file):
            continue

        to_log = file.replace(path, "")
        commit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found = []

        with open(file) as f:
            try:
                data = f.read()
            except Exception:
                continue

            if not no_regex:
                found += regex_check(data, regexes, line_numbers=True)

            if not no_entropy:
                found += find_entropy(data, line_numbers=True)

            for issue in found:
                data = {
                    "date": commit_time,
                    "path": to_log,
                    "branch": "current state",
                    "commit": None,
                    "commitHash": None,
                }
                issue.update(data)

            issues += found
    return issues


def search_history(path, regexes, no_regex=False, no_entropy=False,
                   since_commit=None, max_depth=1000000, branch=None):
    issues = []
    already_searched = set()
    repo = git.Repo(path)

    if branch:
        branches = repo.remotes.origin.fetch(branch)
    else:
        branches = repo.remotes.origin.fetch()

    for remote_branch in branches:
        since_commit_reached = False
        branch = remote_branch.name
        prev_commit = None

        for curr_commit in repo.iter_commits(branch, max_count=max_depth):
            if curr_commit.hexsha == since_commit:
                since_commit_reached = True

            if since_commit and since_commit_reached:
                prev_commit = curr_commit
                continue
            # if not prev_commit, then curr_commit is the newest commit.
            # And we have nothing to diff with.
            # But we will diff the first commit with NULL_TREE here
            # to check the oldest code.
            # In this way, no commit will be missed.
            diff_enc = (str(prev_commit) + str(curr_commit)).encode("utf-8")
            diff_hash = hashlib.md5(diff_enc).digest()

            if not prev_commit:
                prev_commit = curr_commit
                continue

            elif diff_hash in already_searched:
                prev_commit = curr_commit
                continue

            else:
                diff = prev_commit.diff(curr_commit, create_patch=True)

            # avoid searching the same diffs
            already_searched.add(diff_hash)
            issues += diff_worker(
                diff, regexes, prev_commit, branch,
                no_regex=no_regex, no_entropy=no_entropy
            )
            # output = handle_results(output, output_dir, foundIssues)
            prev_commit = curr_commit

        # Handling the first commit
        diff = curr_commit.diff(git.NULL_TREE, create_patch=True)
        issues += diff_worker(
            diff, regexes, prev_commit, branch,
            no_regex=no_regex, no_entropy=no_entropy
        )
    return issues


def diff_worker(diff, regexes, commit, branch,
                no_regex=False, no_entropy=False):
    issues = []
    for blob in diff:
        printableDiff = blob.diff.decode("utf-8", errors="replace")
        if printableDiff.startswith("Binary files"):
            continue

        date = datetime.fromtimestamp(commit.committed_date)
        commit_time = date.strftime("%Y-%m-%d %H:%M:%S")
        path = blob.b_path if blob.b_path else blob.a_path
        if not path.startswith("/"):
            path = "/" + path

        found = []
        if not no_regex:
            found += regex_check(printableDiff, regexes)

        if not no_entropy:
            found += find_entropy(printableDiff)

        for issue in found:
            data = {
                "date": commit_time,
                "path": path,
                "branch": branch,
                "commit": commit.message,
                "commitHash": commit.hexsha,
            }
            issue.update(data)

        issues += found
    return issues


def find_entropy_match(word, chars, threshold):
    found = []
    strings = get_strings_of_set(word, chars)

    for match in strings:
        entropy = shannon_entropy(match, chars)
        if entropy > threshold:
            found.append(match)

    return found


def find_entropy(diff, line_numbers=False):
    matched, issues = [], []

    for i, line in enumerate(diff.split("\n")):
        for word in line.split():
            line_number = i + 1 if line_numbers else None
            entropy_match = find_entropy_match(word, BASE64_CHARS, 4.5)
            entropy_match += find_entropy_match(word, HEX_CHARS, 3.0)
            matched += process_matched(line, entropy_match, line_number)

    if matched:
        issues = [{"stringsFound": matched, "reason": "High Entropy"}]
    return issues


def regex_check(diff, regexes, line_numbers=False):
    issues = []

    for key in regexes:
        matched = []
        for i, line in enumerate(diff.split("\n")):
            line_number = i + 1 if line_numbers else None
            matched_words = regexes[key].findall(line)
            matched += process_matched(line, matched_words, line_number)

        if matched:
            issues.append({"stringsFound": matched, "reason": key})
    return issues


def process_matched(line, matched_words, line_number=None):
    matched = []
    if matched_words:
        if len(line) <= MAX_LINE_LENGTH:
            matched_words = [line]

        for match in matched_words:
            if len(match) > MAX_MATCH_LENGTH:
                continue
            if line_number:
                match = f"{line_number} {match}"
            matched.append(str(match).strip())
    return matched


def shannon_entropy(data, iterator):
    if not data:
        return 0

    entropy = 0
    for x in iterator:
        p_x = float(data.count(x))/len(data)

        if p_x > 0:
            entropy += -p_x * math.log(p_x, 2)

    return entropy


def get_strings_of_set(word, char_set, threshold=20):
    count = 0
    letters = ""
    strings = []

    for char in word:
        if char in char_set:
            letters += char
            count += 1
        else:
            if count > threshold:
                strings.append(letters)

            letters = ""
            count = 0

    if count > threshold:
        strings.append(letters)

    return strings


def colorize(message, color=bcolors.OKGREEN):
    return f"{color}{message}{bcolors.ENDC}"


def log_issue(issue, output=None, json_output=False):
    if json_output:
        data = json.dumps(issue, sort_keys=True)
    else:
        data = "\n".join(str(x) for x in (
            "~~~~~~~~~~~~~~~~~~~~~",
            colorize(f"Reason: {issue.get('reason')}"),
            colorize(f"Filepath: {issue.get('path')}"),
            colorize(f"Branch: {issue.get('branch')}"),
            colorize(f"Commit: {issue.get('commit')}"),
            colorize(f"Hash: {issue.get('commitHash')}"),
            "\n".join(issue.get("stringsFound")),
            "~~~~~~~~~~~~~~~~~~~~~"
        ))
    if output:
        output.write(data + "\n")
    else:
        print(data)


def graceful_keyboard_interrupt():
    def exit_on_keyboard_interrupt():
        sys.stdout.write("\rKeyboard interrupt. Exiting\n")
        sys.exit(0)

    signal(SIGINT, lambda signal, frame: exit_on_keyboard_interrupt())


def check_source(source):
    if not urlparse(source).scheme:
        source = f"file://{os.path.abspath(source)}"
    return source


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description="Find secrets hidden in the depths of git.",
    )
    parser.add_argument(
        "-r", "--rules", help="ignore default regexes and source from json",
        dest="rules", type=regexes.load, default=regexes.DEFAULT
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
