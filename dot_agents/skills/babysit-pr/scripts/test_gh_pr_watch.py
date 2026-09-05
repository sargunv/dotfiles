"""Offline regression tests: python3 -B -m unittest discover -s scripts -v."""

import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gh_pr_watch as watch

HEAD = "a" * 40
BEFORE = "2026-09-05T10:00:00Z"
NOW = "2026-09-05T11:00:00Z"
AFTER = "2026-09-05T12:00:00Z"
CODEX = {"login": "chatgpt-codex-connector[bot]"}
GREPTILE = {"login": "greptile-apps[bot]"}


def snapshot():
    return {
        "pr": {
            "number": 1,
            "head": {"sha": HEAD},
            "state": "open",
            "body": "",
            "updated_at": NOW,
            "html_url": "https://github.com/o/r/pull/1",
            "mergeable": True,
            "mergeable_state": "clean",
            "draft": False,
        },
        "checks": [
            {"name": "test", "state": "success", "url": "https://example.com"}
        ],
        "comments": [],
        "reviews": [],
        "inline": [],
        "threads": [],
        "reactions": [],
    }


def summary(body=None):
    return {
        "id": 10,
        "user": GREPTILE,
        "updated_at": NOW,
        "html_url": "https://github.com/o/r/pull/1#issuecomment-10",
        "body": body
        or f"Confidence Score: 5/5\nLast reviewed commit: `{HEAD[:7]}`",
    }


