# The work ledger

Which worktree, branch and worker belongs to which topic, and how far it got, lives in `work/<topic>/state.md`. When a session disappears, or you come back after doing something else, this file is how the work resumes and how orphaned resources are found.

Only the main session writes it. Workers report; the main session transcribes.

## Single-session work keeps state too

- **When:** anything that will not finish in one answer. A single question answered and done needs no ledger.
- **Updating:** on start, whenever the stage or the next action changes, and at the end. If the conversation changes topic, write the state of what you were doing *before* answering about anything else.
- **Content:** stage, next action, whether you are waiting on the user, and a log. If you edited code, record path, branch and uncommitted changes in the checkout table. Drop tables you are not using.
- **Keep facts current.** Do not just append log lines — fix the stale statements above them at the same time ("not read yet", "could not read", and so on).
- **Resuming:** when the user asks "where were we", read `python3 scripts/ledger-status.py` and that `state.md` before answering.

## Work not started yet

Capture ideas and future/deferred tasks in `work/inbox.md`, including a short summary, date and source. A topic folder is not required just to remember something. Capturing is not implementation approval.

When the user starts that work, create or reuse its `state.md` and link it from the inbox item. Keep detailed progress in that ledger; update only the index status in the inbox. A closed ledger can mean explicitly deferred work, so do not infer that the inbox item is done. Read the inbox separately from `ledger-status.py` at startup and reconcile relevant items at wrap-up.

## When to write

| Point | What goes in |
|---|---|
| Before starting | A row *before* `worker-start`. State `planned`, expected path, base commit |
| Just after starting | The real branch, Run and dispatch. State `working` |
| In between | When the stage or next action changes, when a worker stalls or asks, before moving to other work |
| The user directs or corrects | In the same turn, before answering: what they said and what changes because of it |
| Done | On `worker_done`: last commit and the main session's verification result. State `done` |
| After orchestration | What was adopted and dropped, workers released, what was put on the user's checkout, what needs tidying. Reasons go in `decision.md` |
| Tidying | Rows you removed become state `deleted`. When everything is finished, stage `closed` |

Write before you create the resource. If creation fails, the record is what lets you find the orphan.

Put `<topic> <description>` in the Orca worktree's `--comment` so it is identifiable in the Orca UI too.

## Format

```markdown
# <topic>

- stage: brief | working | verifying | user review | awaiting cleanup | closed
- next: <one line, so the next session can act immediately>
- waiting on user: no | <the question>
- session: <agent> <session id> `<absolute path of the start folder>`
- updated: YYYY-MM-DD HH:MM

## Workers

| repo | role | path | branch | base | last commit | run | dispatch | state |
|---|---|---|---|---|---|---|---|---|

## User checkouts

| path | branch | original state | what was applied | how to undo | state |
|---|---|---|---|---|---|

## Other resources

| path | what it is | state |
|---|---|---|

## Log

- YYYY-MM-DD HH:MM point: what happened
```

**The field and column names are English even when you are answering the user in another language.** `ledger-status.py` matches on them literally, so a ledger with translated labels reconciles against nothing and reports `?` for every field. Write the *values* in whatever language you are speaking — `- next: 통합 테스트 실행` is correct, `- 다음 할 일: ...` is not.

Paths are absolute and wrapped in backticks — `ledger-status.py` matches on that. Worker state is one of `planned`, `working`, `done`, `adopted`, `dropped`, `awaiting cleanup`, `deleted`.

The column names `path`, `state`, `last commit`, `run` and `dispatch` are what the script reads. Rename them and the reconciliation goes quiet, which is worse than noisy.

State `working` is a claim the script checks: it asks Orca whether that dispatch still exists. Orca answers an unknown run with an empty list rather than an error, so without the dispatch id a stale run reads as "all clear".

## The check

Run it when you start a session, when you pick work back up, and before tidying. It only reads.

```text
python3 scripts/ledger-status.py
```

| Output | Meaning | What to do |
|---|---|---|
| open | Topics whose stage is not `closed` | Continue from `next` |
| unlisted worktrees | An Orca worktree in no ledger | Do not delete it. Ask the user |
| ledger mismatch | A path or commit differs from the ledger | Check reality, then fix the ledger |
| unreleased workers | A worker that is not `released` | Release finished ones. Ask about `user_takeover` |

## What may be deleted

Only resources the user has told you to remove *and* that the ledger marks `awaiting cleanup`. Unlisted worktrees and workers the user took over are never deleted without asking. Check for uncommitted changes first. Keep the session id in the ledger: deleting a worktree leaves the transcript findable through `orca search`, but the way back into it from the Orca list is gone.
