"""Supported search algorithms."""

from typing import Iterable, Iterator, Optional, Union

from trufflehog3 import NOSECRET_INLINE_RE, IGNORE_NOSECRET
from trufflehog3 import helper, log, source
from trufflehog3.models import Entropy, Exclude, File, Issue, Pattern

MATCH_ALL_RULE_IDS = "*"


def search(
    file: File,
    rules: Iterable[Union[Entropy, Pattern]],
    exclude: Iterable[Exclude] = None,
    ignore_nosecret: bool = IGNORE_NOSECRET,
    context: int = 0,
) -> Iterable[Issue]:
    """Return issues found using provided rules.

    Examples
    --------
    Entropy-based search

    >>> rule = Entropy()
    >>> file = File(
    ...     path="/path/to/code.py",
    ...     content="password = 'abcdefghijklmnopqrstuvwxyz'",
    ... )
    >>> for issue in search(file, [rule]):
    ...     print(issue.secret)
    abcdefghijklmnopqrstuvwxyz

    Pattern-based search

    >>> rule = Pattern(
    ...     id="bad-password-letmein",
    ...     message="Bad Password 'letmein'",
    ...     pattern="letmein",
    ...     severity="high",
    ... )
    >>> file = File(
    ...     path="/path/to/code.py",
    ...     content="password = 'letmein'",
    ... )
    >>> for issue in search(file, [rule]):
    ...     print(issue.secret)
    letmein

    With exclude

    >>> exc = Exclude(message="Not a secret", paths=["*.py"])
    >>> len(search(file, [rule], exclude=[exc]))
    0

    With inline exclude

    >>> file = File(
    ...     path="/path/to/code.py",
    ...     content="password = 'letmein'  # nosecret",
    ... )
    >>> len(search(file, [rule]))
    0

    >>> file = File(
    ...     path="/path/to/code.py",
    ...     content="password = 'letmein'  # nosecret: bad-password-letmein",
    ... )
    >>> len(search(file, [rule]))
    0

    """
    return list(searchiter(file, rules, exclude, ignore_nosecret, context))


def searchiter(
    file: File,
    rules: Iterable[Union[Entropy, Pattern]],
    exclude: Iterable[Exclude] = None,
    ignore_nosecret: bool = IGNORE_NOSECRET,
    context: int = 0,
) -> Iterator[Issue]:
    """Yield issues found using provided rules."""
    content = file.read()

    for i, line in enumerate(content.splitlines()):
        line_number = i + 1
        exclude_ids = [] if ignore_nosecret else _parse_nosecret(line)
        location = f"{file.path}:{line_number}"

        if MATCH_ALL_RULE_IDS in exclude_ids:
            log.info(f"nosecret: skipping {location}")
            continue

        for rule in rules:
            if rule.id.lower() in exclude_ids:
                log.info(f"nosecret: skipping {rule.id} in {location}")
                continue

            for match in rule.findall(line):
                issue = Issue(
                    rule=rule,
                    path=file.path,
                    line=str(line_number),
                    secret=match,
                    context=helper.get_lines(content, line_number, context),
                    branch=file.branch,
                    message=file.message,
                    author=file.author,
                    commit=file.commit,
                    date=file.date,
                )

                if _match(issue, exclude):
                    log.info(f"exclude: skipping {rule.id} in {location}")
                    continue

                yield issue


def _parse_nosecret(s: str) -> Iterable[str]:
    """Parse `nosecret` comment from string and return excluded rule IDs.

    Note
    ----
    Return `'*'` wildcard if no rule IDs were set in the comment.

    Examples
    --------
    Basic usage examples

    >>> _parse_nosecret("token = get_token()  # not secret")
    []
    >>> _parse_nosecret("token = get_token()  # nosecret")
    ['*']
    >>> _parse_nosecret("token = get_token()  # nosecret: rule-id")
    ['rule-id']
    >>> sorted(_parse_nosecret("token := getToken() // nosecret: id1,id2"))
    ['id1', 'id2']
    >>> sorted(_parse_nosecret("token := getToken() // NOSECRET:id1, id2"))
    ['id1', 'id2']

    """
    match = NOSECRET_INLINE_RE.search(s)
    if match is None:
        return []

    ids = match.groupdict()["ids"]
    if ids is None:
        return [MATCH_ALL_RULE_IDS]

    return list(set(id.strip().lower() for id in ids.split(",") if id.strip()))


def _match(
    issue: Issue, exclude: Iterable[Exclude] = None
) -> Optional[Exclude]:
    r"""Match issue against given exclude rules and return matched rule if any.

    Note
    ----
    Return None if `exclude` is not set.

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
    >>> erule = Exclude(message="Not a secret", id="bad-password-notpass")
    >>> _match(issue, [erule]) is None
    True
    >>> erule = Exclude(message="Not a secret", id="bad-password-letmein")
    >>> _match(issue, [erule]).message
    'Not a secret'
    >>> erule = Exclude(message="Not a secret", paths=["/path/to/*"])
    >>> _match(issue, [erule]).message
    'Not a secret'
    >>> erule = Exclude(message="Not a secret", pattern="letmein")
    >>> _match(issue, [erule]).message
    'Not a secret'
    >>> erule = Exclude(message="Not a secret", pattern="(?i)letmein")
    >>> _match(issue, [erule]).message
    'Not a secret'

    """
    if exclude is None:
        return None

    for exc in exclude:
        if exc.paths:
            path_matched = source._match(issue.path, exc.paths, recursive=True)
        else:
            path_matched = True

        if path_matched and (
            not any((exc.id, exc.pattern))
            or (
                exc.id == issue.rule.id
                or exc.findall(issue.context[issue.line])
            )
        ):
            return exc

    return None
