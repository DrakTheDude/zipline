---
profile: code
for: a code repository people review: an app, a service, a library, automation
folders:
tools:
---

## Changes someone can review

The person, or their team, has to read what you change. A commit that touches forty files
can't be reviewed properly, so it gets waved through or stuck. Keep each change to one
purpose, small enough to read in one sitting. If a task needs more, say how you'd split it
before you start, and do it in pieces.

- Touch only what the task needs. No drive-by reformatting, renaming or "while I was here".
- Don't add files nobody asked for: no extra docs, examples or helper scripts unless agreed.
- Before each commit, say in a few lines what changed and why, in the person's terms.

## Run it before you say it works

"Should work" is not a result. Before you report a change as done, run the project's own
checks (tests, build, linter, whatever the repo uses) and say what they showed. If there are
none for what you changed, say that, and offer the smallest check that would have caught a
mistake.

When you add a check, show it failing once on something broken, then passing. A check that
can't fail isn't a check.

## An attempt here

An attempt is another go at the same failure: the same test still red, the same build error
after another fix. Count them against the limit in `workalong.md`. Three fixes to one error
that each break something else is a reset, not a fourth fix.
