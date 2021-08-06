"""Render reports in all supported formats."""

import jinja2
import json as jsonlib

from collections import defaultdict
from typing import Any, Dict, Iterable, Tuple

from trufflehog3 import STATIC_DIR, HTML_TEMPLATE_FILE, TEXT_TEMPLATE_FILE
from trufflehog3.helper import Color
from trufflehog3.models import Issue, Severity, Pattern  # noqa: F401 doctest


def text(issues: Iterable[Issue]) -> str:
    """Render issues as text.

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
    >>> s = text([issue])

    """
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(STATIC_DIR),
        autoescape=False,  # no need to escape anything for plaintext format
        auto_reload=False,
    )
    template = environment.get_template(TEXT_TEMPLATE_FILE)
    return template.render(issues=sorted(issues, key=_sort_keys), color=Color)


# TODO switch to SARIF-compatible output?
def json(issues: Iterable[Issue]) -> str:
    """Render issues as JSON.

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
    >>> s = json([issue])

    """
    return jsonlib.dumps([i.asdict() for i in issues], indent=2, default=str)


def html(issues: Iterable[Issue]) -> str:
    """Render issues as HTML.

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
    >>> s = html([issue])

    """
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(STATIC_DIR),
        autoescape=True,
        auto_reload=False,
    )
    template = environment.get_template(HTML_TEMPLATE_FILE)
    return template.render(**_prepare_report(issues))


def _prepare_report(issues: Iterable[Issue]) -> Dict[str, Any]:
    """Split issues and rules into structs handy for HTML report building."""
    totals = defaultdict(lambda: 0)
    report = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for issue in sorted(issues, key=_sort_keys):
        totals[issue.rule] += 1
        report[issue.rule][issue.path][issue.commit].append(issue)

    return dict(totals=totals, report=report)


def _sort_keys(issue) -> Tuple[Severity, str, str]:
    """Return rule severity, message and issue path for sorting."""
    return (-issue.rule.severity, issue.rule.message.lower(), issue.path)
