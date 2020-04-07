import math
import os
import re
import string

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import wraps
from itertools import chain

from truffleHog3.lib import log, utils
from truffleHog3.types import List, Meta, MetaGen, Regexes, RawRules, Rules


__all__ = ("Regex", "Entropy")


_BASE64_CHARS = string.ascii_letters + string.digits + "+/="
_HEX_CHARS = string.hexdigits


class Engine(ABC):
    def __init__(self, skip: List[str] = None):
        self.regexes = skip

    @property
    def regexes(self) -> Regexes:
        return self._regexes

    @regexes.setter
    def regexes(self, skip: List[str]):
        self._regexes = utils.compile(skip or [])

    @abstractmethod
    def search(self, data: str) -> MetaGen:
        ...  # pragma: no cover

    def process(self, meta: Meta) -> MetaGen:
        issue = meta.copy()
        lines = issue.pop("data").splitlines()
        found = defaultdict(set)

        for i, line in enumerate(lines):
            for reason, match in self.search(line):
                if self.skip(match):
                    continue
                found[reason].add(line)

        return [
            dict(issue, reason=k, stringsFound=list(found[k])) for k in found
        ]

    def skip(self, match: str, line: str = "", path: str = "") -> bool:
        regex = utils.match(match, self.regexes)
        if regex:
            log.info(f"skipping string '{match}' matched by '{regex}'")
            return True

        return False


class Regex(Engine):
    def __init__(self, rules: RawRules, **kwargs):
        self.rules = rules
        super().__init__(**kwargs)

    @property
    def rules(self) -> Rules:
        return self._rules

    @rules.setter
    def rules(self, rules: RawRules):
        self._rules = {k: re.compile(v) for k, v in (rules or {}).items()}

    def search(self, line: str) -> MetaGen:
        for reason in self.rules:
            match = self.rules[reason].search(line)
            if not match:
                continue

            yield reason, match[0]


class Entropy(Engine):
    def __init__(self, min_length: int = 20, **kwargs):
        self.min_length = min_length
        super().__init__(**kwargs)

    def search(self, line: str) -> MetaGen:
        for word in line.split():
            for match in chain(
                self._entropy_match(word, _BASE64_CHARS, 4.5),
                self._entropy_match(word, _HEX_CHARS, 3.0),
            ):
                yield "High entropy", match

    def _entropy_match(
        self, word: str, alphabet: str, threshold: float
    ) -> List[str]:
        for match in _get_strings(word, alphabet, self.min_length):
            if _shannon_entropy(match, alphabet) > threshold:
                yield match


def _get_strings(word: str, alphabet: str, threshold: int) -> List[str]:
    count = 0
    letters = ""

    for char in word:
        if char in alphabet:
            letters += char
            count += 1
        else:
            if count > threshold:
                yield letters  # pragma: no cover

            letters = ""
            count = 0

    if count > threshold:
        yield letters


def _shannon_entropy(data: str, alphabet: str) -> float:
    if not data:
        return 0  # pragma: no cover

    entropy = 0
    for x in alphabet:
        p_x = float(data.count(x)) / len(data)

        if p_x > 0:
            entropy += -p_x * math.log(p_x, 2)

    return entropy
