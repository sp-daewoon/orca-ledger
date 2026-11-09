---
name: orca-hq-ledger
description: Keep and reconcile the work ledger of an orca-hq workspace — work/<topic>/state.md tracking stage, next action, worktrees, branches, Orca runs, dispatches and workers — and find orphaned resources by comparing it against the real worktrees and Orca workers. Use before spawning an Orca worker or creating a worktree, when a task spans more than one reply, when the user asks "where were we" or what is still running, when tidying up after work, or when worktrees and workers have piled up and it is unclear which belong to what.
---

# The work ledger

One file per topic: `work/<topic>/state.md`. It is how work survives a session ending, and how resources that nobody owns get found.

Only the main session writes it. Workers report; the main session transcribes.

## Write it before you create anything

Before `worker-start`, before `worktree create`, write the row with state `planned`, the expected path and the base commit. If creation then fails, you still have a record pointing at whatever it left behind. This ordering is the whole point — a ledger written afterwards misses exactly the cases you need it for.

## The format

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

Drop tables you are not using. Worker state is one of `planned`, `working`, `done`, `adopted`, `dropped`, `awaiting cleanup`, `deleted`.

Two mechanical rules, because a script reads this file:

- **Paths are absolute and in backticks.** The reconciliation matches on that.
- **Do not rename the `path`, `state`, `last commit`, `run` and `dispatch` columns.** Renamed columns make the check go quiet, which is worse than noisy.
- **Fill in `dispatch` whenever you set state `working`.** Orca answers a run it does not know with an empty worker list, not an error, so a stale run id with no dispatch to check reads as "all clear".

## Keep it honest

Do not only append to the log. When you add a line, fix the stale statements above it too — a `next` that is already done, a "not read yet" that you have since read. A ledger that contradicts itself gets ignored, and then it is worse than nothing.

## Reconcile

```text
python3 scripts/hq-status.py
```

Run it when you start a session, when you pick work back up, and before tidying.

| Output | Meaning | What to do |
|---|---|---|
| alert | A credential expiry within 14 days | Tell the user to renew it |
| open | Topics not yet `closed` | Continue from `next` |
| sessions | Which session owns which topic | Point the ledger at yourself if it is wrong |
| unlisted worktrees | An Orca worktree in no ledger | **Ask the user. Do not delete it.** It may be theirs |
| ledger mismatch | Path or commit differs from reality | Check reality, then fix the ledger |
| unreleased workers | A worker that is not `released` | Release finished ones. Ask about `user_takeover` |

The script only reads. Deleting is a separate, explicit decision: only resources the user told you to remove *and* that the ledger marks `awaiting cleanup`. Check for uncommitted changes first.

## What usually goes wrong

- **A worker that says it is live but is not.** `liveness: live` only means the process exists. A worker stopped by a model capacity error never sends `worker_done`. Read its terminal (`orca terminal read --terminal <handle> --limit 20`) before concluding anything, and resume it with `orca terminal send` rather than starting a second one.
- **A branch locked out everywhere.** One branch checks out in one worktree per clone. A forgotten worktree is why a branch "cannot be checked out".
- **Orphans with no record.** Almost always a resource created before its ledger row. See the first rule.
