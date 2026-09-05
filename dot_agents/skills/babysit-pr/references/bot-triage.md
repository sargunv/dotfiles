# Bot triage

## Watch

Use `scripts/gh_pr_watch.py` from this skill with Python 3.10+ and authenticated
`gh`. It only reads GitHub; acknowledgements change local state. Run it in the
repository, using one state file per PR for the whole session:

```sh
python3 "$SKILL_DIR/scripts/gh_pr_watch.py" --pr auto \
  --state-file /tmp/babysit-OWNER-REPO-PR.json --watch
```

Set `SKILL_DIR` to this skill's directory. A PR number with `--repo OWNER/REPO`
or a GitHub PR URL also works. Omit `--watch` for one snapshot. The loop polls
every 60 seconds without model involvement and prints JSON when work appears,
review finishes, or it times out after 30 minutes. Run it as a background
command and wait for its output; don't build a separate agent polling loop.
Readiness is confirmed on a second poll to allow newly queued checks to appear.

The watcher recognizes Greptile and Codex by their bot accounts. It detects bots
from activity on this PR. Check repository configuration or recent PRs at setup;
use `--bots greptile codex` (or just the installed bot) to select exactly which
bots must finish, including bots that haven't posted yet. This selection
persists in the state file and overrides historical participation by removed
bots. Their existing findings still receive triage. Use `--bots` with no names
when neither bot is used. For other bot accounts, apply the same policy and
inspect their documented status separately.

Output includes full bot summaries, review bodies, and unresolved threads with
all replies, including outdated threads. Read summaries too: findings may exist
only there. Nothing is marked handled just because the watcher emitted it. After
handling a summary or review, acknowledge its exact `token`:

```sh
python3 "$SKILL_DIR/scripts/gh_pr_watch.py" --pr auto \
  --state-file /tmp/babysit-OWNER-REPO-PR.json --ack TOKEN [TOKEN ...]
```

Edits change the token and bring the item back. Threads disappear only when
resolved on GitHub; they cannot be acknowledged locally. Reuse the state file
after fixes and pushes. The watcher resets review freshness when the head
changes.

## Handle findings

Use one policy for every reviewer:

- Verify the claim against the code and the task's intent. Fix meaningful
  problems; reject incorrect, low-value, or out-of-scope suggestions. A cleanup
  PR may intentionally remove guidance or tests; restoring them isn't
  automatically an improvement.
- Treat findings as symptoms. Prefer a simpler design over accumulating guards,
  fallbacks, or try/catch blocks. Repeated findings in the same area are a
  signal to step back and reconsider the whole PR from first principles.
- For accepted findings, implement the fix, run relevant validation, commit and
  push, then resolve the thread. Stage only intended files.
- For rejected findings, reply with one line explaining why, then resolve the
  thread. For summary-only findings, reply on the PR and acknowledge the summary
  once every finding in it is handled. Don't silently dismiss real problems to
  obtain a clean status.

Reply to an inline thread using its root comment's numeric `id`:

```sh
gh api --method POST repos/OWNER/REPO/pulls/PR/comments/COMMENT_ID/replies \
  -f body='One-line reason.'
```

Resolve using the thread's GraphQL `id`:

```sh
gh api graphql -f query='mutation($id: ID!) {
  resolveReviewThread(input: {threadId: $id}) { thread { isResolved } }
}' -f id=THREAD_ID
```

After acting, resume the watcher. Investigate `failed_checks` and merge
conflicts as part of babysitting. On `blocked`, `timeout`, or `error`, inspect
and report the specific blocker; don't restart indefinitely or assume success.

## Completion

| Bot      | Running       | Completed                               | Clean target   |
| -------- | ------------- | --------------------------------------- | -------------- |
| Greptile | Eyes reaction | Review or thumbs-up, even with findings | 5/5 confidence |
| Codex    | Eyes reaction | Review with findings, or thumbs-up      | Thumbs-up      |

Only use results for the current head. Reviews carry a commit SHA; Greptile
summaries may carry a `Last reviewed commit` marker. PR reactions do **not**
carry a SHA. The watcher treats pre-existing reactions as unverified unless a
current review corroborates their timing; otherwise it tracks newly appearing
reaction IDs against a baseline for the current head, independent of the host
clock. Overlapping reviews can still make reactions ambiguous. Verify ambiguous
status or obtain a fresh review instead of calling it clean.

`clean` means checks passed, no conflicts or unhandled findings remain, and all
participating bots meet their clean targets. `handled` means reviews completed
and every finding was handled, but a bot's clean target is unmet. Valid
rejections can leave this result: report the score/reaction discrepancy and stop
rather than changing sound code to appease a bot. Neither result merges the PR.
Report any separate merge requirements GitHub still enforces.

The watcher is adapted from
[OpenAI's PR watcher](https://github.com/openai/codex/blob/ddf04ad26789d040f9ef6a96736f76602e35a6cc/.codex/skills/babysit-pr/scripts/gh_pr_watch.py),
with summary handling informed by
[Greptile's greploop](https://github.com/greptileai/skills/blob/main/greploop/SKILL.md).
Its Apache-2.0 license and attribution are alongside the script.
