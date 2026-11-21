---
name: orca-ledger-reconcile
description: Keep and reconcile the work ledger of an orca-ledger workspace — per-topic state.md files tracking stage, next action, worktrees, branches, Orca runs, dispatches and workers — and find orphaned resources by comparing it against the real worktrees and Orca workers. Use before spawning an Orca worker or creating a worktree, when a task spans more than one reply, when the user asks "where were we" or what is still running, when tidying up after work, or when worktrees and workers have piled up and it is unclear which belong to what.
---

# The work ledger

One folder per topic: `work/<topic>/` or, grouped by domain, `work/<domain>/<topic>/`. It holds `state.md` (the current state — small, rewritten), `log.md` (append-only history) and `decisions.md` (what was decided and why). It is how work survives a session ending, and how resources that nobody owns get found. Closed topics older than 30 days move to `work/_archive/`.

Only the ledger's `owner` rewrites `state.md`; everyone else appends to `log.md`. Workers report; the owner transcribes. By default the owner is the topic's session. In the optional operator model a single operator agent owns every ledger (`owner: operator`) and a delegated session owns one only for its task, then hands it back.

## Write it before you create anything

Before `worker-start`, before `worktree create`, write the row with state `planned`, the expected path and the base commit. If creation then fails, you still have a record pointing at whatever it left behind. This ordering is the whole point — a ledger written afterwards misses exactly the cases you need it for.

## The format

```markdown
---
id: <topic>
domain: <domain>            # optional
stage: brief                # brief | working | verifying | user-review | waiting-external | done | closed
next: <one line, so the next session can act immediately>
waiting_on: none            # none | user: <question> | external: <who or what>
owner: operator             # operator | <agent>:<session id>
repos: [<repo>]
updated: YYYY-MM-DD HH:MM
verified_at:                # last verification by the owner, or empty
---

# <topic>

<two or three lines of context; history goes in log.md>

## Workers

| repo | role | path | branch | base | last commit | run | dispatch | state |
|---|---|---|---|---|---|---|---|---|

## User checkouts

| path | branch | original state | what was applied | how to undo | state |
|---|---|---|---|---|---|

## Other resources

| path | what it is | state |
|---|---|---|
```

`stage` is one of the seven words, never free text. `next` is never empty or `?` while the topic is open. Full field meanings: the workspace's `playbooks/work-state.md`. Ledgers with the v1 `- stage:` bullet header are still read; the lint asks for them to be migrated.

Drop tables you are not using. Worker state is one of `planned`, `working`, `done`, `adopted`, `dropped`, `awaiting cleanup`, `deleted`.

Mechanical rules, because scripts read this file:

- **The field and column names stay English, in every language.** If you are answering the user in Korean, write `next: 통합 테스트 실행`, never `다음 할 일:`. The scripts match the keys literally; translate them and every field reads back as `?` while the reconciliation silently finds nothing. Values are yours to write in any language.

- **Paths are absolute and in backticks.** The reconciliation matches on that.
- **Do not rename the `path`, `state`, `last commit`, `run` and `dispatch` columns.** Renamed columns make the check go quiet, which is worse than noisy.
- **Fill in `dispatch` whenever you set state `working`.** Orca answers a run it does not know with an empty worker list, not an error, so a stale run id with no dispatch to check reads as "all clear".

## Keep it honest

`state.md` is rewritten, not appended to. When something happens, put it in `log.md` and fix the stale statements in `state.md` — a `next` that is already done, a "not read yet" that you have since read. A ledger that contradicts itself gets ignored, and then it is worse than nothing.

## Reconcile

```text
python3 scripts/ledger-status.py   # includes ledger-lint
python3 scripts/ledger-lint.py     # lint alone; exits 1 on errors
```

Run it when you start a session, when you pick work back up, and before tidying.

| Output | Meaning | What to do |
|---|---|---|
| alert | A credential expiry within 14 days | Tell the user to renew it |
| open | Topics not yet `closed` | Continue from `next` |
| sessions | Each topic's `owner` | Point `owner` at yourself if you are taking it over |
| lint | Bad frontmatter or stage, empty `next`, `confirmed` facts whose `checked_at` is over 30 days old, dead paths, a `state.md` over 4 KB, closed topics not archived | Fix errors now. Re-read stale facts and update `checked_at`, or downgrade them to `assumed` |
| unlisted worktrees | An Orca worktree in no ledger | **Ask the user. Do not delete it.** It may be theirs |
| ledger mismatch | Path or commit differs from reality | Check reality, then fix the ledger |
| unreleased workers | A worker that is not `released` | Release finished ones. Ask about `user_takeover` |

The script only reads. Deleting is a separate, explicit decision: only resources the user told you to remove *and* that the ledger marks `awaiting cleanup`. Check for uncommitted changes first.

## Commit records every turn

At the end of each turn that changed records, the owner commits them, naming each file: `git commit -m "records: <topic> <summary>" -- <files>`. Never `git add -A`. Uncommitted records get lost on a reset or swept into someone else's commit.

## What usually goes wrong

- **A worker that says it is live but is not.** `liveness: live` only means the process exists. A worker stopped by a model capacity error never sends `worker_done`. Read its terminal (`orca terminal read --terminal <handle> --limit 20`) before concluding anything, and resume it with `orca terminal send` rather than starting a second one.
- **A branch locked out everywhere.** One branch checks out in one worktree per clone. A forgotten worktree is why a branch "cannot be checked out".
- **Orphans with no record.** Almost always a resource created before its ledger row. See the first rule.


## Work not started

`work/inbox.md` is the index for ideas and deferred tasks. Read it separately at startup or when the user asks what remains; `ledger-status.py` does not include it. Use `orca-ledger-inbox` when available and follow the workspace contract. Link an item to `work/<topic>/state.md` when work starts. An inbox entry is not permission to implement, and a ledger closed for deferral does not make the item done.
