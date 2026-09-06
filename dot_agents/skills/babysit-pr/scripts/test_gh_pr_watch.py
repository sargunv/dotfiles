"""Observable collector regressions; no bot prose interpretation is expected."""

import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gh_pr_watch as watch

HEAD = "3415b90d9372af69f51510a74af38dd83aeec775"
FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def snapshot():
    return {
        "pr": {
            "head": {"sha": HEAD},
            "mergeable": None,
            "mergeable_state": "unknown",
        },
        "ci": {"state": "FAILURE", "contexts": []},
        "comments": [fixture("greptile-summary"), fixture("codex-activity")],
        "reviews": [
            {
                "id": 20,
                "state": "APPROVED",
                "body": "Please fix this.",
                "commit_id": "6dc289d",
                "user": None,
            }
        ],
        "threads": [
            {
                "id": "T",
                "isResolved": True,
                "isOutdated": True,
                "comments": [
                    {
                        "id": 30,
                        "body": "A finding",
                        "user": {"login": "arbitrary-app", "type": "Bot"},
                        "path": "a.py",
                    },
                    {
                        "id": 31,
                        "in_reply_to_id": 30,
                        "body": "Human reply",
                        "user": {"login": "reviewer", "type": "User"},
                    },
                ],
            }
        ],
        "reactions": [
            {
                "id": 40,
                "content": "+1",
                "user": {"login": "another-app", "type": "Bot"},
            }
        ],
    }


def baseline(data):
    return {
        "version": 2,
        "pr": "o/r#1",
        "head": data["pr"]["head"]["sha"],
        "hashes": watch.fingerprints(data),
    }


class ActivityTests(unittest.TestCase):
    def test_actual_public_bodies_survive_output_verbatim(self):
        data = snapshot()
        greptile, codex = data["comments"]
        # The real descriptive link puts this SHA outside the former parser's
        # window. Keep the entire body, including the exact footer and URL.
        footer = greptile["body"].split("Last reviewed commit", 1)[1]
        self.assertGreater(footer.index(HEAD), 100)
        self.assertIn("Confidence Score: 5/5", greptile["body"])
        self.assertTrue(
            codex["body"].startswith(
                "<!-- codex-pull-request-review-summary -->"
            )
        )
        self.assertIn("`6dc289d`", codex["body"])
        result = json.loads(json.dumps(watch.observe(data, {})))
        self.assertEqual(result["snapshot"], data)
        self.assertEqual(result["event"], "snapshot")
        self.assertEqual(result["snapshot"]["comments"], [greptile, codex])
        self.assertEqual(
            set(result), {"event", "changed", "head_changed", "snapshot"}
        )

    def test_arbitrary_content_and_unknown_authors_are_never_filtered(self):
        for user in (
            None,
            {},
            {"login": "human", "type": "User"},
            {"login": "new-bot", "type": "Bot"},
        ):
            for state in (
                "APPROVED",
                "DISMISSED",
                "CHANGES_REQUESTED",
                "PENDING",
            ):
                with self.subTest(user=user, state=state):
                    data = snapshot()
                    data["reviews"][0].update(
                        user=user,
                        state=state,
                        body="<table>arbitrary request</table>",
                    )
                    data["comments"][0]["user"] = user
                    original = copy.deepcopy(data)
                    result = watch.observe(data, {})
                    self.assertEqual(result["snapshot"], original)
                    self.assertEqual(data, original)

    def test_edits_replies_deletions_and_state_changes_wake_observer(self):
        before = snapshot()
        mutations = [
            (
                "comments",
                lambda d: d["comments"][1].update(body="Edited activity table"),
            ),
            ("comments", lambda d: d["comments"].pop()),
            ("reviews", lambda d: d["reviews"][0].update(state="DISMISSED")),
            (
                "reviews",
                lambda d: d["reviews"][0].update(
                    body="New request in approval"
                ),
            ),
            ("threads", lambda d: d["threads"][0].update(isResolved=False)),
            (
                "threads",
                lambda d: d["threads"][0]["comments"][0].update(
                    body="Bot edit"
                ),
            ),
            (
                "threads",
                lambda d: d["threads"][0]["comments"][1].update(
                    body="Human edit"
                ),
            ),
            (
                "threads",
                lambda d: d["threads"][0]["comments"].append(
                    {"id": 99, "body": "Reply after resolution", "user": None}
                ),
            ),
            ("pr", lambda d: d["pr"].update(mergeable_state="blocked")),
            ("reactions", lambda d: d["reactions"].clear()),
            ("ci", lambda d: d["ci"].update(state="PENDING")),
        ]
        for section, mutate in mutations:
            with self.subTest(section=section, mutation=mutate):
                changed = copy.deepcopy(before)
                mutate(changed)
                result = watch.observe(changed, baseline(before))
                self.assertEqual(result["event"], "changed")
                self.assertEqual(result["changed"], [section])
                self.assertEqual(result["snapshot"], changed)

    def test_new_head_preserves_old_review_evidence_without_approval_gate(self):
        before = snapshot()
        after = copy.deepcopy(before)
        after["pr"]["head"]["sha"] = "b" * 40
        result = watch.observe(after, baseline(before))
        self.assertTrue(result["head_changed"])
        self.assertEqual(result["changed"], ["pr"])
        self.assertEqual(result["snapshot"]["reviews"], before["reviews"])
        self.assertEqual(result["snapshot"]["comments"], before["comments"])
        self.assertEqual(
            watch.observe(after, baseline(after))["event"], "unchanged"
        )


