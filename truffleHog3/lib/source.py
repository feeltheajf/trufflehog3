import git
import os

from abc import ABC, abstractmethod
from datetime import datetime

from truffleHog3.lib import log, utils
from truffleHog3.types import List, MetaGen, Regexes


_FMT = "%Y-%m-%d %H:%M:%S"
_NOW = datetime.now().strftime(_FMT)

SELF = ["trufflehog.json", "trufflehog.yaml", "trufflehog.yml"]


class Engine(ABC):
    def __init__(self, path: str, skip: List[str] = None):
        self.path = path
        self.regexes = skip

    @property
    def regexes(self) -> Regexes:
        return self._regexes

    @regexes.setter
    def regexes(self, skip: List[str]):
        self._regexes = utils.compile((skip or []) + SELF)

    @abstractmethod
    def __iter__(self) -> MetaGen:
        ...  # pragma: no cover

    def skip(self, path: str) -> bool:
        regex = utils.match(path, self.regexes)
        if regex:
            log.info(f"skipping '{path}' matched by '{regex}'")
            return True

        return False


class Simple(Engine):
    def __iter__(self) -> MetaGen:
        for root, dirs, files in os.walk(self.path):
            for d in dirs:
                if d.startswith(".") or self.skip(d):
                    dirs.remove(d)

            for file in files:
                filepath = os.path.join(root, file)
                relative_path = os.path.relpath(filepath, self.path)
                if self.skip(relative_path):
                    continue

                try:
                    with open(filepath) as f:
                        data = f.read()
                except Exception as error:  # pragma: no cover
                    log.warning(f"error reading '{filepath}': {error}")
                    continue

                yield {
                    "date": _NOW,
                    "path": relative_path,
                    "branch": None,
                    "commit": None,
                    "commitHash": None,
                    "data": data,
                }


class Git(Engine):
    def __init__(
        self,
        path: str,
        branch: str = None,
        since_commit: str = None,
        max_depth: int = None,
        **kwargs,
    ):
        self.repo = git.Repo(path)
        self.branch = branch
        self.since_commit = since_commit
        self.max_depth = max_depth
        super().__init__(path, **kwargs)

    def __iter__(self):
        already_searched = set()

        for branch in self._get_branches():
            log.info(f"switching to branch '{branch}'")
            prev_commit = None
            since_commit_reached = False
            commits = self.repo.iter_commits(branch, max_count=self.max_depth)

            for curr_commit in commits:
                if curr_commit.hexsha == self.since_commit:
                    since_commit_reached = True

                if self.since_commit and since_commit_reached:
                    prev_commit = curr_commit
                    continue

                diff_hash = str(prev_commit) + str(curr_commit)
                if not prev_commit or diff_hash in already_searched:
                    prev_commit = curr_commit
                    continue

                diff = prev_commit.diff(curr_commit, create_patch=True)
                already_searched.add(diff_hash)
                yield from self._diff_worker(diff, prev_commit, branch)
                prev_commit = curr_commit

            diff = curr_commit.diff(git.NULL_TREE, create_patch=True)
            yield from self._diff_worker(diff, prev_commit, branch)

    def _diff_worker(
        self, diff: git.DiffIndex, commit: git.Commit, branch: git.Head = None
    ) -> MetaGen:
        for blob in diff:
            pdiff = blob.diff.decode("utf-8", errors="replace")
            path = blob.b_path if blob.b_path else blob.a_path

            if pdiff.startswith("Binary files") or self.skip(path):
                continue

            date = datetime.fromtimestamp(commit.committed_date)
            yield {
                "date": date.strftime(_FMT),
                "path": path,
                "branch": branch.name,
                "commit": commit.message,
                "commitHash": commit.hexsha,
                "data": pdiff,
            }

    def _get_branches(self) -> List[git.Head]:
        if self.repo.remotes:  # pragma: no cover
            try:
                return self.repo.remotes.origin.fetch(self.branch)
            except git.GitCommandError as error:
                log.warning(f"error fetching remote branches: {error}")
        else:
            log.warning("missing remote")

        if not self.branch:
            branches = [self.repo.active_branch]
        else:
            branches = [self.repo.branches[self.branch]]

        return branches
