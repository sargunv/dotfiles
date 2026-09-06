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
- Human comments, review bodies, and inline threads have been read and reported.
  Fix human findings only when the intended change is clear and unambiguous. Ask
  the user about ambiguous substantive requests. Never reply to human comments
  or mark human threads resolved on GitHub, even after fixing them. Any thread
  containing a human contribution follows this stricter policy.

Steps to take:

1. Watch the PR for CI and code review. For polling all review activity and
   handling human and bot findings under their separate policies, follow
   [references/bot-triage.md](references/bot-triage.md).
2. Fix accepted findings locally, validate, then commit and push.
3. Wait for the checks to run again, if there are more issues, repeat step 2,
   otherwise move on to the next step
4. Give the user a concise summary of the changes you made to fix the PR and a
   concise list of things the PR actually does. Identify human findings you
   addressed and those needing the user's decision, with links.

NOTE: if the user asks for an extra review from you, use a subagent to do that
review and treat it like one of the AI code reviewer bots. Take its findings and
follow the steps above.
