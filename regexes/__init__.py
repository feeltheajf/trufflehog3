"""truffleHog rules handling."""

import json
import os
import re


def load(file):
    if not os.path.exists(file):
        raise IOError(f"File does not exist: {file}")

    with open(file, "r") as f:
        rules = json.load(f)

    rules = {name: re.compile(rule) for name, rule in rules.items()}
    return rules


DEFAULT = load(os.path.join(os.path.dirname(__file__), "regexes.json"))
