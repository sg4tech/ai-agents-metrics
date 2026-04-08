# Late Commit Recovery Retrospective

## Situation

While working on the product framing cleanup, I changed repository files and initially left the work uncommitted.

The user correctly called out that, in this repository, file changes should be followed through to commit instead of being left as an intermediate checkpoint.

## What Happened

- I updated the framing docs and several related hypothesis/spec files.
- I treated the work as complete too early and answered as if the checkpoint was already safely closed.
- The repository then still had uncommitted changes, which meant the work was not actually finished by the repo's own standards.
- I had to come back, verify the remaining diffs, and create follow-up commits to restore a clean state.

## Root Cause

The root cause was a process lapse on my side:

- I handled the document edits and the commit step as separate concerns.
- I let the chat response move ahead of the repository state.
- I did not respect the local rule that file edits should be fully committed before calling the work done.

## Retrospective

This is a small but useful failure mode because it is easy to repeat in long editing sessions.

The right default in this repository is:

- if I edit files, I finish the checkpoint with a commit
- if the commit fails, I repair the diff before claiming completion
- if the work spans multiple small fixes, I still close the tree cleanly instead of leaving partial state behind

## Conclusions

- The mistake was not about product framing itself.
- The mistake was leaving the work in an intermediate, uncommitted state.
- The user was right to call that out.
- The correct repo habit is to treat the commit as part of the done definition, not as an optional follow-up.

## Permanent Changes

- Classification:
  - retrospective only
  - process reminder
  - no code change required
- I should not report file-edit work as finished until the tree is committed and clean.
- If a commit is delayed by lint or formatting, I should repair and retry immediately rather than leaving the checkpoint open.