class TriageTests(unittest.TestCase):
    def test_explicit_bot_selection_overrides_history_without_hiding_findings(
        self,
    ):
        data, state = snapshot(), {}
        data["comments"] = [summary()]
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": BEFORE}
        ]
        result = watch.evaluate(data, state, ["greptile"])
        self.assertEqual(result["event"], "action_required")
        state["acknowledged"] = [result["items"][0]["token"]]
        result = watch.evaluate(data, state)
        self.assertEqual(result["event"], "clean")
        self.assertFalse(result["bots"]["codex"]["required"])
        data["comments"][0]["body"] += "\nAnother finding."
        self.assertEqual(
            watch.evaluate(data, state, [])["event"], "action_required"
        )

    def test_codex_activity_summary_does_not_wake_or_supersede_review(self):
        data, state = snapshot(), {}
        data["comments"] = [
            {
                "id": 10,
                "user": CODEX,
                "updated_at": AFTER,
                "html_url": "url",
                "body": "<!-- codex-pull-request-review-summary -->\n\n## Codex Review Summary\n"
                "| Review | Status | Commit | Review trigger |\n"
                "| Code Review | Running | `aaaaaaa` | PR opened |",
            }
        ]
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "eyes", "created_at": AFTER}
        ]
        result = watch.evaluate(data, state)
        self.assertEqual(result["event"], "waiting")
        self.assertEqual(result["items"], [])
        data["reactions"][0].update(id=2, content="+1")
        self.assertEqual(watch.evaluate(data, state)["event"], "clean")

    def test_later_empty_review_preserves_current_greptile_score(self):
        data, state = snapshot(), {}
        data["comments"] = [summary()]
        data["reviews"] = [
            {
                "id": 20,
                "user": GREPTILE,
                "state": "COMMENTED",
                "body": "",
                "submitted_at": AFTER,
                "commit_id": HEAD,
                "html_url": "url",
            }
        ]
        result = watch.evaluate(data, state)
        state["acknowledged"] = [result["items"][0]["token"]]
        result = watch.evaluate(data, state)
        self.assertEqual(result["event"], "clean")
        self.assertEqual(result["bots"]["greptile"]["score"], 5)

    def test_reaction_discovery_includes_description_findings_immediately(self):
        data = snapshot()
        data["pr"]["body"] = summary()["body"] + "\nFix this edge case."
        data["reactions"] = [
            {"id": 1, "user": GREPTILE, "content": "+1", "created_at": AFTER}
        ]
        result = watch.evaluate(data, {})
        self.assertEqual(result["event"], "action_required")
        self.assertEqual(result["items"][0]["kind"], "description")
        self.assertIn("Fix this edge case.", result["items"][0]["body"])

    def test_no_bots_and_explicit_expected_bot(self):
        self.assertEqual(watch.evaluate(snapshot(), {})["event"], "clean")
        state = {}
        self.assertEqual(
            watch.evaluate(snapshot(), state, ["codex"])["event"],
            "waiting",
        )
        # An expected bot stays expected on subsequent invocations.
        self.assertEqual(watch.evaluate(snapshot(), state)["event"], "waiting")

    def test_summary_only_findings_persist_and_edits_reappear(self):
        data, state = snapshot(), {}
        data["comments"] = [summary()]
        result = watch.evaluate(data, state)
        token = result["items"][0]["token"]
        self.assertEqual(result["event"], "action_required")
        self.assertEqual(
            watch.evaluate(data, state)["items"][0]["token"], token
        )
        state["acknowledged"] = [token]
        self.assertEqual(watch.evaluate(data, state)["event"], "clean")
        data["comments"][0]["body"] += "\nA newly added edge case."
        result = watch.evaluate(data, state)
        self.assertEqual(result["event"], "action_required")
        self.assertNotEqual(result["items"][0]["token"], token)

    def test_handled_is_not_clean(self):
        data, state = snapshot(), {}
        data["comments"] = [summary().copy()]
        data["comments"][0]["body"] = data["comments"][0]["body"].replace(
            "5/5", "3/5"
        )
        data["reactions"] = [
            {"id": 1, "user": GREPTILE, "content": "+1", "created_at": AFTER}
        ]
        state["acknowledged"] = [
            watch.evaluate(data, state)["items"][0]["token"]
        ]
        result = watch.evaluate(data, state)
        self.assertEqual(result["event"], "handled")
        self.assertTrue(result["bots"]["greptile"]["complete"])
        self.assertFalse(result["bots"]["greptile"]["clean"])

    def test_codex_review_with_findings_completes_without_thumb(self):
        data, state = snapshot(), {}
        data["reviews"] = [
            {
                "id": 20,
                "user": CODEX,
                "state": "COMMENTED",
                "body": "Fix x",
                "submitted_at": NOW,
                "commit_id": HEAD,
                "html_url": "url",
            }
        ]
        result = watch.evaluate(data, state)
        state["acknowledged"] = [result["items"][0]["token"]]
        self.assertEqual(watch.evaluate(data, state)["event"], "handled")
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": AFTER}
        ]
        self.assertEqual(watch.evaluate(data, state)["event"], "clean")

    def test_old_thumb_not_current_approval_and_push_resets_freshness(self):
        data, state = snapshot(), {}
        data["reactions"] = [
            {
                "id": 1,
                "user": CODEX,
                "content": "+1",
                "created_at": "2999-01-01T00:00:00Z",
            }
        ]
        self.assertEqual(watch.evaluate(data, state)["event"], "waiting")
        data["reactions"][0]["id"] = 2
        data["reactions"][0]["created_at"] = "2000-01-01T00:00:00Z"
        self.assertEqual(watch.evaluate(data, state)["event"], "clean")
        data["pr"]["head"]["sha"] = "b" * 40
        self.assertEqual(watch.evaluate(data, state)["event"], "waiting")

    def test_eyes_prevent_clean_even_with_thumb(self):
        data = snapshot()
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": c, "created_at": AFTER}
            for c in ("eyes", "+1")
        ]
        self.assertEqual(watch.evaluate(data, {})["event"], "waiting")

    def test_late_review_of_old_head_does_not_validate_new_thumb(self):
        data, state = snapshot(), {}
        watch.evaluate(data, state)
        data["reviews"] = [
            {
                "id": 20,
                "user": CODEX,
                "state": "COMMENTED",
                "body": "Old review",
                "submitted_at": AFTER,
                "commit_id": "b" * 40,
                "html_url": "url",
            }
        ]
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": AFTER}
        ]
        result = watch.evaluate(data, state)
        self.assertFalse(result["bots"]["codex"]["clean"])

    def test_later_findings_supersede_earlier_thumb_on_same_head(self):
        data, state = snapshot(), {}
        watch.evaluate(data, state)
        data["reviews"] = [
            {
                "id": 20,
                "user": CODEX,
                "state": "COMMENTED",
                "body": "New finding",
                "submitted_at": AFTER,
                "commit_id": HEAD,
                "html_url": "url",
            }
        ]
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": NOW}
        ]
        result = watch.evaluate(data, state)
        self.assertTrue(result["bots"]["codex"]["complete"])
        self.assertFalse(result["bots"]["codex"]["clean"])

    def test_outdated_threads_keep_all_replies_until_resolved(self):
        data, state = snapshot(), {}
        data["inline"] = [
            {"id": 30, "user": CODEX, "body": "Check this", "commit_id": "old"}
        ]
        data["inline"] += [
            {
                "id": 31 + n,
                "user": {"login": "human"},
                "body": str(n),
                "in_reply_to_id": 30,
            }
            for n in range(110)
        ]
        data["threads"] = [
            {
                "id": "THREAD",
                "isResolved": False,
                "isOutdated": True,
                "comments": {"nodes": [{"databaseId": 30}]},
            }
        ]
        result = watch.evaluate(data, state)
        self.assertEqual(len(result["items"][0]["comments"]), 111)
        self.assertEqual(state["offered"], [])
        state["acknowledged"] = [result["items"][0]["token"]]
        self.assertEqual(
            watch.evaluate(data, state)["event"], "action_required"
        )
        data["threads"][0]["isResolved"] = True
        self.assertEqual(watch.evaluate(data, state)["items"], [])

    def test_ci_conflicts_and_blockers(self):
        for check_state, event in [
            ("pending", "waiting"),
            ("failure", "action_required"),
            ("cancelled", "action_required"),
            ("skipped", "clean"),
        ]:
            with self.subTest(check_state=check_state):
                data = snapshot()
                data["checks"][0]["state"] = check_state
                self.assertEqual(watch.evaluate(data, {})["event"], event)
        for field, value, event in [
            ("mergeable", False, "action_required"),
            ("mergeable", None, "waiting"),
            ("mergeable_state", "blocked", "blocked"),
            ("draft", True, "blocked"),
            ("state", "closed", "closed"),
        ]:
            data = snapshot()
            data["pr"][field] = value
            self.assertEqual(watch.evaluate(data, {})["event"], event)

    def test_score_and_commit_marker_do_not_match_incidental_numbers(self):
        self.assertIsNone(watch.score("Example 5/5 was fine"))
        self.assertEqual(watch.score("### Confidence Score: 4/5"), 4)
        self.assertTrue(watch.reviewed_head(summary()["body"], HEAD))
        self.assertFalse(watch.reviewed_head(f"Fix {HEAD}", HEAD))
        self.assertFalse(watch.reviewed_head(summary()["body"], "b" * 40))


