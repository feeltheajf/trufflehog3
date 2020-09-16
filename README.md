[![Package Version](https://img.shields.io/pypi/v/truffleHog3.svg)](https://pypi.org/project/truffleHog3)
![Python Version](https://img.shields.io/badge/python-3.6%2B-informational.svg)
[![Downloads](https://pepy.tech/badge/trufflehog3)](https://pepy.tech/project/trufflehog3)
[![Build Status](https://travis-ci.com/feeltheajf/truffleHog3.svg?branch=master)](https://travis-ci.com/feeltheajf/truffleHog3)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Ffeeltheajf%2Ftrufflehog3.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Ffeeltheajf%2Ftrufflehog3?ref=badge_shield)
[![Code Coverage](https://codecov.io/gh/feeltheajf/truffleHog3/branch/master/graph/badge.svg)](https://codecov.io/gh/feeltheajf/truffleHog3)


# truffleHog3
This is an enhanced version of [truffleHog](https://github.com/dxa4481/truffleHog) scanner

[![Report Preview](https://github.com/feeltheajf/truffleHog3/blob/master/examples/report.png)](https://feeltheajf.github.io/other/trufflehog)


## Important

TruffleHog 2.x is not backwards compatible with 1.x branch, see new [trufflehog.yaml](https://github.com/feeltheajf/truffleHog3/blob/master/examples/trufflehog.yaml) and [Help](#Help)


## New

- Python 3.6
- flake8 compliant code
- output to file in different formats: text, JSON, YAML, [HTML](https://feeltheajf.github.io/other/trufflehog)
- option to disable Git history checks - scan simple files/directories
- option to exclude files/directories, see [trufflehog.yaml](https://github.com/feeltheajf/truffleHog3/blob/master/examples/trufflehog.yaml)
- config file support with automatic detection in source code directory


## Installation

Package is available on [PyPI](https://pypi.org/project/truffleHog3)

```
pip install truffleHog3
```


## Customizing

List of default regexes was moved into repository, see [rules.yaml](https://github.com/feeltheajf/truffleHog3/blob/master/truffleHog3/rules.yaml)


## Help

```
usage: trufflehog3 [options] source

Find secrets in your codebase.

positional arguments:
  source             URLs or paths to local folders for secret searching

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      enable verbose logging {-v, -vv, -vvv}
  -c, --config       path to config file
  -o, --output       write report to file
  -f, --format       output format {text, json, yaml, html}
  -r, --rules        ignore default regexes and source from file
  -R, --render-html  render HTML report from JSON or YAML
  --branch           name of the repository branch to be scanned
  --since-commit     scan starting from a given commit hash
  --skip-strings     skip matching strings
  --skip-paths       skip paths matching regex
  --line-numbers     include line numbers in match
  --max-depth        max commit depth for searching
  --no-regex         disable high signal regex checks
  --no-entropy       disable entropy checks
  --no-history       disable commit history check
  --no-current       disable current status check
```


## Thanks

Special thanks to Dylan Ayrey ([@dxa4481](https://github.com/dxa4481)), developer of the original [truffleHog](https://github.com/dxa4481/truffleHog) scanner
