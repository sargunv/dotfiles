---
name: babysit-pr
description: Get a PR ready to merge. Use when asked to babysit, watch, or follow a PR.
---

# Babysit PR

The PR you are doing this for is:

- If you are on a branch with a remote PR on it already, that one
- If the user includes a specific PR in their request, babysit that one

The end state here is:

- The PR doesn't have merge conflicts with the target branch
- The CI checks are green
- The AI code review bots' findings have been addressed (by either implementing
  them or rejecting them because they're not worth addressing). Aim for clean
  reviews; report any remaining score or approval discrepancy after triage.

Steps to take:

1. Watch the PR for CI and code review. For polling the review bots, fetching
   their full findings, and deciding fix-vs-skip, follow
   [references/bot-triage.md](references/bot-triage.md).
2. When issues come in, fix them locally then commit and push them up
3. Wait for the checks to run again, if there are more issues, repeat step 2,
   otherwise move on to the next step
4. Give the user a concise summary of the changes you made to fix the PR and a
   concise list of things the PR actually does

NOTE: if the user asks for an extra review from you, use a subagent to do that
review and treat it like one of the AI code reviewer bots. Take its findings and
follow the steps above.
