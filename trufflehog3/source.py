"""Supported search sources."""

import git
import os

from pathlib import Path
from typing import Iterable, Iterator, Optional

from trufflehog3 import DEFAULT_EXCLUDE_SET
from trufflehog3 import log
from trufflehog3.models import File


def dirlist(path: str, exclude: Iterable[str] = None) -> Iterable[File]:
    """Recursively iterate over directory and return existing files.

    Examples
    --------
    Basic usage examples

    >>> len(dirlist("trufflehog3/static", exclude=["*.yml"]))
    2

    """
    return list(diriter(path, exclude))


def diriter(path: str, exclude: Iterable[str] = None) -> Iterator[File]:
    """Recursively iterate over directory and yield existing files."""
    exclude_set = DEFAULT_EXCLUDE_SET | set(exclude or [])
    # Using `os.walk` here since it allows to drop whole directories.
    # `Path.rglob` requires checking every file against exclude rules.
    # This helps to save a lot of time when excluding large directories.
    for dirpath, dirnames, filenames in os.walk(path):
        rel = Path(dirpath).relative_to(path)

        for directory in dirnames:
            dirname = rel / directory
            pattern = _match(dirname, exclude_set)
            if pattern:
                log.debug(f"skipping directory '{dirname}': '{pattern}'")
                dirnames.remove(directory)

        for file in filenames:
            filename = rel / file
            if filename.is_symlink():  # pragma: no cover
                continue

            pattern = _match(filename, exclude_set)
            if pattern:
                log.debug(f"skipping file '{filename}': '{pattern}'")
                continue

            yield File(
                path=filename.as_posix(),
                absolute=filename.absolute().as_posix(),
            )


def gitlist(
    path: str,
    exclude: Iterable[str] = None,
    branch: str = None,
    depth: int = None,
    since: str = None,
) -> Iterable[File]:
    """Iterate over Git commit history and return diff blobs for each file.

    Examples
    --------
    Basic usage examples

    >>> files = gitlist(
    ...     ".",
    ...     exclude=["*.toml"],
    ...     branch="1.x",
    ...     since="9e404e6c59d286645b2465aacaf61108ebc12a3a",
    ... )
    >>> for d in files[:3]:
    ...     print(d.path)
    README.md
    LICENSE
    README.md

    """
    return list(gititer(path, exclude, branch, depth, since))


def gititer(
    path: str,
    exclude: Iterable[str] = None,
    branch: str = None,
    depth: int = None,
    since: str = None,
) -> Iterator[File]:
    """Iterate over Git commit history and yield diff blobs for each file."""
    try:
        repo = git.Repo(path)
    except Exception:  # pragma: no cover
        log.warning("not a Git repository: %s", path)
        raise StopIteration

    already_searched = set()
    for branch in _get_branches(repo, branch):
        log.info(f"switching to branch '{branch}'")
        prev_commit = None
        since_reached = False
        commits = repo.iter_commits(branch, max_count=depth)

        for curr_commit in commits:
            if curr_commit.hexsha == since:
                since_reached = True

            if since and since_reached:
                prev_commit = curr_commit
                continue

            diff_id = str(prev_commit) + str(curr_commit)
            if not prev_commit or diff_id in already_searched:
                prev_commit = curr_commit
                continue

            diff = prev_commit.diff(curr_commit, create_patch=True)
            already_searched.add(diff_id)
            yield from _diffiter(diff, prev_commit, branch, exclude)
            prev_commit = curr_commit

        diff = curr_commit.diff(git.NULL_TREE, create_patch=True)
        yield from _diffiter(diff, prev_commit, branch, exclude)


def _diffiter(
    diff: git.DiffIndex,
    commit: git.Commit,
    branch: git.Head,
    exclude: Iterable[str] = None,
) -> Iterator[File]:
    r"""Iterate over commit blobs and yield diffs for each file.

    Note
    ----
    Blobs with change type "D" (delete) and "R" (rename) are skipped.

    Examples
    --------
    Basic usage examples

    >>> repo = git.Repo()
    >>> b1 = b"\x87\x02\xc5\x00p\xf8\x84\x04\xd5bLJ\xec\xe69\xba\x85\xf1V\x81"
    >>> b2 = b"o\xac\x8e\xf5\x88\x8e/\xacM\x0cd^\xcd\xc0\xb1\x9dY$`\x80"
    >>> c1 = git.Commit(repo, b1)
    >>> c2 = git.Commit(repo, b2)
    >>> diff = c1.diff(c2, create_patch=True)
    >>> branch = _get_branches(repo, "master")[0]
    >>> len(list(_diffiter(diff, c1, branch, ["tests/*"])))
    6

    """
    exclude_set = DEFAULT_EXCLUDE_SET | set(exclude or [])
    for blob in diff:
        if blob.deleted_file or blob.renamed_file:  # pragma: no cover
            continue

        pdiff = blob.diff.decode("utf-8", errors="replace")
        fpath = blob.b_path if blob.b_path else blob.a_path

        if pdiff.startswith("Binary files"):  # pragma: no cover
            continue

        pattern = _match(fpath, exclude_set, recursive=True)
        if pattern:
            log.debug(f"skipping diff '{fpath}': '{pattern}'")
            continue

        yield File(
            path=fpath,
            content=pdiff,
            branch=branch.name,
            message=commit.message.strip(),
            author=f"{commit.author.name} <{commit.author.email}>",
            commit=commit.hexsha,
            date=commit.committed_datetime.isoformat(),
        )


def _get_branches(
    repo: git.Repo, branch: str = None
) -> Iterable[git.Commit]:  # pragma: no cover
    """Return a list of repository branches.

    Try to fetch branches from remote first.
    In case of failure, use `branch` as a fallback.
    Otherwise, use active repository branch.

    Examples
    --------
    Basic usage examples

    >>> repo = git.Repo()
    >>> len(_get_branches(repo)) > 1
    True
    >>> _get_branches(repo, "master")[0].name
    'FETCH_HEAD'

    """
    if repo.remotes:
        try:
            return repo.remotes.origin.fetch(branch)
        except git.GitCommandError as e:
            log.warning(f"fetching remote branches: {e}")
    else:
        log.warning("missing remotes")

    return [repo.branches[branch] if branch else repo.active_branch]


def _match(
    path: str, patterns: Iterable[str] = None, recursive: bool = False
) -> Optional[str]:
    """Match path against given glob patterns and return matched pattern if any.

    If `recursive` is set to True, check all parent directories as well.

    Note
    ----
    Return None if `patterns` is empty or not set.

    Examples
    --------
    Basic usage examples

    >>> _match("README.md", []) is None
    True
    >>> _match("README.md", ["*.txt", "*.yml"]) is None
    True
    >>> _match(".trufflehog.yml", ["*.txt", "*.yml"])
    '*.yml'
    >>> _match(".git/hooks/update.sample", [".git/*"]) is None
    True
    >>> _match(".git/hooks/update.sample", [".git/*"], recursive=True)
    '.git/*'

    """
    if not patterns:
        return None

    fpath = Path(path)
    paths = [fpath, *fpath.parents] if recursive else [fpath]
    for p in paths:
        for glob in patterns:
            if p.match(glob):
                return glob

    return None
