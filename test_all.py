"""truffleHog3 unittests."""

import git
import os
import sys
import unittest

from tempfile import TemporaryDirectory

from truffleHog3 import cli
from truffleHog3 import core

PATH = os.path.join(core.CWD, "cli.py")
REPO = "https://github.com/feeltheajf/truffleHog3"


class TestCLI(unittest.TestCase):

    def test_package_run(self):
        r = os.system("python3 -m truffleHog3 -h")
        self.assertEqual(0, r)

    def test_should_fail_on_non_existentt_rules_file(self):
        with self.assertRaises(IOError):
            sys.argv = [PATH, REPO, "--rules", "no_rules.json"]
            cli.run()

    def test_local_file(self):
        sys.argv = [PATH, "./tests/test_slack_token.json", "--no-history"]
        self.assertEqual(1, cli.run())

    def test_local_directory_no_history(self):
        sys.argv = [PATH, "./tests", "--no-history"]
        self.assertEqual(1, cli.run())

    def test_should_fail_on_remote_non_existent(self):
        with self.assertRaises(RuntimeError):
            sys.argv = [PATH, REPO + "21"]
            cli.run()

    def test_remote_with_history(self):
        sys.argv = [PATH, REPO]
        self.assertEqual(1, cli.run())

    def test_branch(self):
        sys.argv = [PATH, REPO, "--branch", "master"]
        self.assertEqual(1, cli.run())


class TestCore(unittest.TestCase):

    def test_shannon(self):
        random_stringB64 = ("ZWVTjPQSdhwRgl204Hc51YCsritMIzn8"
                            "B=/p9UyeX7xu6KkAGqfm3FJ+oObLDNEva")
        random_stringHex = "b3A0a1FDfe86dcCE945B72"
        self.assertGreater(
            core._shannon_entropy(
                random_stringB64,
                core.BASE64_CHARS),
            4.5
        )
        self.assertGreater(
            core._shannon_entropy(
                random_stringHex,
                core.HEX_CHARS),
            3
        )

    def test_return_correct_commit_hash(self):
        # Start at commit d15627104d07846ac2914a976e8e347a663bbd9b, which
        # is immediately followed by a secret inserting commit:
        # 9ed54617547cfca783e0f81f8dc5c927e3d1e345
        since_commit = "d15627104d07846ac2914a976e8e347a663bbd9b"
        commit_w_secret = "9ed54617547cfca783e0f81f8dc5c927e3d1e345"
        cross_valdiating_commit_w_secret_comment = "OH no a secret"

        with TemporaryDirectory() as tmp:
            git.Repo.clone_from(REPO, tmp)
            core.config.since_commit = since_commit
            results = core.search_history(tmp)

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

    def test_exclude(self):
        core.config.exclude = ["truffleHog3/.*", "test.*.py"]
        issues = core.search_current(".")
        core.log(issues)
        self.assertEqual(5, len(issues))


if __name__ == "__main__":
    unittest.main()