class ApiTests(unittest.TestCase):
    def test_rest_pagination_preserves_every_record(self):
        with patch.object(
            watch,
            "gh_json",
            return_value=[list(range(100)), list(range(100, 205))],
        ) as call:
            self.assertEqual(watch.api_list("endpoint"), list(range(205)))
            self.assertEqual(
                call.call_args.args[0],
                ["api", "--paginate", "--slurp", "endpoint"],
            )

    def test_graphql_thread_pagination(self):
        def page(nodes, more, cursor):
            return {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": nodes,
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
            side_effect=[
                page(list(range(100)), True, "next"),
                page([100], False, None),
            ],
        ) as call:
            self.assertEqual(watch.review_threads("o/r", 1), list(range(101)))
            self.assertEqual(call.call_args.kwargs["cursor"], "next")

    def test_fetch_preserves_full_threads_beyond_one_page(self):
        data = snapshot()
        inline = copy.deepcopy(data["threads"][0]["comments"])
        inline.extend(
            dict(inline[1], id=i, body=f"Reply {i}") for i in range(32, 237)
        )
        threads = [
            {
                "id": "T",
                "isResolved": True,
                "isOutdated": True,
                "comments": {"nodes": [{"databaseId": 30}]},
            }
        ]
        with (
            patch.object(watch, "gh_json", return_value=data["pr"]),
            patch.object(watch, "ci_status", return_value=data["ci"]),
            patch.object(watch, "review_threads", return_value=threads),
            patch.object(
                watch,
                "api_list",
                side_effect=[
                    data["comments"],
                    data["reviews"],
                    inline,
                    data["reactions"],
                ],
            ),
        ):
            collected = watch.fetch("o/r", 1)
        self.assertEqual(collected["threads"][0]["comments"], inline)
        self.assertEqual(len(collected["threads"][0]["comments"]), 207)
        for section in ("comments", "reviews", "reactions", "pr", "ci"):
            self.assertEqual(collected[section], data[section])

    def test_inconsistent_roots_or_orphan_replies_reject_snapshot(self):
        for inline, roots in (
            ([{"id": 30}], []),
            ([], [30]),
            ([{"id": 31, "in_reply_to_id": 30}], []),
            ([], [None]),
        ):
            with (
                self.subTest(inline=inline, roots=roots),
                patch.object(watch, "gh_json", return_value=snapshot()["pr"]),
                patch.object(watch, "ci_status", return_value={}),
                patch.object(
                    watch,
                    "review_threads",
                    return_value=[
                        {
                            "comments": {
                                "nodes": [{"databaseId": r}] if r else []
                            }
                        }
                        for r in roots
                    ],
                ),
                patch.object(
                    watch, "api_list", side_effect=[[], [], inline, []]
                ),
                self.assertRaises(watch.SnapshotChanged),
            ):
                watch.fetch("o/r", 1)

    def test_head_race_rejects_snapshot(self):
        before = snapshot()["pr"]
        after = {"head": {"sha": "b" * 40}}
        with (
            patch.object(watch, "gh_json", side_effect=[before, after]),
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "ci_status", return_value={}),
            patch.object(watch, "review_threads", return_value=[]),
            self.assertRaises(watch.SnapshotChanged),
        ):
            watch.fetch("o/r", 1)

    @staticmethod
    def ci_page(state, checks, more=False):
        return {
            "repository": {
                "object": {
                    "statusCheckRollup": {
                        "state": state,
                        "contexts": {
                            "nodes": checks,
                            "pageInfo": {
                                "hasNextPage": more,
                                "endCursor": "next",
                            },
                        },
                    }
                }
            }
        }

    def test_ci_retains_cancelled_run_replacement_and_authoritative_failure(
        self,
    ):
        old = {
            "id": "old",
            "name": "test",
            "status": "COMPLETED",
            "conclusion": "CANCELLED",
            "detailsUrl": "old-url",
        }
        new = {
            "id": "new",
            "name": "test",
            "status": "IN_PROGRESS",
            "conclusion": None,
            "detailsUrl": "new-url",
        }
        with patch.object(
            watch,
            "graphql",
            side_effect=[
                self.ci_page("FAILURE", [old], True),
                self.ci_page("FAILURE", [new]),
            ],
        ) as call:
            result = watch.ci_status("o/r", HEAD)
        self.assertEqual(result, {"state": "FAILURE", "contexts": [old, new]})
        self.assertEqual(call.call_args.kwargs["cursor"], "next")
        self.assertEqual(call.call_args.kwargs["sha"], HEAD)

    def test_ci_rollup_change_during_pagination_rejects_snapshot(self):
        with (
            patch.object(
                watch,
                "graphql",
                side_effect=[
                    self.ci_page("PENDING", [], True),
                    self.ci_page("SUCCESS", []),
                ],
            ),
            self.assertRaises(watch.SnapshotChanged),
        ):
            watch.ci_status("o/r", HEAD)

    def test_no_rollup_preserves_uncertainty(self):
        with patch.object(
            watch,
            "graphql",
            return_value={
                "repository": {"object": {"statusCheckRollup": None}}
            },
        ):
            self.assertEqual(
                watch.ci_status("o/r", HEAD), {"state": None, "contexts": []}
            )

    def test_graphql_partial_error_is_not_accepted_as_complete(self):
        with (
            patch.object(
                watch,
                "gh_json",
                return_value={
                    "data": {},
                    "errors": [{"message": "Unavailable"}],
                },
            ),
            self.assertRaises(watch.GhCommandError),
        ):
            watch.graphql("query {}")


