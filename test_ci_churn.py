"""Offline GitHub pagination regressions; no gh credentials required."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import subprocess
import unittest
from unittest.mock import patch

import ci_churn


class GitHubPaginationTests(unittest.TestCase):
    def mock_pages(self, pages):
        return patch(
            "ci_churn.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(pages), stderr=""
            ),
        )

    def test_array_pages_preserve_nested_values_and_brackets(self):
        pages = [
            [{"sha": "a", "commit": {"message": "fix: [nested]", "parents": []}}],
            [{"sha": "b", "commit": {"message": "feat: second page"}}],
        ]
        with self.mock_pages(pages) as run:
            rows = ci_churn._gh("repos/example/repo/pulls/1/commits")
        self.assertEqual(rows, pages[0] + pages[1])
        self.assertEqual(
            run.call_args.args[0],
            ["gh", "api", "--paginate", "--slurp",
             "repos/example/repo/pulls/1/commits"],
        )

    def test_single_object_is_not_flattened(self):
        detail = {"head": {"ref": "feature/test", "repo": {"full_name": "a/b"}}}
        with self.mock_pages([detail]):
            self.assertEqual(ci_churn._gh("repos/a/b/pulls/1"), detail)

    def test_single_array_and_empty_collection(self):
        for pages, expected in [([[{"id": 1}]], [{"id": 1}]), ([[]], []), ([], [])]:
            with self.subTest(pages=pages), self.mock_pages(pages):
                self.assertEqual(ci_churn._gh("repos/a/b/events"), expected)

    def test_pr_commits_include_later_pages(self):
        pages = [
            [{"sha": "a" * 40, "commit": {"message": "feat: first\nbody"}}],
            [{"sha": "b" * 40, "commit": {"message": "fix: second"}}],
        ]
        with self.mock_pages(pages):
            rows = ci_churn.get_pr_commits(1, "a", "b")
        self.assertEqual([row["sha"] for row in rows], ["a" * 40, "b" * 40])
        self.assertEqual(rows[0]["message"], "feat: first")
        self.assertFalse(rows[1]["replaced"])

    def test_workflow_pages_contribute_to_churn_totals(self):
        def workflow(run_id, duration):
            return {
                "id": run_id,
                "name": "CI",
                "conclusion": "success",
                "created_at": "2026-07-01T00:00:00Z",
                "run_started_at": "2026-07-01T00:00:00Z",
                "updated_at": f"2026-07-01T00:00:{duration:02d}Z",
            }

        pages = [
            {"total_count": 2, "workflow_runs": [workflow(1, 10)]},
            {"total_count": 2, "workflow_runs": [workflow(2, 20)]},
        ]
        with self.mock_pages(pages):
            runs = ci_churn.get_runs_for_sha("abc", "a", "b")
        self.assertEqual([run["run_id"] for run in runs], [1, 2])
        metrics = ci_churn.calculate_churn(
            [{"sha": "abc", "short": "abc", "message": "fix ci"}],
            {"abc": runs}, [],
        )
        self.assertEqual(metrics["avoidable_ci_s"], 30)
        self.assertEqual(metrics["avoidable_wall_s"], 20)

    def test_empty_workflow_collection(self):
        with self.mock_pages([{"total_count": 0, "workflow_runs": []}]):
            self.assertEqual(ci_churn.get_runs_for_sha("abc", "a", "b"), [])

    def test_invalid_page_shapes_raise_instead_of_dropping_data(self):
        for pages in [None, {}, [[], {}], [{}, {}]]:
            with self.subTest(pages=pages), self.mock_pages(pages):
                with self.assertRaises(RuntimeError):
                    ci_churn._gh("repos/a/b/events")
        for pages in [[{}], [{"workflow_runs": None}], [{"workflow_runs": []}, {}]]:
            with self.subTest(pages=pages), self.mock_pages(pages):
                with self.assertRaises(RuntimeError):
                    ci_churn.get_runs_for_sha("abc", "a", "b")

    def test_malformed_json_raises_api_error(self):
        with patch("ci_churn.subprocess.run", return_value=subprocess.CompletedProcess(
            [], 0, stdout="not json", stderr=""
        )):
            with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                ci_churn._gh("repos/a/b/events")

    def test_nonzero_gh_exit_retains_error(self):
        with patch("ci_churn.subprocess.run", return_value=subprocess.CompletedProcess(
            [], 1, stdout="", stderr="rate limit exceeded"
        )):
            with self.assertRaisesRegex(RuntimeError, "rate limit exceeded"):
                ci_churn._gh("repos/a/b/events")


class CommandFailureTests(unittest.TestCase):
    def test_missing_gh_exits_one_without_traceback_or_report(self):
        out, err = StringIO(), StringIO()
        with patch("sys.argv", ["ci_churn.py", "1", "--owner", "a", "--repo", "b"]), \
             patch("ci_churn.subprocess.run", side_effect=FileNotFoundError), \
             redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as exited:
                ci_churn.main()
        self.assertEqual(exited.exception.code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("gh CLI is not installed or not authenticated", err.getvalue())

    def test_workflow_fetch_error_does_not_report_zero_usage(self):
        out, err = StringIO(), StringIO()
        commit = {"sha": "abc", "short": "abc", "message": "fix ci"}
        with patch("sys.argv", ["ci_churn.py", "1", "--owner", "a", "--repo", "b", "--json"]), \
             patch("ci_churn.subprocess.run", return_value=subprocess.CompletedProcess([], 0)), \
             patch("ci_churn.get_pr_commits", return_value=[commit]), \
             patch("ci_churn.get_force_pushed_shas", return_value=[]), \
             patch("ci_churn.get_runs_for_sha", side_effect=RuntimeError("rate limit")), \
             redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as exited:
                ci_churn.main()
        self.assertEqual(exited.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("could not fetch workflow runs for abc", err.getvalue())
        self.assertIn("rate limit", err.getvalue())


if __name__ == "__main__":
    unittest.main()