class ApiTests(unittest.TestCase):
    def test_distinct_suites_keep_failures_and_only_replace_their_own_reruns(
        self,
    ):
        def check(run_id, suite_id, conclusion):
            return {
                "id": run_id,
                "check_suite": {"id": suite_id},
                "name": "test",
                "status": "completed",
                "conclusion": conclusion,
                "html_url": "url",
            }

        checks = [
            check(1, 10, "failure"),
            check(2, 20, "success"),
            check(3, 30, "failure"),
            check(4, 30, "success"),
        ]
        with (
            patch.object(
                watch,
                "gh_json",
                side_effect=[
                    snapshot()["pr"],
                    [{"check_runs": checks}],
                    snapshot()["pr"],
                ],
            ) as call,
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "review_threads", return_value=[]),
        ):
            data = watch.fetch("o/r", 1)
        self.assertIsNotNone(data)
        self.assertEqual(len(data["checks"]), 3)
        self.assertIn("filter=all", call.call_args_list[1].args[0][-1])
        result = watch.evaluate(data, {})
        self.assertEqual(result["event"], "action_required")
        self.assertEqual(len(result["failed_checks"]), 1)

    def test_new_inline_root_without_thread_discards_incomplete_snapshot(self):
        with (
            patch.object(
                watch,
                "gh_json",
                side_effect=[snapshot()["pr"], [{"check_runs": []}]],
            ),
            patch.object(
                watch,
                "api_list",
                side_effect=[[], [], [], [{"id": 30, "user": GREPTILE}], []],
            ),
            patch.object(watch, "review_threads", return_value=[]),
        ):
            self.assertIsNone(watch.fetch("o/r", 1))

    def test_missing_thread_root_discards_incomplete_snapshot(self):
        thread = {
            "id": "THREAD",
            "isResolved": False,
            "comments": {"nodes": [{"databaseId": 30}]},
        }
        with (
            patch.object(
                watch,
                "gh_json",
                side_effect=[snapshot()["pr"], [{"check_runs": []}]],
            ),
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "review_threads", return_value=[thread]),
        ):
            self.assertIsNone(watch.fetch("o/r", 1))

    def test_rest_pagination_flattens_all_pages(self):
        with patch.object(
            watch, "gh_json", return_value=[[1] * 100, [2]]
        ) as call:
            self.assertEqual(len(watch.api_list("endpoint")), 101)
            self.assertIn("--paginate", call.call_args.args[0])

    def test_graphql_thread_pagination(self):
        def page(node, more, cursor):
            return {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [node],
                            "pageInfo": {
                                "hasNextPage": more,
                                "endCursor": cursor,
                            },
                        }
                    }
                }
            }

        with patch.object(
            watch,
            "graphql",
            side_effect=[page(1, True, "next"), page(2, False, None)],
        ) as call:
            self.assertEqual(watch.review_threads("o/r", 1), [1, 2])
            self.assertEqual(call.call_args.kwargs["cursor"], "next")

    def test_head_race_discards_snapshot(self):
        before = snapshot()["pr"]
        after = copy.deepcopy(before)
        after["head"]["sha"] = "b" * 40
        with (
            patch.object(
                watch,
                "gh_json",
                side_effect=[before, [{"check_runs": []}], after],
            ),
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "review_threads", return_value=[]),
        ):
            self.assertIsNone(watch.fetch("o/r", 1))

    def test_watch_is_quiet_until_ci_failure(self):
        pending, failed = snapshot(), snapshot()
        pending["checks"][0]["state"] = "pending"
        failed["checks"][0]["state"] = "failure"
        with tempfile.TemporaryDirectory() as tmp:
            args = [
                "watch",
                "--watch",
                "--state-file",
                str(Path(tmp) / "state.json"),
            ]
            out = io.StringIO()
            with (
                patch("sys.argv", args),
                patch("sys.stdout", out),
                patch.object(watch, "resolve_pr", return_value=("o/r", 1)),
                patch.object(
                    watch, "fetch", side_effect=[pending, pending, failed]
                ),
                patch.object(watch.time, "sleep") as sleep,
            ):
                watch.main()
            self.assertEqual(sleep.call_count, 2)
            self.assertEqual(len(out.getvalue().splitlines()), 1)
            self.assertEqual(
                json.loads(out.getvalue())["event"], "action_required"
            )

    def test_watch_gives_new_ci_a_poll_to_appear(self):
        ready, pending, failed = snapshot(), snapshot(), snapshot()
        pending["checks"][0]["state"] = "pending"
        failed["checks"][0]["state"] = "failure"
        with tempfile.TemporaryDirectory() as tmp:
            args = [
                "watch",
                "--watch",
                "--state-file",
                str(Path(tmp) / "state.json"),
            ]
            out = io.StringIO()
            with (
                patch("sys.argv", args),
                patch("sys.stdout", out),
                patch.object(watch, "resolve_pr", return_value=("o/r", 1)),
                patch.object(
                    watch, "fetch", side_effect=[ready, pending, failed]
                ),
                patch.object(watch.time, "sleep") as sleep,
            ):
                watch.main()
            self.assertEqual(sleep.call_count, 2)
            self.assertEqual(
                json.loads(out.getvalue())["event"], "action_required"
            )


if __name__ == "__main__":
    unittest.main()
