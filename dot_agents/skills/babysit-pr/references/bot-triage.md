# Human and bot review triage

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
CI readiness uses GitHub's combined check/status rollup for the captured head;
individual check results provide diagnostics, without deduplicating job names or
reconstructing rerun history locally.

The watcher recognizes Greptile and Codex by their bot accounts. It detects bots
from activity on this PR. Check repository configuration or recent PRs at setup;
use `--bots greptile codex` (or just the installed bot) to select exactly which
bots must finish, including bots that haven't posted yet. This selection
persists in the state file and overrides historical participation by removed
bots. Their existing findings still receive triage. Use `--bots` with no names
when neither bot is used. This selects readiness requirements, never which
comments are visible. Other bot accounts are surfaced as bots; inspect their
review status separately because the watcher only tracks Greptile/Codex
freshness.

Output includes PR comments, published review bodies/states, and inline threads
with all replies and author/location metadata. Read bodies even in approvals:
findings may exist only there. Human items include dismissed reviews and
resolved or outdated threads, so later edits and replies remain visible.

`author_type` is `human`, `bot`, or `mixed`; both `human` and `mixed` follow the
human policy in [SKILL.md](../SKILL.md). Unknown/deleted authors receive human
handling. The `bot` field only identifies a recognized bot in the item.

After triaging every finding and reporting human outcomes to the user,
acknowledge items with `can_acknowledge: true` using their exact `token`:

```sh
python3 "$SKILL_DIR/scripts/gh_pr_watch.py" --pr auto \
  --state-file /tmp/babysit-OWNER-REPO-PR.json --ack TOKEN [TOKEN ...]
```

Acknowledgement is local triage, not GitHub resolution or human approval. Human
and mixed threads can remain open; bot-only threads require GitHub resolution.
`acknowledged_human_items` retains acknowledged content for reporting, and
`open_human_threads` lists currently open human/mixed thread IDs.

Do not acknowledge substantive human requests awaiting the user's decision,
including ambiguous, disputed, or out-of-scope requests. Informational comments
and approvals need no code change but still need to be read and reported.

Edits, new replies from any author, and review/thread state changes produce new
tokens and resurface items. Reuse the state file after pushes: unchanged human
acknowledgements persist, while bot review freshness resets for the new head.

## Bot findings

Apply this policy only to bot items and bot-only threads:

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

Re-fetch the full thread before replying or resolving; any human contribution
makes it subject to the human policy.

Reply to a bot-only inline thread using its root comment's numeric `id`:

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

Codex automatically re-reviews on push. Wait for that review; don't also post
`@codex review`. Only request a manual review when explicitly asked or when you
have verified that automatic review is disabled, and never while a review is
already running.

## Completion

| Bot      | Running       | Completed                               | Clean target   |
| -------- | ------------- | --------------------------------------- | -------------- |
| Greptile | Eyes reaction | Review or thumbs-up, even with findings | 5/5 confidence |
| Codex    | Eyes reaction | Review with findings, or thumbs-up      | Thumbs-up      |

Only use results for the current head. Reviews carry a commit SHA; Greptile
summaries may carry a `Last reviewed commit` marker, and Codex completion
comments carry `Reviewed commit`. PR reactions do **not** carry a SHA. The
watcher treats pre-existing reactions as unverified unless a current review
corroborates their timing; otherwise it tracks newly appearing reaction IDs
against a baseline for the current head, independent of the host clock.
Overlapping reviews can still make reactions ambiguous. Verify ambiguous status
or obtain a fresh review instead of calling it clean.

`clean` and `handled` both require passing checks, no conflicts, completed
required bot reviews, and all items triaged. `handled` means a bot's clean
target is unmet or acknowledged human threads remain open; `clean` means neither
condition remains. Report open human threads and any score/reaction discrepancy
and stop, rather than polling forever or changing sound code to appease a bot.

Neither result merges the PR or establishes human approval. GitHub merge
requirements still apply: report `blocked` requirements such as human approval
or conversation resolution without resolving human threads to clear them.

The watcher is adapted from
[OpenAI's PR watcher](https://github.com/openai/codex/blob/ddf04ad26789d040f9ef6a96736f76602e35a6cc/.codex/skills/babysit-pr/scripts/gh_pr_watch.py),
with summary handling informed by
[Greptile's greploop](https://github.com/greptileai/skills/blob/main/greploop/SKILL.md).
Its Apache-2.0 license and attribution are alongside the script.
