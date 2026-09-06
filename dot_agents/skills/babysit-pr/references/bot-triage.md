# Human and bot review triage

## Collect activity

Run `scripts/gh_pr_watch.py` with Python 3.10+ and authenticated `gh`. Set
`SKILL_DIR` to this skill's directory. Use one new state file per PR and
watching session; a PR number with `--repo OWNER/REPO`, a GitHub PR URL, or
`--pr auto` in the repository works:

```sh
python3 "$SKILL_DIR/scripts/gh_pr_watch.py" --pr auto \
  --state-file /tmp/babysit-OWNER-REPO-PR-v2.json
```

Read the snapshot, handle actionable work, then wait for changes:

```sh
python3 "$SKILL_DIR/scripts/gh_pr_watch.py" --pr auto \
  --state-file /tmp/babysit-OWNER-REPO-PR-v2.json --watch
```

The watcher only reads GitHub and writes its own local state file. It returns
one JSON object. Without `--watch`, it returns immediately. With `--watch`, the
first run returns immediately; subsequent runs poll every 60 seconds until any
collected section changes or 30 minutes elapse. `--poll-seconds` and
`--timeout-seconds` override those intervals. Run the wait in the background and
wait for output instead of building another agent polling loop.

Output contains:

- `event`: `snapshot` on first observation, `changed`, `unchanged` for a single
  unchanged poll, or `timeout`. None means approved, handled, or ready.
- `changed`: section names differing from the last returned snapshot;
  `head_changed` flags a different head since that snapshot.
- `snapshot.pr`: the full REST PR object, including head/base SHAs, draft/state,
  requested reviewers, labels, and mergeability fields.
- `snapshot.ci`: GitHub's `statusCheckRollup.state` for the captured head and
  all paginated contexts, preserving check identities, statuses, conclusions,
  URLs, and workflow/app metadata. Null means no reported rollup, not passing
  checks.
- `snapshot.comments` and `snapshot.reviews`: full REST issue comments and
  review records, including bodies in approvals and dismissed reviews, authors,
  review states, timestamps, URLs, and review commit IDs.
- `snapshot.threads`: all paginated review threads, including resolved/outdated
  state, with full REST inline comments in `comments`, including every reply and
  its author, body, location, and commit metadata.
- `snapshot.reactions`: all PR issue reactions as evidence, without interpreting
  their meaning or associating them with a commit.

Every successful output includes the full snapshot, including unchanged items.
No prose or author is filtered. Edits, replies, deletions, review/thread state
changes, CI changes, and head changes can wake the watcher. The state file
stores only delivery fingerprints and PR/head identity. Keep outstanding
findings and user decisions in your session notes: seeing an item once does not
handle it. There is no `--ack`, `--bots`, bot completion state, or readiness
event. Old state files are rejected; use a new path instead of overwriting
another session's state.

GitHub reads are not transactional. Head changes and mismatched thread roots
cause an `inconsistent` result with a reason and no snapshot, or a retry in
watch mode. A timeout after an inconsistent fetch has a reason instead of a
snapshot; otherwise it includes the latest unchanged snapshot. API errors exit
nonzero with an `error` JSON object on stderr. Incomplete fetches never replace
the baseline. Re-fetch before acting; a quiet interval does not prove no
activity is in flight, and edits between polls cannot be recovered as historical
versions.

## Triage findings

Read arbitrary review prose, including HTML tables and Markdown links, without
assuming a particular bot's format. Reviews can contain findings even when their
state says approved or dismissed. Read resolved and outdated threads too: edits
and later replies can introduce new requests.

Apply human handling from [SKILL.md](../SKILL.md) unless GitHub identifies an
author as a bot. Unknown/deleted identities receive human handling. Any human
contribution makes the whole thread subject to human handling. Report ambiguous,
disputed, or out-of-scope substantive human requests for the user's decision.

For bot findings, verify the claim against the code and task intent. Fix
meaningful problems; reject incorrect, low-value, or out-of-scope suggestions.
Prefer addressing a shared cause over adding workarounds for repeated symptoms.
Stage only intended files, validate, commit and push accepted fixes.

Replying or resolving on GitHub requires authorization from the user/session.
When authorized, explain rejected bot findings concisely and resolve bot-only
threads after triage. Re-fetch the full thread immediately before either action;
a human contribution invokes the stricter policy. Local triage and GitHub thread
resolution are separate facts. For summary-only findings, track each outcome
without treating a summary's score or wording as a demand for code changes.

## Assess completion

Use GitHub's head rollup as the authoritative CI status. Preserve a failure
while a replacement workflow runs, even if a cancelled older job shares its
name. Inspect individual contexts and linked workflow runs for diagnosis; do not
deduplicate job names to manufacture success. Check merge conflicts and actual
repository requirements separately, including required checks, approvals, draft
status, and conversation resolution. Report unknown or blocked requirements
explicitly; never resolve human threads to clear a merge gate.

Inspect review evidence for what was reviewed and whether work is currently
running. Review commit IDs, full linked commits in summaries, and activity
tables can establish scope. A reaction alone has no head SHA. Do not relabel an
old approval as approval of the latest head, or infer completion from silence.

Bots, including Codex, decide when to review or re-review. Do not assume every
push triggers a review, require fresh bot approval after every commit, or infer
that automatic review is disabled when no new review appears. A bot choosing not
to re-review is not itself a blocker. Follow actual repository requirements and
the user's instructions. Do not request a manual review unless authorized, and
respect a declined request without asking again because another push occurred.

Finish when actionable findings are triaged, relevant validation and CI are
satisfactory, and merge requirements are understood. Report what each observed
review covered, any active review, unresolved human threads, and remaining
uncertainty or decisions. If checks/reviews are still running, continue watching
within the task's scope. On timeouts or errors, inspect and report the specific
condition instead of restarting indefinitely. Scores, thumbs-up reactions, and
absence of a new review are evidence to interpret, not universal completion
gates.

The watcher is adapted from
[OpenAI's PR watcher](https://github.com/openai/codex/blob/ddf04ad26789d040f9ef6a96736f76602e35a6cc/.codex/skills/babysit-pr/scripts/gh_pr_watch.py).
Its Apache-2.0 license and attribution are alongside the script.
