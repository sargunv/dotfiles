---
name: babysit
description: >-
  Keep a PR merge-ready by triaging comments, resolving clear conflicts, and
  fixing CI in a loop.
---

# Babysit PR

Your job is to get this PR to a merge-ready state.

Check PR status, comments, and latest CI and resolve any issues until the PR is
ready to merge.

1. Merge conflicts: Intelligently resolve any merge conflicts, preserving the
   intent and correctness of changes on your branch and the base branch. If
   intents conflict, abort the merge and ask for clarification.
2. Comments: Review active unresolved comments (including automated review bots
   such as Bugbot, Greptile, CodeRabbit, Codex, and Gemini) and resolve change
   requests / bug reports where valid. When fetching GitHub comments, filter out
   resolved threads first. Read only each comment body and the minimum
   location/URL needed to act on it; do not read the entire JSON output or other
   unnecessary payload data. Carefully validate issues reported by automated
   review bots and only take action on those that are valid; explain when you
   disagree or are unsure.
3. CI: Fix CI issues caused by changes within this PR's scope. Never change CI
   checks/workflows just to make failures pass, or make unrelated code changes;
   if that would be required, report back instead. For merge-blocking failures
   that seem unrelated to this PR, check whether the branch is behind the base
   branch and merge latest changes, since another PR may have fixed them. Push
   scoped fixes and re-watch CI until mergeable + green + comments triaged.

Repeat in a loop until the PR is merge-ready. Between each iteration, sleep for
a reasonable time; 5 minutes is a good default.

## Special Notes

- Most reviewers, including bots, mark their own comments as resolved when they
  have been addressed. Do not manually mark comments as resolved. EXCEPTION:
  Codex does not automatically resolve comments when they are addressed. When
  you resolve them, mark them as resolved manually.
- When operating on a pull request in one of the following repositories, you may
  respond to comments with a justification when rejecting them. Only respond to
  bots; never respond to human reviewers. Keep your response to one line, and
  sign it with your agent harness name (e.g., Codex, Cursor, OpenCode, etc).
  - github.com/sargunv/*
  - github.com/maplibre/maplibre-native-ffi
  - github.com/maplibre/maplibre-compose
- When operating on a pull request in any other repository, NEVER respond to
  comments on the PR. Instead, log any justifications and feedback to an
  uncommitted babysit.md file in the local repo for the user to review.
- Some reviews leave actionable feedback as top level comments rather than
  inline comments. Some bots (Greptile) also edit their previous top level
  comments with the latest review status rather than posting new ones. Always
  check top level comments on each iteration.
