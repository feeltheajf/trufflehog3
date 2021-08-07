"""Helper classes for passing data around."""

import attr
import re
import string
import uuid

from abc import ABC, abstractmethod
from datetime import datetime
from enum import auto, Enum, EnumMeta
from pathlib import Path
from typing import Any, Dict, List, Optional

from trufflehog3 import log, helper, IGNORE_NOSECRET

_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")

BASE64_CHARS = string.ascii_letters + string.digits + "+/="
BASE64_LIMIT = 4.5
HEX_CHARS = string.hexdigits
HEX_LIMIT = 3.0


class CaseInsensitiveEnumMeta(EnumMeta):
    """Meta class for case-insensitive enum."""

    def __call__(self, value, *args, **kwargs):
        """Search enum names instead of values when value is string."""
        if isinstance(value, str):
            return self.__getitem__(value)

        return super().__call__(value, *args, **kwargs)

    def __getitem__(self, name):
        """Make get item operation case-insensitive."""
        return super().__getitem__(name.upper())


class Severity(Enum, metaclass=CaseInsensitiveEnumMeta):
    """Issue severity based on match confidence and other factors."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()

    def __lt__(self, other):  # pragma: no cover
        """Severity comparison is used for sorting issues."""
        return self.value < other.value

    def __le__(self, other):
        """Severity equality is used for sorting issues."""
        return self.value <= other.value

    def __str__(self):
        """Override string method to return enum name."""
        return self.name

    def __neg__(self):
        """Override negation method to use enum value."""
        return -self.value


class Format(Enum, metaclass=CaseInsensitiveEnumMeta):
    """Supported output formats."""

    TEXT = auto()
    JSON = auto()
    HTML = auto()

    def __str__(self):  # pragma: no cover
        """Override string method to return enum name."""
        return self.name


@attr.s
class Model:
    """Model is a base class for all models definitions."""

    def asdict(self):
        """Convert model to dictionary."""
        return attr.asdict(
            self, filter=lambda attr, _: not attr.name.startswith("_")
        )


@attr.s(frozen=True)
class File(Model):
    """File is a basic wrapper with Git metadata support.

    Attributes
    ----------
    path (str)
    : File path.

    branch (str, optional)
    : Git commit branch.

    message (str, optional)
    : Git commit message.

    author (str, optional)
    : Git commit author as `name <email>`.

    commit (str, optional)
    : Git commit hash.

    date (datetime.datetime, optional)
    : Git commit timestamp.

    Args
    ----
    content (str, optional)
    : File content.

    Examples
    --------
    Basic usage examples

    >>> f = File("tests/data/test_file.txt")
    >>> f.read()
    'Test'
    >>> f = File("nosuchpath/test_file.txt", content="Test")
    >>> f.read()
    'Test'

    """

    path: str = attr.ib()
    branch: Optional[str] = attr.ib(None)
    message: Optional[str] = attr.ib(None)
    commit: Optional[str] = attr.ib(None)
    author: Optional[str] = attr.ib(None)
    date: Optional[datetime] = attr.ib(None)
    _content: Optional[str] = attr.ib(None)
    _real: Optional[str] = attr.ib(None)

    def read(self) -> str:
        """Return the given content or read file from path."""
        if self._content is not None:
            return self._content

        try:
            return Path(self._real or self.path).read_text()
        except Exception as e:  # pragma: no cover
            log.warning(f"skipping file '{self.path}': {e}")
            return ""


@attr.s
class Rule(Model, ABC):
    """Rule is a base class for rules definitions."""

    def __eq__(self, other):  # pragma: no cover
        """Override equality check to use rule IDs."""
        return (type(self) == type(other)) and (self.id == other.id)

    def __hash__(self):  # pragma: no cover
        """Override hash value to use rule ID."""
        return hash(self.id)

    @abstractmethod
    def findall(self, s: str) -> List[str]:  # pragma: no cover
        """Find all substrings matching rule."""
        ...

    @staticmethod
    def fromany(x: Any) -> Any:
        """Convert any object to rule."""
        return x if issubclass(type(x), Rule) else Rule.fromdict(x)

    @staticmethod
    def fromdict(x: Dict[str, Any]) -> Any:
        """Convert dict to rule subclass."""
        try:
            return Pattern(**x)
        except Exception:
            return Entropy(**x)

    @staticmethod
    def fromargs(**x: Any) -> Any:
        """Convert args to rule subclass."""
        return Rule.fromdict(x)


@attr.s(frozen=True)
class Entropy(Rule):
    """Entropy is used for detecting high entropy strings.

    Attributes
    ----------
    id (str)
    : Rule ID, should be unique.

    message (str)
    : Short explanation of what is matched by the rule.

    severity (Severity)
    : Severity of issues detected by the rule.

    Args
    ----
    alphabet (str, optional)
    : Alphabet to search characters from.

    threshold (float, optional)
    : Shannon entropy threshold.

    minlen (int, optional)
    : Minimum match length.

    Examples
    --------
    There are two ways to customize high entropy check.
    The easiest one is to set custom minimum length for matched strings.
    The other way is to set custom alphabets and/or thresholds for them.

    >>> BASE32_CHARS = string.ascii_letters + "234567="
    >>> rule = Entropy(
    ...     alphabet=BASE32_CHARS,
    ...     threshold=3.75,
    ...     minlen=10,
    ... )
    >>> rule.findall("password = 'irtksdajfhaeu356'")
    ['irtksdajfhaeu356']

    """

    id: str = attr.ib("high-entropy")
    message: str = attr.ib("High Entropy")
    severity: Optional[Severity] = attr.ib(Severity.MEDIUM, converter=Severity)
    _alphabet: Optional[str] = attr.ib(BASE64_CHARS)
    _threshold: Optional[float] = attr.ib(BASE64_LIMIT)
    _minlen: Optional[int] = attr.ib(20)
    _uuid: uuid.UUID = attr.ib(init=False)

    @_uuid.default
    def _uuid_default(self):
        return uuid.uuid3(_NAMESPACE, self.id)

    def findall(self, s: str) -> List[str]:
        """Find high entropy substring occurrences in the string.

        Examples
        --------
        Basic usage examples. The first match here is from base64 alphabet
        and the second one exceeded defined hexadecimal entropy threshold.

        >>> rule = Entropy()
        >>> rule.findall("token = 'abcdefghijklmnopqrstuvwxyz'")
        ['abcdefghijklmnopqrstuvwxyz']

        >>> rule = Entropy(
        ...     alphabet=HEX_CHARS,
        ...     threshold=HEX_LIMIT,
        ...     minlen=10,
        ... )
        >>> rule.findall("password = '1234567890'")
        ['1234567890']

        """
        matched = []

        for word in helper.get_strings(s, self._alphabet, self._minlen):
            if helper.shannon_entropy(word, self._alphabet) > self._threshold:
                matched.append(word)

        return matched


@attr.s(frozen=True)
class Pattern(Rule):
    """Pattern holds all neccessary metadata for pattern-based rule definition.

    Attributes
    ----------
    id (str)
    : Rule ID, should be unique.

    message (str)
    : Short explanation of what is matched by the rule.

    pattern (Pattern)
    : Python `re.Pattern` to search for.

    severity (Severity, optional)
    : Severity of issues detected by the rule.

    Examples
    --------
    Match `letmein` string everywhere

    >>> rule = Pattern(
    ...     id="bad-password-letmein",
    ...     message="Bad Password 'letmein'",
    ...     pattern="letmein",
    ...     severity="high",
    ... )

    Match `letmein` Python `re.Pattern`, case-insensitive

    >>> rule = Pattern(
    ...     id="bad-password-letmein",
    ...     message="Bad Password 'letmein'",
    ...     pattern="(?i)letmein",
    ...     severity="high",
    ... )

    """

    id: str = attr.ib()
    message: str = attr.ib()
    pattern: str = attr.ib()
    severity: Optional[Severity] = attr.ib(Severity.MEDIUM, converter=Severity)
    _uuid: uuid.UUID = attr.ib(init=False)
    _pattern: re.Pattern = attr.ib(init=False)

    @_uuid.default
    def _uuid_default(self):
        return uuid.uuid3(_NAMESPACE, self.id)

    @_pattern.default
    def _pattern_default(self):
        return re.compile(self.pattern)

    def findall(self, s: str) -> List[str]:
        """Find pattern occurrences in the string.

        Examples
        --------
        Basic usage examples

        >>> rule = Pattern(
        ...     id="bad-password-letmein",
        ...     message="Bad Password 'letmein'",
        ...     pattern="letmein",
        ...     severity="high",
        ... )
        >>> rule.findall("password = 'letmein'")
        ['letmein']

        """
        return [m.group() for m in self._pattern.finditer(s)]


@attr.s(frozen=True)
class Exclude(Rule):
    """Exclude is used for referencing rules in configuration exclude list.

    Attributes
    ----------
    message (str)
    : Short explanation of what is matched by the rule.

    id (str, optional)
    : Rule ID, should be unique.

    pattern (Pattern, optional)
    : Python `re.Pattern` to search for.

    paths (List[str], optional)
    : File paths for rule to be applied on, defaults to everywhere.
      Each item should be a glob pattern as recognized by `pathlib.Path.match`.

    Note
    ----
    Only one of `id`, `pattern` must be set.

    If `paths` is set, exclude will only be applied on the specified paths.

    Examples
    --------
    Skip rule by its ID, but only in YAML files

    >>> rule = Exclude(
    ...     id="bad-password.letmein",
    ...     message="Not Password 'letmein'",
    ...     paths=["*.yaml", "*.yml"],
    ... )

    Skip lines containing `letmein` string

    >>> rule = Exclude(
    ...     message="Not Password 'letmein'",
    ...     pattern="letmein",
    ... )

    Skip lines containing `letmein` Python `re.Pattern`, case-insensitive

    >>> rule = Exclude(
    ...     message="Not Password 'letmein'",
    ...     pattern="(?i)letmein",
    ... )

    """

    message: str = attr.ib()
    id: Optional[str] = attr.ib(None)
    pattern: Optional[re.Pattern] = attr.ib(
        None, converter=lambda x: re.compile(x) if x else None
    )
    paths: Optional[List[str]] = attr.ib(None)

    def findall(self, s: str) -> List[str]:
        """Find pattern occurrences in the string."""
        return (
            [m.group() for m in self.pattern.finditer(s)]
            if self.pattern
            else []
        )

    @staticmethod
    def fromany(x: Any) -> Any:
        """Convert any object to exclude rule."""
        return x if isinstance(x, Exclude) else Exclude.fromdict(x)

    @staticmethod
    def fromdict(x: Dict[str, Any]) -> Any:
        """Convert dict to exclude rule."""
        return Exclude(**x)


class Context(dict):
    """Dumb workaround for dict being unhashable by default.

    Note
    ----
    It is only intended to be used as `context` property for `models.Issue`,
    which uses its own hashing algorithm.

    """

    __slots__ = ()

    def __eq__(self, other):  # pragma: no cover
        """Return false."""
        return False

    def __hash__(self):
        """Return zero."""
        return 0


@attr.s(frozen=True)
class Issue(Model):
    r"""Issue holds finding metadata.

    Attributes
    ----------
    rule (Rule):
    : Rule the issue was detected by.

    path (str):
    : File path.

    line (int):
    : Line number of the matched line.
      For Git history this is the line number in diff blob, not the real one.

    secret (str):
    : String matched by the rule.

    context (str):
    : Code lines containing secret matched by the rule.

    id (str, optional):
    : Issue ID. Generated automatically from `path`, `secret` and rule UUID.

    branch (str, optional)
    : Git commit branch.

    message (str, optional)
    : Git commit message.

    author (str, optional)
    : Git commit author as `name <email>`.

    commit (str, optional)
    : Git commit hash.

    date (datetime.datetime, optional)
    : Git commit timestamp.

    Examples
    --------
    Basic usage examples

    >>> rule = Pattern(
    ...     id="bad-password-letmein",
    ...     message="Bad Password 'letmein'",
    ...     pattern="letmein",
    ...     severity="high",
    ... )
    >>> issue = Issue(
    ...     rule=rule,
    ...     path="/path/to/code.py",
    ...     line="10",
    ...     secret="letmein",
    ...     context={
    ...         "9":  "username = 'admin'",
    ...         "10": "password = 'letmein'",
    ...         "11": "response = authorize(username, password)",
    ...     },
    ... )
    >>> issue.id
    UUID('bfd860e4-2002-30dd-a1b1-24e29083c7d5')

    """

    rule: Rule = attr.ib(converter=Rule.fromany)
    path: str = attr.ib()
    line: str = attr.ib()
    secret: str = attr.ib()
    context: Context = attr.ib(converter=Context)
    id: Optional[uuid.UUID] = attr.ib()
    branch: Optional[str] = attr.ib(None)
    message: Optional[str] = attr.ib(None)
    author: Optional[str] = attr.ib(None)
    commit: Optional[str] = attr.ib(None)
    date: Optional[datetime] = attr.ib(None)

    @id.default
    def _id_default(self):
        fields = ":".join((self.path, self.secret))
        return uuid.uuid3(self.rule._uuid, fields)

    def __eq__(self, other):  # pragma: no cover
        """Override equality check to use issue IDs."""
        return (type(self) == type(other)) and (self.id == other.id)

    def __hash__(self):  # pragma: no cover
        """Override hash check to use issue ID."""
        return self.id.int

    @property
    def multiline(self) -> bool:
        """Return true if context contains multiple lines."""
        return len(self.lines) > 1

    @property
    def lines(self) -> List[int]:
        """Return context keys containing line numbers."""
        return list(self.context)

    @property
    def line_start(self) -> int:  # pragma: no cover
        """Return first context line number."""
        return self.lines[0]

    @property
    def line_end(self) -> int:
        """Return last context line number."""
        return self.lines[-1]


@attr.s
class Config(Model):
    """Config holds all configuration."""

    # search configuration
    exclude: Optional[List[Exclude]] = attr.ib(
        None,
        converter=lambda x: [Exclude.fromany(r) for r in x] if x else None,
    )
    severity: Optional[Severity] = attr.ib(Severity.LOW, converter=Severity)
    ignore_nosecret: Optional[bool] = attr.ib(IGNORE_NOSECRET)
    no_entropy: Optional[bool] = attr.ib(False)
    no_pattern: Optional[bool] = attr.ib(False)

    # source configuration
    branch: Optional[str] = attr.ib(None)
    depth: Optional[int] = attr.ib(10000)
    since: Optional[str] = attr.ib(None)
    no_current: Optional[bool] = attr.ib(False)
    no_history: Optional[bool] = attr.ib(False)

    # render configuration
    context: Optional[int] = attr.ib(0)
