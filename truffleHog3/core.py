"""truffleHog3 scanner core."""

import git
import hashlib
import json
import math
import os
import re
import string

from datetime import datetime
from glob import glob
from io import IOBase


def search_current(path):
    issues = []

    for file in glob(os.path.join(path, "**"), recursive=True):
        if not os.path.isfile(file) or _match(file, config._exclude):
            continue

        to_log = file.replace(path, "")
        commit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found = []

        with open(file) as f:
            try:
                data = f.read()
            except Exception:  # pragma: no cover
                continue

            if not config.no_regex:
                found += _search_regex(data, config.rules, line_numbers=True)

            if not config.no_entropy:
                found += _search_entropy(data, line_numbers=True)

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
            elif diff_hash in already_searched:  # pragma: no cover
                prev_commit = curr_commit
                continue
            else:
                diff = prev_commit.diff(curr_commit, create_patch=True)

            # avoid searching the same diffs
            already_searched.add(diff_hash)
            issues += _diff_worker(diff, prev_commit)
            prev_commit = curr_commit

        # Handling the first commit
        diff = curr_commit.diff(git.NULL_TREE, create_patch=True)
        issues += _diff_worker(diff, prev_commit)

    return issues


def log(issues, output=None, json_output=False):
    if json_output:
        report = json.dumps(issues, indent=2)  # pragma: no cover
    else:
        report = "\n".join(_render(issue) for issue in issues)

    if output:
        output.write(report)  # pragma: no cover
    else:
        print(report)


def _diff_worker(diff, commit):
    issues = []

    for blob in diff:
        pdiff = blob.diff.decode("utf-8", errors="replace")
        path = blob.b_path if blob.b_path else blob.a_path

        if not path.startswith("/"):
            path = "/" + path

        if pdiff.startswith("Binary files") or _match(path, config._exclude):
            continue

        date = datetime.fromtimestamp(commit.committed_date)
        commit_time = date.strftime("%Y-%m-%d %H:%M:%S")

        found = []
        if not config.no_regex:
            found += _search_regex(pdiff, config.rules)

        if not config.no_entropy:
            found += _search_entropy(pdiff)

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


def _process_matched(line, matched_words, line_number=None):
    matched = []
    if matched_words:
        if len(line) <= MAX_LINE_LENGTH:
            matched_words = [line]

        for match in matched_words:
            if _match(match, config.whitelist):
                continue

            if len(match) > MAX_MATCH_LENGTH:
                continue  # pragma: no cover

            if line_number:
                match = "{} {}".format(line_number, match)

            matched.append(str(match).strip())

    return matched


def _search_regex(data, rules, line_numbers=False):
    issues = []

    for key in rules:
        matched = []
        for i, line in enumerate(data.split("\n")):
            line_number = i + 1 if line_numbers else None
            matched_words = re.findall(rules[key], line)
            for i, m in enumerate(matched_words):
                if isinstance(m, tuple) and len(m):
                    matched_words[i] = m[0]
            matched += _process_matched(line, matched_words, line_number)

        if matched:
            issues.append({"stringsFound": matched, "reason": key})

    return issues


def _search_entropy(data, line_numbers=False):
    matched, issues = [], []

    for i, line in enumerate(data.split("\n")):
        for word in line.split():
            line_number = i + 1 if line_numbers else None
            entropy_match = _find_entropy_match(word, BASE64_CHARS, 4.5)
            entropy_match += _find_entropy_match(word, HEX_CHARS, 3.0)
            matched += _process_matched(line, entropy_match, line_number)

    if matched:
        issues = [{"stringsFound": matched, "reason": "High Entropy"}]

    return issues


def _find_entropy_match(word, chars, threshold):
    found = []
    strings = _get_strings_of_set(word, chars)

    for match in strings:
        entropy = _shannon_entropy(match, chars)
        if entropy > threshold:
            found.append(match)

    return found


def _get_strings_of_set(word, char_set, threshold=20):
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


def _shannon_entropy(data, iterator):
    if not data:
        return 0  # pragma: no cover

    entropy = 0
    for x in iterator:
        p_x = float(data.count(x))/len(data)

        if p_x > 0:
            entropy += -p_x * math.log(p_x, 2)

    return entropy


def _render(issue):
    strings = "\n".join(issue["stringsFound"])
    colored = TEMPLATE % (colors.OKGREEN, colors.ENDC)
    return colored.format(**issue, strings=strings)


def _match(string, regexes):
    for regex in regexes:
        if re.search(regex, string):
            return True
    return False


class _Colors:
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
        self.rules = DEFAULT_RULES
        self.branch = None
        self.max_depth = 1000000
        self.since_commit = None
        self.exclude = []
        self.whitelist = []
        self.no_regex = False
        self.no_entropy = False
        self.no_history = False

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def dump(self, stream):  # pragma: no cover
        json.dump(self.as_dict, stream, indent=2)

    def load(self, stream):  # pragma: no cover
        self.update(**json.load(stream))

    @property
    def rules(self):
        return self._rules

    @rules.setter
    def rules(self, file):
        if not isinstance(file, IOBase):
            file = open(file)
        self._rules = json.load(file)

    @property
    def _exclude(self):
        return self.exclude + [DEFAULT_CONFIG]

    @property
    def as_dict(self):
        items = self.__dict__.items()
        return {k: v for k, v in items if not k.startswith("_")}


DEFAULT_CONFIG = "trufflehog.json"
DEFAULT_RULES = os.path.join(os.path.dirname(__file__), "regexes.json")

MAX_LINE_LENGTH = 160  # intentionally not in config yet
MAX_MATCH_LENGTH = 1000  # intentionally not in config yet

BASE64_CHARS = string.ascii_letters + string.digits + "+/="
HEX_CHARS = string.hexdigits

TEMPLATE = """~~~~~~~~~~~~~~~~~~~~~%s
Reason: {reason}
Path:   {path}
Branch: {branch}
Commit: {commit}
Hash:   {commitHash}
%s{strings}
~~~~~~~~~~~~~~~~~~~~~"""

colors = _Colors()
config = _Config()
