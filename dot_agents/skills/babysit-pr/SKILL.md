---
name: babysit-pr
description: Get a PR ready to merge. Use when asked to babysit, watch, or follow a PR.
---

# Babysit PR

Use the PR specified by the user, or the current branch's PR if none is
specified. Watch CI and review activity, fix accepted findings, validate, then
commit and push only intended changes. Repeat while there is actionable work or
active checks/reviews to follow. Do not merge unless asked.

Use [references/bot-triage.md](references/bot-triage.md) for the read-only
watcher, review handling, and completion evidence. The watcher collects GitHub
facts and arbitrary review content; it does not decide whether findings are
handled or the PR is ready.

Read and report human comments, review bodies, and full inline threads. Fix
human findings when the intended change is clear and unambiguous; ask the user
about ambiguous substantive requests. Never reply to human comments or resolve
human threads automatically, even after fixing them. Any thread with a human
contribution follows this policy. Unknown or deleted authors receive human
handling.

Finish with a concise summary of what the PR does, your fixes and validation,
current CI and merge requirements, and remaining findings or user decisions with
links. Distinguish observed review activity from assumptions: bots decide when
to review, and a new commit does not universally require fresh bot approval.

If the user asks for an extra review from you, use a subagent and triage its
findings like bot findings.
