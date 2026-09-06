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
HUMAN = {"login": "reviewer", "type": "User"}


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
        "ci_state": "SUCCESS",
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
    def test_codex_clean_completion_comment_recognizes_existing_thumb(self):
        data = snapshot()
        data["comments"] = [
            {
                "id": 10,
                "user": CODEX,
                "updated_at": NOW,
                "html_url": "url",
                "body": "Codex Review: Didn't find any major issues. Hooray!\n\n"
                f"**Reviewed commit:** `{HEAD[:10]}`\n\n<details>About Codex</details>",
            }
        ]
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": AFTER}
        ]
        result = watch.evaluate(data, {})
        self.assertEqual(result["event"], "clean")
        self.assertEqual(result["items"], [])
        data["pr"]["head"]["sha"] = "b" * 40
        self.assertEqual(watch.evaluate(data, {})["event"], "waiting")

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

    def test_outdated_bot_threads_keep_all_replies_until_resolved(self):
        data, state = snapshot(), {}
        data["inline"] = [
            {"id": 30, "user": CODEX, "body": "Check this", "commit_id": "old"}
        ]
        data["inline"] += [
            {
                "id": 31 + n,
                "user": GREPTILE,
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
                data["ci_state"] = {
                    "pending": "PENDING",
                    "failure": "FAILURE",
                    "cancelled": "FAILURE",
                    "skipped": "SUCCESS",
                }[check_state]
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


class HumanTriageTests(unittest.TestCase):
    def thread_snapshot(self, users=(HUMAN,), resolved=False):
        data = snapshot()
        data["inline"] = [
            {
                "id": 30 + n,
                "user": user,
                "body": f"Finding or reply {n}",
                "updated_at": NOW,
                "html_url": f"https://github.com/o/r/pull/1#discussion_r{30 + n}",
                "path": "src/main.py",
                "line": 42,
                "commit_id": HEAD,
                **({"in_reply_to_id": 30} if n else {}),
            }
            for n, user in enumerate(users)
        ]
        data["threads"] = [
            {
                "id": "THREAD",
                "isResolved": resolved,
                "isOutdated": True,
                "comments": {"nodes": [{"databaseId": 30}]},
            }
        ]
        return data

    def test_human_comments_and_review_bodies_ignore_bot_selection(self):
        for expected in (None, [], ["codex"]):
            with self.subTest(expected=expected):
                data, state = snapshot(), {}
                data["comments"] = [
                    dict(summary("Please simplify this"), user=HUMAN)
                ]
                data["reviews"] = [
                    dict(
                        summary(
                            "Approved, but please remove the extra dependency"
                        ),
                        id=20,
                        user=HUMAN,
                        state="APPROVED",
                        submitted_at=BEFORE,
                        commit_id="old",
                    )
                ]
                result = watch.evaluate(data, state, expected)
                self.assertEqual(result["event"], "action_required")
                self.assertEqual(
                    [i["kind"] for i in result["items"]], ["comment", "review"]
                )
                for item in result["items"]:
                    self.assertEqual(item["author_type"], "human")
                    self.assertEqual(item["user"], HUMAN)
                    self.assertIsNone(item["bot"])
                    self.assertTrue(item["body"])
                self.assertEqual(result["items"][1]["state"], "APPROVED")
                state["acknowledged"] = state["offered"][:]
                result = watch.evaluate(data, state)
                self.assertEqual(result["items"], [])
                self.assertEqual(len(result["acknowledged_human_items"]), 2)
                self.assertEqual(
                    result["event"], "waiting" if expected else "clean"
                )
                for source in ("comments", "reviews"):
                    changed = copy.deepcopy(data)
                    changed[source][0]["body"] += " An additional request."
                    result = watch.evaluate(changed, state)
                    self.assertEqual(result["event"], "action_required")
                    self.assertEqual(len(result["items"]), 1)

    def test_human_review_state_changes_and_dismissed_bodies_are_visible(self):
        data, state = snapshot(), {}
        data["reviews"] = [
            dict(
                summary(),
                id=20,
                user=HUMAN,
                state="APPROVED",
                body="",
                submitted_at=NOW,
                commit_id=HEAD,
            )
        ]
        first = watch.evaluate(data, state)["items"][0]
        state["acknowledged"] = [first["token"]]
        for review_state in ("CHANGES_REQUESTED", "DISMISSED"):
            data["reviews"][0]["state"] = review_state
            item = watch.evaluate(data, state)["items"][0]
            self.assertEqual(item["state"], review_state)
            self.assertNotEqual(item["token"], first["token"])
        data["reviews"][0]["state"] = "PENDING"
        self.assertEqual(watch.evaluate(data, state)["items"], [])

    def test_human_and_mixed_threads_can_stay_open_after_local_triage(self):
        for users in ((HUMAN,), (CODEX, HUMAN), (HUMAN, CODEX)):
            with self.subTest(users=users):
                data, state = self.thread_snapshot(users), {}
                original = copy.deepcopy(data)
                result = watch.evaluate(data, state, [])
                item = result["items"][0]
                self.assertEqual(
                    item["author_type"], "human" if len(users) == 1 else "mixed"
                )
                self.assertEqual(
                    [c["user"] for c in item["comments"]], list(users)
                )
                self.assertEqual(item["comments"][0]["path"], "src/main.py")
                self.assertTrue(item["outdated"])
                self.assertFalse(item["resolved"])
                self.assertEqual(state["offered"], [item["token"]])
                self.assertEqual(
                    watch.evaluate(data, state)["event"], "action_required"
                )
                state["acknowledged"] = state["offered"][:]
                result = watch.evaluate(data, state)
                self.assertEqual(result["event"], "handled")
                self.assertEqual(result["items"], [])
                self.assertEqual(result["open_human_threads"], ["THREAD"])
                self.assertEqual(result["acknowledged_human_items"], [item])
                self.assertEqual(data, original)
                data["pr"]["head"]["sha"] = "b" * 40
                self.assertEqual(watch.evaluate(data, state)["items"], [])

    def test_thread_edits_and_new_replies_invalidate_acknowledgement(self):
        data, state = self.thread_snapshot((CODEX, HUMAN)), {}
        token = watch.evaluate(data, state, [])["items"][0]["token"]
        state["acknowledged"] = [token]
        for index in (0, 1):
            for field, value in (
                ("body", "Edited request"),
                ("updated_at", AFTER),
            ):
                with self.subTest(index=index, field=field):
                    changed = copy.deepcopy(data)
                    changed["inline"][index][field] = value
                    result = watch.evaluate(changed, state)
                    self.assertEqual(result["event"], "action_required")
                    self.assertNotEqual(result["items"][0]["token"], token)
                    self.assertEqual(result["acknowledged_human_items"], [])
        for user in (HUMAN, CODEX):
            changed = copy.deepcopy(data)
            changed["inline"].append(
                dict(changed["inline"][1], id=99, user=user)
            )
            result = watch.evaluate(changed, state)
            self.assertEqual(result["event"], "action_required")
            self.assertEqual(len(result["items"][0]["comments"]), 3)

    def test_human_reply_changes_bot_thread_to_human_handling(self):
        data, state = self.thread_snapshot((CODEX,)), {}
        first = watch.evaluate(data, state, [])["items"][0]
        self.assertFalse(first["can_acknowledge"])
        self.assertEqual(state["offered"], [])
        data["inline"].append(
            dict(data["inline"][0], id=31, user=HUMAN, in_reply_to_id=30)
        )
        item = watch.evaluate(data, state)["items"][0]
        self.assertEqual(item["author_type"], "mixed")
        self.assertNotEqual(item["token"], first["token"])
        self.assertEqual(state["offered"], [item["token"]])

    def test_resolved_human_threads_and_later_replies_remain_visible(self):
        data, state = (
            self.thread_snapshot((CODEX,) + (HUMAN,) * 110, resolved=True),
            {},
        )
        item = watch.evaluate(data, state, [])["items"][0]
        self.assertTrue(item["resolved"])
        self.assertEqual(len(item["comments"]), 111)
        state["acknowledged"] = [item["token"]]
        self.assertEqual(watch.evaluate(data, state)["event"], "clean")
        data["inline"][-1]["body"] = "New substantive request"
        self.assertEqual(
            watch.evaluate(data, state)["event"], "action_required"
        )
        data["threads"][0]["isResolved"] = False
        result = watch.evaluate(data, state)
        self.assertEqual(result["open_human_threads"], ["THREAD"])
        self.assertNotEqual(result["items"][0]["token"], item["token"])

    def test_unrecognized_authors_are_surfaced_with_conservative_policy(self):
        for user, authors in (
            (None, "human"),
            ({"login": "other[bot]"}, "bot"),
            ({"login": "app", "type": "Bot"}, "bot"),
        ):
            with self.subTest(user=user):
                data = self.thread_snapshot((user,))
                data["comments"] = [dict(summary(), user=user)]
                result = watch.evaluate(data, {})
                self.assertEqual(len(result["items"]), 2)
                self.assertEqual(result["bots"], {})
                for item in result["items"]:
                    self.assertEqual(item["author_type"], authors)

    def test_acknowledged_humans_do_not_bypass_ci_or_bot_freshness(self):
        data, state = self.thread_snapshot(), {}
        state["acknowledged"] = [
            watch.evaluate(data, state, ["codex"])["items"][0]["token"]
        ]
        self.assertEqual(watch.evaluate(data, state)["event"], "waiting")
        data["reactions"] = [
            {"id": 1, "user": CODEX, "content": "+1", "created_at": AFTER}
        ]
        self.assertEqual(watch.evaluate(data, state)["event"], "handled")
        data["pr"]["head"]["sha"] = "b" * 40
        self.assertEqual(watch.evaluate(data, state)["event"], "waiting")
        for ci_state, event in (
            ("FAILURE", "action_required"),
            ("PENDING", "waiting"),
        ):
            data["ci_state"] = ci_state
            self.assertEqual(watch.evaluate(data, state, [])["event"], event)
        data["ci_state"] = "SUCCESS"
        data["pr"]["mergeable_state"] = "blocked"
        self.assertEqual(watch.evaluate(data, state)["event"], "blocked")

    def test_cli_local_ack_and_watch_recheck_open_human_threads(self):
        for new_reply in (False, True):
            with (
                self.subTest(new_reply=new_reply),
                tempfile.TemporaryDirectory() as tmp,
            ):
                data, state = self.thread_snapshot(), {}
                token = watch.evaluate(data, state)["items"][0]["token"]
                path = Path(tmp) / "state.json"
                watch.save_state(path, state)
                args = ["watch", "--state-file", str(path)]
                later = copy.deepcopy(data)
                if new_reply:
                    later["inline"].append(
                        dict(later["inline"][0], id=31, in_reply_to_id=30)
                    )
                with (
                    patch("sys.stdout", io.StringIO()) as output,
                    patch.object(watch, "resolve_pr", return_value=("o/r", 1)),
                    patch.object(
                        watch,
                        "gh_text",
                        side_effect=AssertionError("Unexpected GitHub call"),
                    ),
                    patch.object(
                        watch, "fetch", side_effect=[data, later]
                    ) as fetch,
                    patch.object(watch.time, "sleep") as sleep,
                ):
                    with patch("sys.argv", args + ["--ack", token]):
                        watch.main()
                    fetch.assert_not_called()
                    self.assertEqual(
                        json.loads(output.getvalue())["event"], "acknowledged"
                    )
                    output.seek(0)
                    output.truncate()
                    with patch("sys.argv", args + ["--watch"]):
                        watch.main()
                    self.assertEqual(sleep.call_count, 1)
                    self.assertEqual(len(output.getvalue().splitlines()), 1)
                    result = json.loads(output.getvalue())
                    self.assertEqual(
                        result["event"],
                        "action_required" if new_reply else "handled",
                    )
                    self.assertEqual(result["open_human_threads"], ["THREAD"])
                    if new_reply:
                        self.assertNotEqual(result["items"][0]["token"], token)
                        with (
                            patch("sys.argv", args + ["--ack", token]),
                            self.assertRaises(ValueError),
                        ):
                            watch.main()
                    else:
                        self.assertEqual(result["items"], [])
                        self.assertEqual(
                            result["acknowledged_human_items"][0]["token"],
                            token,
                        )


class ApiTests(unittest.TestCase):
    def test_ci_rollup_preserves_duplicate_names_across_pages(self):
        def page(run_id, conclusion, more):
            return {
                "repository": {
                    "object": {
                        "statusCheckRollup": {
                            "state": "FAILURE",
                            "contexts": {
                                "nodes": [
                                    {
                                        "id": run_id,
                                        "name": "test",
                                        "detailsUrl": "url",
                                        "status": "COMPLETED",
                                        "conclusion": conclusion,
                                    }
                                ],
                                "pageInfo": {
                                    "hasNextPage": more,
                                    "endCursor": "next",
                                },
                            },
                        }
                    }
                }
            }

        with patch.object(
            watch,
            "graphql",
            side_effect=[
                page("a", "FAILURE", True),
                page("b", "SUCCESS", False),
            ],
        ) as call:
            ci_state, checks = watch.ci_status("o/r", HEAD)
        self.assertEqual(call.call_args.kwargs["cursor"], "next")
        self.assertEqual([c["id"] for c in checks], ["a", "b"])
        data = dict(snapshot(), ci_state=ci_state, checks=checks)
        result = watch.evaluate(data, {})
        self.assertEqual(result["event"], "action_required")
        self.assertEqual(len(result["failed_checks"]), 1)

    def test_ci_readiness_uses_server_rollup_instead_of_reaggregating_attempts(
        self,
    ):
        for ci_state, event in [
            ("FAILURE", "action_required"),
            ("ERROR", "action_required"),
            ("EXPECTED", "waiting"),
            ("PENDING", "waiting"),
            ("SUCCESS", "clean"),
            (None, "clean"),
        ]:
            with self.subTest(ci_state=ci_state):
                data = snapshot()
                data["ci_state"] = ci_state
                data["checks"][0]["state"] = "failure"
                result = watch.evaluate(data, {})
                self.assertEqual(result["event"], event)
                if event == "clean":
                    self.assertEqual(result["failed_checks"], [])

    def test_null_ci_rollup_means_no_reported_checks(self):
        with patch.object(
            watch,
            "graphql",
            return_value={
                "repository": {"object": {"statusCheckRollup": None}}
            },
        ):
            self.assertEqual(watch.ci_status("o/r", HEAD), (None, []))

    def test_new_inline_root_without_thread_discards_incomplete_snapshot(self):
        with (
            patch.object(
                watch,
                "gh_json",
                return_value=snapshot()["pr"],
            ),
            patch.object(
                watch,
                "api_list",
                side_effect=[[], [], [{"id": 30, "user": GREPTILE}], []],
            ),
            patch.object(watch, "ci_status", return_value=(None, [])),
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
                return_value=snapshot()["pr"],
            ),
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "ci_status", return_value=(None, [])),
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
                side_effect=[before, after],
            ),
            patch.object(watch, "api_list", return_value=[]),
            patch.object(watch, "ci_status", return_value=(None, [])),
            patch.object(watch, "review_threads", return_value=[]),
        ):
            self.assertIsNone(watch.fetch("o/r", 1))

    def test_watch_is_quiet_until_ci_failure(self):
        pending, failed = snapshot(), snapshot()
        pending["checks"][0]["state"] = "pending"
        pending["ci_state"] = "PENDING"
        failed["checks"][0]["state"] = "failure"
        failed["ci_state"] = "FAILURE"
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
        pending["ci_state"] = "PENDING"
        failed["checks"][0]["state"] = "failure"
        failed["ci_state"] = "FAILURE"
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
