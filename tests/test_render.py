import os

from truffleHog3.lib import utils
from truffleHog3.lib.render import TEXT, JSON, YAML, HTML
from truffleHog3.types import Issues


def test_render(issues: Issues, datadir: str, tempdir: str):
    for f in TEXT, JSON, YAML, HTML:
        report_name = f"report.{f.__name__.lower()}"
        original = os.path.join(datadir, report_name)
        expected = os.path.join(tempdir, report_name)
        utils.dump(f(issues), expected)

        with open(original) as f1, open(expected) as f2:
            assert f1.read() == f2.read()
