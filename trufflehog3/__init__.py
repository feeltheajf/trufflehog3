"""Main trufflehog3 module."""

import logging
import re

from pathlib import Path

from trufflehog3 import helper

__NAME__ = "trufflehog3"
__VERSION__ = "3.0.0"

HERE = Path(__file__).parent
STATIC_DIR = HERE / "static"
HTML_TEMPLATE_FILE = "report.html.j2"
TEXT_TEMPLATE_FILE = "report.text.j2"
DEFAULT_RULES_FILE = STATIC_DIR / "rules.yml"

DEFAULT_CONFIG_FILE = f".{__NAME__}.yml"
DEFAULT_EXCLUDE_SET = {DEFAULT_CONFIG_FILE, ".git"}

# Inline 'nosecret' comment implementation taken from semgrep:
# https://github.com/returntocorp/semgrep/blob/master/semgrep/semgrep/constants.py
NOSECRET_INLINE_RE = re.compile(
    # We're looking for items that look like this:
    # ' nosecret'
    # ' nosecret: example-pattern-id'
    # ' nosecret: pattern-id1,pattern-id2'
    # ' NOSECRET:pattern-id1, pattern-id2'
    #
    # * We do not want to capture the ': ' that follows 'nosecret'
    # * We do not care about the casing of 'nosecret'
    # * We want a comma-separated list of ids
    # * We want multi-language support, so we cannot strictly look for
    #   Python comments that begin with '# '
    #
    r" nosecret(?::[\s]?(?P<ids>([^,\s](?:[,\s]+)?)+))?",
    re.IGNORECASE,
)
IGNORE_NOSECRET = False

# global logger instance
log = helper.logger()


def set_debug(debug: bool):
    """Switch debug logging on and off.

    Examples
    --------
    Switch debug logging on and off

    >>> set_debug(True)
    >>> log.level
    10
    >>> set_debug(False)
    >>> log.level
    40

    """
    log.setLevel(logging.DEBUG if debug else logging.ERROR)
