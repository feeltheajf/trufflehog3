"""Helper functions."""

import logging
import math

from typing import List, Dict


class Color:
    """Supported ANSI colors."""

    BLACK = "\x1b[30m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"
    WHITE = "\x1b[37m"
    GRAY = "\x1b[90m"

    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    UNDERLINE = "\x1b[4m"


def colored(s: str, color: str = Color.GREEN) -> str:
    """Return ANSI-colored string."""
    return f"{color}{s}{Color.RESET}"


def logger(level: int = logging.ERROR, name="secret") -> logging.Logger:
    """Initialize and return named logger singleton.

    Note
    ----
    Level is not changed upon subsequent calls. Use log.setLevel().

    Examples
    --------
    >>> log1 = logger(level=logging.DEBUG, name="debug")
    >>> log2 = logger(level=logging.ERROR, name="debug")
    >>> log3 = logger(level=logging.ERROR, name="error")
    >>> log1 == log2
    True
    >>> log2.level  # log2 still has DEBUG level
    10
    >>> log1 == log3
    False
    >>> log2.setLevel(logging.ERROR)  # log1 and log2 now have ERROR level
    >>> log2.level
    40

    """
    log = logging.Logger.manager.loggerDict.get(name)  # type: ignore
    if log:
        return log

    logging.addLevelName(logging.DEBUG, colored("[D]", Color.CYAN))
    logging.addLevelName(logging.INFO, colored("[I]", Color.GREEN))
    logging.addLevelName(logging.WARNING, colored("[W]", Color.YELLOW))
    logging.addLevelName(logging.ERROR, colored("[E]", Color.RED))
    logging.addLevelName(logging.FATAL, colored("[F]", Color.BOLD + Color.RED))

    log = logging.getLogger(name)
    log.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt=colored("%I:%M%p", Color.GRAY),
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log


def get_lines(s: str, line: int, context: int = 0) -> Dict[int, str]:
    r"""Extract lines with context from the given string.

    Return dict with lines range and the extracted lines.

    Note
    ----
    It is supposed that `line` parameter is 1-indexed.

    Examples
    --------
    Basic usage examples

    >>> s = "1\n2\n3\n4\n5"
    >>> get_lines(s, 3)
    {'3': '3'}
    >>> get_lines(s, 1, 2)
    {'1': '1', '2': '2', '3': '3'}
    >>> get_lines(s, 5, 2)
    {'3': '3', '4': '4', '5': '5'}
    >>> get_lines(s, 3, 10)
    {'1': '1', '2': '2', '3': '3', '4': '4', '5': '5'}

    """
    lines = s.splitlines()
    lower = max(0, line - context - 1)
    upper = min(len(lines), line + context)

    return {f"{i + 1}": lines[i] for i in range(lower, upper)}


def get_strings(s: str, alphabet: str, minlen: int) -> List[str]:
    """Extract substrings of given alphabet from the string.

    Examples
    --------
    Basic usage examples

    >>> get_strings("testing get_strings", "abcdefghijklmnopqrstuvwxyz", 5)
    ['testing', 'strings']
    >>> get_strings("something about deadbeef", "0123456789abcdef", 5)
    ['deadbeef']

    """
    chars = ""
    count = 0

    sub = []
    for char in s:
        if char in alphabet:
            chars += char
            count += 1
        else:
            if count >= minlen:
                sub.append(chars)

            chars = ""
            count = 0

    if count > minlen:
        sub.append(chars)

    return sub


def shannon_entropy(s: str, alphabet: str) -> float:
    """Calculate Shannon entropy for given string of alphabet characters.

    Note
    ----
    Return zero for empty string.

    Examples
    --------
    Basic usage examples

    >>> shannon_entropy("", "abcdefghijklmnopqrstuvwxyz")
    0.0
    >>> shannon_entropy("abcd", "abcdefghijklmnopqrstuvwxyz")
    2.0
    >>> shannon_entropy("1234abcd", "0123456789abcdef")
    3.0

    """
    entropy = 0.0
    if not s:
        return entropy

    for x in alphabet:
        px = float(s.count(x)) / len(s)
        if px > 0:
            entropy += -px * math.log(px, 2)

    return entropy
