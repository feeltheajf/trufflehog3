import logging
import re
import sys
import yaml

from io import IOBase

from truffleHog3.types import Any, File, List, Regexes


__all__ = ("logger", "load", "dump", "compile", "match")


_LOGGER_NAME = "trufflehog"
_LOGGER_FMT = "[%(levelname).1s] %(message)s"


def logger(level: int = logging.ERROR) -> logging.Logger:
    logger = logging.Logger.manager.loggerDict.get(_LOGGER_NAME)
    if logger:
        logger.setLevel(level)
        return logger

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(_LOGGER_FMT))
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.addHandler(stream_handler)
    return logger


def load(file: File) -> Any:
    if not isinstance(file, IOBase):
        file = open(file)
    return yaml.safe_load(file)


def dump(obj: Any, file: File = None):
    if file is None:
        file = sys.stdout
    elif not isinstance(file, IOBase):
        file = open(file, "w")
    file.write(str(obj))


def compile(raw: List[str]) -> Regexes:
    return [re.compile(s) for s in raw]


def match(string: str, regexes: Regexes) -> str:
    for regex in regexes:
        if regex.search(string):
            return regex.pattern
    return None