class CliTests(unittest.TestCase):
    def run_cli(self, path, responses, *args, clock=None):
        with (
            patch("sys.argv", ["watch", "--state-file", str(path), *args]),
            patch("sys.stdout", io.StringIO()) as output,
            patch.object(watch, "resolve_pr", return_value=("o/r", 1)),
            patch.object(watch, "fetch", side_effect=responses),
            patch.object(watch.time, "sleep") as sleep,
            patch.object(
                watch.time, "monotonic", side_effect=clock, return_value=0
            ),
        ):
            watch.main()
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return json.loads(lines[0]), sleep.call_count

    def test_first_watch_returns_full_snapshot_and_next_watch_waits_for_change(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            before = snapshot()
            result, sleeps = self.run_cli(path, [before], "--watch")
            self.assertEqual(result["event"], "snapshot")
            self.assertEqual(sleeps, 0)
            self.assertEqual(json.loads(path.read_text()), baseline(before))
            after = copy.deepcopy(before)
            after["comments"][1]["body"] += "\nEdited status"
            result, sleeps = self.run_cli(
                path, [before, before, after], "--watch"
            )
            self.assertEqual(sleeps, 2)
            self.assertEqual(result["changed"], ["comments"])
            self.assertEqual(result["snapshot"], after)
            result, sleeps = self.run_cli(path, [after])
            self.assertEqual(result["event"], "unchanged")
            self.assertEqual(sleeps, 0)

    def test_timeout_is_not_completion_and_retains_snapshot_or_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            data = snapshot()
            watch.save_state(path, baseline(data))
            for response in (data, watch.SnapshotChanged("Head moved")):
                with self.subTest(response=type(response)):
                    result, sleeps = self.run_cli(
                        path,
                        [response],
                        "--watch",
                        "--timeout-seconds",
                        "1",
                        clock=[0, 1],
                    )
                    self.assertEqual(result["event"], "timeout")
                    self.assertEqual(sleeps, 0)
                    if isinstance(response, Exception):
                        self.assertEqual(result["reason"], "Head moved")
                        self.assertNotIn("snapshot", result)
                    else:
                        self.assertEqual(result["snapshot"], data)
                    self.assertEqual(
                        json.loads(path.read_text()), baseline(data)
                    )

    def test_inconsistent_fetch_does_not_advance_baseline_and_watch_retries(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            data = snapshot()
            watch.save_state(path, baseline(data))
            original = path.read_bytes()
            result, _ = self.run_cli(
                path, [watch.SnapshotChanged("Head moved")]
            )
            self.assertEqual(result["event"], "inconsistent")
            self.assertEqual(path.read_bytes(), original)
            after = copy.deepcopy(data)
            after["pr"]["head"]["sha"] = "b" * 40
            result, sleeps = self.run_cli(
                path, [watch.SnapshotChanged("Head moved"), after], "--watch"
            )
            self.assertTrue(result["head_changed"])
            self.assertEqual(sleeps, 1)

    def test_api_failure_leaves_previous_state_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            watch.save_state(path, baseline(snapshot()))
            original = path.read_bytes()
            with self.assertRaises(watch.GhCommandError):
                self.run_cli(path, [watch.GhCommandError("API failed")])
            self.assertEqual(path.read_bytes(), original)

    def test_old_or_wrong_pr_state_is_rejected_without_modification(self):
        for state in (
            {"acknowledged": []},
            dict(baseline(snapshot()), pr="other/repo#2"),
        ):
            with (
                self.subTest(state=state),
                tempfile.TemporaryDirectory() as tmp,
            ):
                path = Path(tmp) / "state.json"
                watch.save_state(path, state)
                original = path.read_bytes()
                with self.assertRaises(ValueError):
                    self.run_cli(path, [])
                self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
