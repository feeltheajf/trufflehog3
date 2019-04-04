[![Build Status](https://travis-ci.com/feeltheajf/truffleHog3.svg?branch=master)](https://travis-ci.com/feeltheajf/truffleHog3)
[![codecov](https://codecov.io/gh/feeltheajf/truffleHog3/branch/master/graph/badge.svg)](https://codecov.io/gh/feeltheajf/truffleHog3)


# truffleHog3
This is an enhanced version of [truffleHog](https://github.com/dxa4481/truffleHog) scanner


## New

- Python3.6
- refactored code
- option for file output
- option to disable Git history checks - scan simple files/folders


## Roadmap

- ~~update tests~~
- ~~setup travis integration~~
- ~~add package to PYPI~~
- valid JSON output?


## Installation

Package is now available on [PYPI](https://pypi.org)
```
pip install truffleHog3
```


## Customizing

List of regexes was moved into repository, see [regexes.json](https://github.com/feeltheajf/truffleHog/blob/master/regexes/regexes.json)


## Help

```
usage: truffleHog.py [-h] [-r RULES] [-o OUTPUT] [--json] [--no-regex]
                     [--no-entropy] [--no-history]
                     [--since-commit SINCE_COMMIT] [--max-depth MAX_DEPTH]
                     [--branch BRANCH]
                     source

Find secrets hidden in the depths of git.

positional arguments:
  source                URL or local path for secret searching

optional arguments:
  -h, --help            show this help message and exit
  -r RULES, --rules RULES
                        ignore default regexes and source from json
  -o OUTPUT, --output OUTPUT
                        write report to file
  --json                output in JSON
  --no-regex            disable high signal regex checks
  --no-entropy          disable entropy checks
  --no-history          disable commit history check
  --since-commit SINCE_COMMIT
                        only scan starting from a given commit hash
  --max-depth MAX_DEPTH
                        max commit depth when searching for secrets
  --branch BRANCH       name of the branch to be scanned
```


## Thanks

Special thanks to Dylan Ayrey ([@dxa4481](https://github.com/dxa4481)), developer of the original [truffleHog](https://github.com/dxa4481/truffleHog) scanner
