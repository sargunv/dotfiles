# Default guidance

These are defaults. A project's own guidance overrides them.

## Pull requests

Write a short PR title and description for a reviewer who will read the diff.
Say what the diff, its doc comments, and CI can't:

- Open with the problem and what users can now do, or what maintainers gain.
- Show one small example of new API, or a bug's trigger with before and after.
- Add these only if they apply: what callers must adopt, measured numbers with a
  one-line method, and validation that CI does not run.
- Rewrite both when review changes the scope.

## AI disclosure

When you post AI-contributed GitHub content, including a new Discussion or
Issue, a reply, or a PR description or comment, append this disclosure:
`*AI-assisted — Tool: <tool>; model: <provider>/<model>*`

This section and "Pull requests" replace the description and attribution formats
in skills such as `file-pr` and `leaving-pr-comments`. Skip their "Created with"
line and 🤖 note callout. Put any block a skill places before the model line,
such as a review summary, before this disclosure.
