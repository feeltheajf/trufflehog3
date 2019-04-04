"""truffleHog unittests."""

import git
import os
import sys
import unittest

from tempfile import TemporaryDirectory

from truffleHog3 import scanner
from truffleHog3 import __main__ as cli

PATH = os.path.join(scanner.CWD, "__main__.py")
REPO = "https://github.com/feeltheajf/truffleHog3"


class TestStringMethods(unittest.TestCase):

    def test_shannon(self):
        random_stringB64 = ("ZWVTjPQSdhwRgl204Hc51YCsritMIzn8"
                            "B=/p9UyeX7xu6KkAGqfm3FJ+oObLDNEva")
        random_stringHex = "b3A0a1FDfe86dcCE945B72"
        self.assertGreater(
            scanner.shannon_entropy(
                random_stringB64,
                scanner.BASE64_CHARS),
            4.5
        )
        self.assertGreater(
            scanner.shannon_entropy(
                random_stringHex,
                scanner.HEX_CHARS),
            3
        )

    def test_return_correct_commit_hash(self):
        # Start at commit d15627104d07846ac2914a976e8e347a663bbd9b, which
        # is immediately followed by a secret inserting commit:
        # https://github.com/feeltheajf/truffleHog3/commit/9ed54617547cfca783e0f81f8dc5c927e3d1e345
        since_commit = "d15627104d07846ac2914a976e8e347a663bbd9b"
        commit_w_secret = "9ed54617547cfca783e0f81f8dc5c927e3d1e345"
        cross_valdiating_commit_w_secret_comment = "OH no a secret"

        with TemporaryDirectory() as tmp:
            git.Repo.clone_from(REPO, tmp)
            scanner.config.since_commit = since_commit
            results = scanner.search_history(tmp)

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

    def test_main_remote_with_history(self):
        sys.argv = [PATH, REPO]
        self.assertEqual(1, cli.main())

    def test_main_local_no_history(self):
        sys.argv = [PATH, "./scripts", "--no-history"]
        self.assertEqual(1, cli.main())

    def test_exclude(self):
        scanner.config.exclude = ["truffleHog3/.*", "test.*.py"]
        self.assertEqual(5, len(scanner.search(".")))


if __name__ == "__main__":
    unittest.main()
