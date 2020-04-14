from truffleHog3.lib.search import Regex, Entropy
from truffleHog3.types import Issue, Meta, Rules


def test_regex(
    rules: Rules, meta_entropy: Meta, meta_regex: Meta, issue_regex: Issue
):
    re = Regex(rules)
    assert len(re.process(meta_entropy)) == 0

    issues = re.process(meta_regex)
    assert len(issues) == 1
    assert issues[0] == issue_regex

    re.skip = ["@localhost"]
    assert len(re.process(meta_regex)) == 0


def test_entropy(meta_entropy: Meta, meta_regex: Meta, issue_entropy: Issue):
    en = Entropy()
    assert len(en.process(meta_regex)) == 0

    issues = en.process(meta_entropy)
    assert len(issues) == 1
    assert issues[0] == issue_entropy

    en.skip = {"/high_entropy.py": "f18e9874c9"}
    assert len(en.process(meta_entropy)) == 0
