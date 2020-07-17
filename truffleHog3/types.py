import yaml

from typing import Any, Generator, List, Mapping, re, TextIO, Tuple, Union


File = Union[str, TextIO]
Issue = Mapping[str, Any]
Issues = List[Issue]
Meta = Mapping[str, Any]
MetaGen = Generator[Meta, None, None]
Regex = re.Pattern
Regexes = List[re.Pattern]
Repo = Tuple[str, Meta]
RawRules = Mapping[str, str]
Rules = Mapping[str, re.Pattern]
SkipRules = Union[List[str], Mapping[str, List[str]]]
StrGen = Generator[str, None, None]


class Config:
    def __init__(self, **kwargs):
        self.branch = None
        self.since_commit = None
        self.skip_strings = []
        self.skip_paths = []
        self.line_numbers = False
        self.max_depth = 1000000
        self.no_regex = False
        self.no_entropy = False
        self.no_history = False
        self.no_current = False
        self.update(**kwargs)

    def __repr__(self):
        return yaml.safe_dump(self.raw, default_flow_style=False)

    def __eq__(self, other):
        if isinstance(other, Config):
            return self.raw == other.raw
        return self.raw == other

    @property
    def raw(self) -> dict:
        items = self.__dict__.items()
        return {k: v for k, v in items if not k.startswith("_")}

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
