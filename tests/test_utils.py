import logging
import os

from truffleHog3.lib import utils
from truffleHog3.types import Config


def test_logger():
    log1 = utils.logger(level=logging.DEBUG)
    log2 = utils.logger(level=logging.ERROR)
    assert log1 == log2


def test_load(datadir: str, config: Config):
    assert utils.load(os.path.join(datadir, "trufflehog.json")) == config
    assert utils.load(os.path.join(datadir, "trufflehog.yaml")) == config


def test_dump(capsys, tempdir: str):
    data = "1234567"

    utils.dump(data)
    captured = capsys.readouterr()
    assert captured.out.strip() == data
    assert captured.err.strip() == ""

    path = os.path.join(tempdir, "file.txt")
    utils.dump(data, path)
    with open(path) as f:
        assert f.read() == data


def test_match():
    string1 = "/some/very/long/path/to/code.py"
    string2 = "/some/other/path/for/another.py"
    string3 = "/some/important/path/to/code.go"
    regexes = utils.compile(["/long/.*", ".*.py"])
    assert utils.match(string1, regexes) == regexes[0].pattern
    assert utils.match(string2, regexes) == regexes[1].pattern
    assert utils.match(string3, regexes) is None
