import jinja2
import json
import os
import yaml

from abc import ABC, abstractmethod
from collections import defaultdict

from truffleHog3.types import Issue, Issues, Meta


__all__ = ("TEXT", "JSON", "YAML", "HTML")


class _colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


_TEXT_TEMPLATE = """~~~~~~~~~~~~~~~~~~~~~%s
Reason: {reason}
Path:   {path}
Branch: {branch}
Commit: {commit}
Hash:   {commitHash}
%s{strings}
~~~~~~~~~~~~~~~~~~~~~"""

_HTML_STATIC_FOLDER = os.path.dirname(os.path.dirname(__file__))
_HTML_TEMPLATE = "report.j2"


class Engine(ABC):
    def __init__(self, issues: Issues):
        self.issues = issues

    @abstractmethod
    def __str__(self):
        ...  # pragma: no cover


class TEXT(Engine):
    def __init__(self, issues: Issues):
        self.load_template()
        super().__init__(issues)

    def __str__(self):
        return "\n".join(self._render(i) for i in self.issues)

    def _render(self, issue: Issue) -> str:
        strings = "\n".join(issue["stringsFound"])
        return self.template.format(**issue, strings=strings)

    def load_template(self):
        self.template = _TEXT_TEMPLATE % (_colors.OKGREEN, _colors.ENDC)


class JSON(Engine):
    def __str__(self):
        return json.dumps(self.issues, indent=2)


class YAML(Engine):
    def __str__(self):
        return yaml.safe_dump(self.issues, default_flow_style=False)


class HTML(Engine):
    def __init__(self, issues: Issues):
        self.load_template()
        super().__init__(issues)

    def __str__(self):
        return self.template.render(report=_make_report(self.issues))

    def load_template(self):
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_HTML_STATIC_FOLDER),
            autoescape=True,
        )
        env.filters["strip"] = _strip
        self.template = env.get_template(_HTML_TEMPLATE)


def _make_report(issues: Issues) -> Meta:
    total, entropy, regexes = len(issues), 0, 0
    mapping = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for issue in issues:
        reason = issue["reason"]
        if reason == "High entropy":
            entropy += 1
        else:
            regexes += 1

        folder = os.path.dirname(issue["path"])
        filename = os.path.basename(issue["path"])
        mapping[reason][folder][filename].append(issue)

    return {
        "total": total,
        "entropy": entropy,
        "regexes": regexes,
        "issues": mapping,
    }


def _strip(data: str) -> str:
    return data.strip() if data else None
