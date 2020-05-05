import pytest

from truffleHog3.lib.source import Simple, Git
from truffleHog3.types import Repo


skip = [".*.py"]


def test_simple(repo: Repo):
    path, _ = repo
    files = list(Simple(path))
    assert len(files) == 12

    files = list(Simple(path, skip))
    assert len(files) == 1


def test_git(repo: Repo):
    path, meta = repo
    diffs = list(Git(path))
    assert len(diffs) == 24

    diffs = list(Git(path, skip=skip))
    assert len(diffs) == 13

    diffs = list(Git(path, branch="master"))
    assert len(diffs) == 24

    with pytest.raises(IndexError):
        list(Git(path, branch="non-existent"))

    diffs = list(Git(path, since_commit=meta["private_key_commit"]))
    assert len(diffs) == 10

    diffs = list(Git(path, max_depth=7))
    assert len(diffs) == 12
