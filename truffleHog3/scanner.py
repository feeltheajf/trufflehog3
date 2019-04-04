"""truffleHog scanner core."""

import git
import hashlib
import json
import math
import os
import re
import string

from datetime import datetime
from glob import glob


def search(path):
    issues = []

    for file in glob(os.path.join(path, "**"), recursive=True):
        if not os.path.isfile(file) or is_excluded(file):
            continue

        to_log = file.replace(path, "")
        commit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found = []

        with open(file) as f:
            try:
                data = f.read()
            except Exception:
                continue

            if not config.no_regex:
                found += regex_check(data, config.rules, line_numbers=True)

            if not config.no_entropy:
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


def search_history(path):
    issues = []
    already_searched = set()
    repo = git.Repo(path)

    if config.branch:
        branches = repo.remotes.origin.fetch(config.branch)
    else:
        branches = repo.remotes.origin.fetch()

    for remote_branch in branches:
        since_commit_reached = False
        branch = remote_branch.name
        prev_commit = None
        commits = repo.iter_commits(branch, max_count=config.max_depth)

        for curr_commit in commits:
            if curr_commit.hexsha == config.since_commit:
                since_commit_reached = True

            if config.since_commit and since_commit_reached:
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
            issues += diff_worker(diff, prev_commit)
            prev_commit = curr_commit

        # Handling the first commit
        diff = curr_commit.diff(git.NULL_TREE, create_patch=True)
        issues += diff_worker(diff, prev_commit)

    return issues


def diff_worker(diff, commit):
    issues = []
    for blob in diff:
        printableDiff = blob.diff.decode("utf-8", errors="replace")
        path = blob.b_path if blob.b_path else blob.a_path

        if printableDiff.startswith("Binary files") or is_excluded(path):
            continue

        date = datetime.fromtimestamp(commit.committed_date)
        commit_time = date.strftime("%Y-%m-%d %H:%M:%S")

        if not path.startswith("/"):
            path = "/" + path

        found = []
        if not config.no_regex:
            found += regex_check(printableDiff, config.rules)

        if not config.no_entropy:
            found += find_entropy(printableDiff)

        for issue in found:
            data = {
                "date": commit_time,
                "path": path,
                "branch": config.branch,
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


def regex_check(diff, rules, line_numbers=False):
    issues = []

    for key in rules:
        matched = []
        for i, line in enumerate(diff.split("\n")):
            line_number = i + 1 if line_numbers else None
            matched_words = rules[key].findall(line)
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
                match = "{} {}".format(line_number, match)
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


def log(issues, output=None, json_output=False):
    if json_output:
        report = json.dumps(issues, indent=2)
    else:
        report = "\n".join(render(issue) for issue in issues)

    if output:
        output.write(report)
    else:
        print(report)


def render(issue):
    strings = "\n".join(issue["stringsFound"])
    return TEMPLATE.format(**issue, strings=strings)


def load(file):
    if not os.path.exists(file):
        raise IOError("File does not exist: {}".format(file))

    with open(file, "r") as f:
        rules = json.load(f)

    rules = {name: re.compile(rule) for name, rule in rules.items()}
    return rules


def is_excluded(path):
    for rule in config.exclude:
        if re.search(rule, path):
            return True
    return False


class colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class _Config:

    def __init__(self):
        self.rules = load(os.path.join(CWD, "regexes.json"))
        self.no_regex = False
        self.no_entropy = False
        self.since_commit = None
        self.max_depth = 1000000
        self.branch = None
        self.exclude = []

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    @property
    def as_dict(self):
        return self.__dict__


MAX_LINE_LENGTH = 160
MAX_MATCH_LENGTH = 1000

BASE64_CHARS = string.ascii_letters + string.digits + "+/="
HEX_CHARS = string.hexdigits

TEMPLATE = """~~~~~~~~~~~~~~~~~~~~~%s
Reason: {reason}
Path:   {path}
Branch: {branch}
Commit: {commit}
Hash:   {commitHash}
%s{strings}
~~~~~~~~~~~~~~~~~~~~~""" % (colors.OKGREEN, colors.ENDC)
CWD = os.path.dirname(__file__)

config = _Config()
