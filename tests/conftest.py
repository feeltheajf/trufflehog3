import os
import pytest

from subprocess import check_output
from tempfile import TemporaryDirectory

from truffleHog3.cli import _RULES
from truffleHog3.lib import utils
from truffleHog3.types import Config, Issue, Issues, Meta, Repo, Rules


@pytest.fixture
def rootdir() -> str:
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def datadir(rootdir: str) -> str:
    return os.path.join(rootdir, "tests/data")


@pytest.fixture
def tempdir() -> str:
    t = TemporaryDirectory(dir="/tmp")
    yield t.name
    t.cleanup()


@pytest.fixture
def repo(tempdir: str) -> Repo:
    print(check_output(["./scripts/makerepo", tempdir]).decode())
    meta = utils.load(os.path.join(tempdir, "meta.yaml"))
    return os.path.join(tempdir, "repo"), meta


@pytest.fixture
def remote() -> str:
    return "https://github.com/feeltheajf/truffleHog3"


@pytest.fixture
def rules() -> Rules:
    return utils.load(_RULES)


@pytest.fixture
def config() -> Config:
    return Config(
        branch="master",
        since_commit="d15627104d07846ac2914a976e8e347a663bbd9b",
        skip_strings=["qweqwe"],
        skip_paths=[".*key.json"],
        max_depth=10000,
        no_regex=False,
        no_entropy=False,
        no_history=False,
        no_current=True,
    )


@pytest.fixture()
def issues(issue_entropy: Issue, issue_regex: Issue) -> Issues:
    return [issue_entropy, issue_regex]


@pytest.fixture
def issue_entropy() -> Issue:
    return {
        "date": "2020-04-03 11:50:58",
        "path": "/high_entropy.py",
        "branch": "master",
        "commit": "Adds no secret values at all",
        "commitHash": "d15627104d07846ac2914a976e8e347a663bbd9b",
        "reason": "High entropy",
        "stringsFound": ["f18e9874c95a664e7175e8a7991ff9e5e1f91a473665f5"],
    }


@pytest.fixture
def issue_regex() -> Issue:
    return {
        "date": "2020-04-03 11:50:59",
        "path": "/password_in_url.go",
        "branch": None,
        "commit": None,
        "commitHash": None,
        "reason": "Password in URL",
        "stringsFound": [
            "server_url = 'https://username:password@localhost:1234'"
        ],
    }


@pytest.fixture
def meta_entropy() -> Meta:
    return {
        "date": "2020-04-03 11:50:58",
        "path": "/high_entropy.py",
        "branch": "master",
        "commit": "Adds no secret values at all",
        "commitHash": "d15627104d07846ac2914a976e8e347a663bbd9b",
        "data": "\n".join(
            (
                "line1",
                "line2",
                "f18e9874c95a664e7175e8a7991ff9e5e1f91a473665f5",
            )
        ),
    }


@pytest.fixture
def meta_regex() -> Meta:
    return {
        "date": "2020-04-03 11:50:59",
        "path": "/password_in_url.go",
        "branch": None,
        "commit": None,
        "commitHash": None,
        "data": "\n".join(
            (
                "sample code before secret line",
                "server_url = 'https://username:password@localhost:1234'",
                "sample code after secret line",
            )
        ),
    }
