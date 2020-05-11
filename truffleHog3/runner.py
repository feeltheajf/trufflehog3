import argparse
import json
import logging
from tempfile import TemporaryDirectory
from typing import List

from truffleHog3 import cli
from truffleHog3.lib import log, utils
from truffleHog3.types import Issue, Config


def get_config(dir_source: str,
               rules_file: str,
               branch=None,
               config=None,
               format='text',
               max_depth=None,
               no_current=False,
               no_entropy=False,
               no_history=False,
               no_regex=False,
               output=None,
               render_html=False,
               since_commit=None,
               skip_paths=None,
               skip_strings=None,
               verbose=0):
    return argparse.Namespace(branch=branch,
                              config=config,
                              format=format,
                              max_depth=max_depth,
                              no_current=no_current,
                              no_entropy=no_entropy,
                              no_history=no_history,
                              no_regex=no_regex,
                              output=output,
                              render_html=render_html,
                              rules=open(
                                  rules_file,
                                  mode='r',
                                  encoding='UTF-8'),
                              since_commit=since_commit,
                              skip_paths=skip_paths,
                              skip_strings=skip_strings,
                              source=[dir_source],
                              verbose=verbose)


def run(config: argparse.Namespace) -> List[Issue]:
    log.setLevel(logging.ERROR - config.verbose * 10)
    rules = utils.load(config.rules)

    issues: List[Issue] = []
    source_dir = config.source[0]

    config_obj = Config()
    config_obj.update(**config.__dict__)

    with TemporaryDirectory() as tmp:
        cli.copy(source_dir, tmp)
        issues.extend(cli.scan(tmp, config_obj, rules))

    print(json.dumps(issues, indent=2))

    return issues
