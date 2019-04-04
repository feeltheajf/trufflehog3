"""truffleHog unittests."""

import git
import io
import json
import sys
import unittest

from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from truffleHog3 import truffleHog3 as tf

REPO = "https://github.com/feeltheajf/truffleHog3"


def scan_history(url, log=False, **kwargs):
    with TemporaryDirectory() as tmp:
        git.Repo.clone_from(url, tmp)
        issues = tf.search_history(tmp, tf.DEFAULT, **kwargs)
    if log:
        for issue in issues:
            tf.log_issue(issue, json_output=True)


class TestStringMethods(unittest.TestCase):

    def test_shannon(self):
        random_stringB64 = ("ZWVTjPQSdhwRgl204Hc51YCsritMIzn8"
                            "B=/p9UyeX7xu6KkAGqfm3FJ+oObLDNEva")
        random_stringHex = "b3A0a1FDfe86dcCE945B72"
        self.assertGreater(
            tf.shannon_entropy(
                random_stringB64,
                tf.BASE64_CHARS),
            4.5
        )
        self.assertGreater(
            tf.shannon_entropy(
                random_stringHex,
                tf.HEX_CHARS),
            3
        )

    def test_return_correct_commit_hash(self):
        # Start at commit d15627104d07846ac2914a976e8e347a663bbd9b, which
        # is immediately followed by a secret inserting commit:
        # https://github.com/feeltheajf/truffleHog3/commit/9ed54617547cfca783e0f81f8dc5c927e3d1e345
        since_commit = "d15627104d07846ac2914a976e8e347a663bbd9b"
        commit_w_secret = "9ed54617547cfca783e0f81f8dc5c927e3d1e345"
        cross_valdiating_commit_w_secret_comment = "OH no a secret"

        if sys.version_info >= (3,):
            tmp_stdout = io.StringIO()
        else:
            tmp_stdout = io.BytesIO()
        bak_stdout = sys.stdout

        # Redirect STDOUT, run scan and re-establish STDOUT
        sys.stdout = tmp_stdout
        try:
            scan_history(REPO, log=True, since_commit=since_commit)
        finally:
            sys.stdout = bak_stdout

        json_result_list = tmp_stdout.getvalue().split("\n")
        results = [json.loads(r) for r in json_result_list if bool(r.strip())]
        filtered_results = list(filter(
            lambda r: r["commitHash"] == commit_w_secret,
            results
        ))
        self.assertEqual(1, len(filtered_results))
        self.assertEqual(commit_w_secret, filtered_results[0]["commitHash"])
        # Additionally, we cross-validate the commit
        # comment matches the expected comment
        self.assertEqual(
            cross_valdiating_commit_w_secret_comment,
            filtered_results[0]["commit"].strip()
        )

    @patch("git.Repo.clone_from")
    @patch("git.Repo")
    def test_branch(self, repo_const_mock, clone_git_repo):
        repo = MagicMock()
        repo_const_mock.return_value = repo
        scan_history("test_repo", branch="testbranch")
        repo.remotes.origin.fetch.assert_called_once_with("testbranch")

    def test_search(self):
        issues = tf.search("./scripts", tf.DEFAULT)
        self.assertEqual(5, len(issues))


if __name__ == "__main__":
    unittest.main()
