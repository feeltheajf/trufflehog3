import os
import pytest
import sys

from glob import glob
from unittest.mock import patch

from truffleHog3 import cli
from truffleHog3.lib import utils
from truffleHog3.types import Config, Issues, Repo, Rules


config_json = "trufflehog.json"
config_yaml = "trufflehog.yaml"


def test_run_scan(repo: Repo, tmpdir: str):
    expected = os.path.join(tmpdir, "repo.json")
    path, _ = repo
    args = ["", path, "-f", "json", "--output", expected]
    with patch.object(sys, "argv", args):
        cli.run()

    assert len(utils.load(expected)) == 4


def test_run_scan_with_config(repo: Repo, datadir: str, tmpdir: str):
    expected = os.path.join(tmpdir, "repo.json")
    path, _ = repo
    args = [
        "",
        path,
        "-f",
        "json",
        "--output",
        expected,
        "-c",
        os.path.join(datadir, config_json),
    ]
    with patch.object(sys, "argv", args):
        cli.run()

    assert len(utils.load(expected)) == 3


def test_run_render(datadir: str, tmpdir: str):
    report_json = os.path.join(datadir, "report.json")
    original = os.path.join(datadir, "report.html")
    expected = os.path.join(tmpdir, "report.html")
    args = ["", "--render-html", report_json, "--output", expected]
    with patch.object(sys, "argv", args):
        cli.run()

    with open(original) as f1, open(expected) as f2:
        assert f1.read() == f2.read()


def count(path: str) -> int:
    return len(glob(f"{path}/**", recursive=True))


def test_copy_local_folder(datadir: str, tempdir: str):
    cli.copy(datadir, tempdir)
    assert count(datadir) == count(tempdir)


def test_copy_local_file(datadir: str, tempdir: str):
    original = os.path.join(datadir, config_json)
    expected = os.path.join(tempdir, config_json)
    cli.copy(original, expected)

    with open(original) as f1, open(expected) as f2:
        assert f1.read() == f2.read()


def test_copy_remote(remote: str, tempdir: str):
    cli.copy(remote, tempdir)
    assert count(tempdir) > 0
    assert os.path.exists(os.path.join(tempdir, "README.md"))


def test_scan(repo: Repo, rules: Rules):
    path, meta = repo

    config = Config()
    issues = cli.scan(path, config, rules)
    assert len(issues) == 4

    config = Config(since_commit=meta["private_key_commit"])
    issues = cli.scan(path, config, rules)
    assert len(issues) == 2

    config = Config(max_depth=5)
    issues = cli.scan(path, config, rules)
    assert len(issues) == 2

    config = Config(no_history=True)
    issues = cli.scan(path, config, rules)
    assert len(issues) == 1

    config = Config(no_current=True)
    issues = cli.scan(path, config, rules)
    assert len(issues) == 3

    config = Config(no_entropy=True)
    issues = cli.scan(path, config, rules)
    assert len(issues) == 2

    config = Config(no_regex=True)
    issues = cli.scan(path, config, rules)
    assert len(issues) == 2


def test_scan_commit(repo: Repo, rules: Rules):
    path, meta = repo
    config = Config()
    issues = cli.scan(path, config, rules)

    commit = meta["high_entropy_commit"]
    filtered = [i for i in issues if i["commitHash"] == commit]
    assert len(filtered) == 1
    issue = filtered[0]
    assert issue["commit"].strip() == issue["reason"] == "High entropy"

    commit = meta["private_key_commit"]
    filtered = [i for i in issues if i["commitHash"] == commit]
    assert len(filtered) == 1
    issue = filtered[0]
    assert issue["commit"].strip() == issue["reason"] == "RSA private key"


def test_write(issues: Issues, datadir: str, tempdir: str):
    for format in "text", "json", "yaml", "html":
        report_name = f"report.{format}"
        original = os.path.join(datadir, report_name)
        expected = os.path.join(tempdir, report_name)
        cli.write(issues, expected, format)

        with open(original) as f1, open(expected) as f2:
            assert f1.read() == f2.read()

    with pytest.raises(NotImplementedError):
        cli.write(None, None, "non-supported")


def test_load_config(config: Config, datadir: str, tempdir: str):
    args = ["", "."]
    with patch.object(sys, "argv", args):
        config1 = cli._load_config(os.path.join(datadir, config_json))
        config2 = cli._load_config(os.path.join(datadir, config_yaml))
        assert config1 == config2 == config

        tmp = os.path.join(tempdir, "tmp.yaml")
        open(tmp, "w").close()
        assert cli._load_config(tmp) == Config()


def test_load_config_with_args(config: Config, datadir: str):
    branch = "2.0"
    since_commit = "123"
    skip_strings = [".*test_secret.*", "test_password = .*"]
    skip_paths = []
    max_depth = 10
    args = [
        "",
        ".",
        "--branch",
        branch,
        "--since-commit",
        since_commit,
        "--skip-strings",
        *skip_strings,
        "--skip-paths",
        *skip_paths,
        "--max-depth",
        str(max_depth),
        "--no-regex",
    ]
    config.update(
        branch=branch,
        since_commit=since_commit,
        skip_strings=skip_strings,
        skip_paths=skip_paths,
        max_depth=max_depth,
        no_regex=True,
    )
    config_path = os.path.join(datadir, config_yaml)
    with patch.object(sys, "argv", args):
        assert cli._load_config(config_path) == config


def test_search_config(config: Config, datadir: str, tempdir: str):
    args = ["", "."]
    with patch.object(sys, "argv", args):
        assert cli._search_config(datadir) == config
        assert cli._search_config(tempdir) == Config()


def test_search_config_with_args(config: Config, datadir: str):
    max_depth = 1000
    args = ["", ".", "--max-depth", str(max_depth)]
    config.update(max_depth=max_depth)
    with patch.object(sys, "argv", args):
        assert cli._search_config(datadir) == config
