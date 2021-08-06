"""Run trufflehog3 as a module.

Currently, it is the same as running it with CLI

```bash
$ python -m trufflehog3 --help
```
"""

from trufflehog3 import cli  # pragma: no cover

cli.run()  # pragma: no cover
