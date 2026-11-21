# The work ledger

Which worktree, branch and worker belongs to which topic, and how far it got, lives in `work/<topic>/state.md`. When a session disappears, or you come back after doing something else, this file is how the work resumes and how orphaned resources are found.

Only the ledger's `owner` rewrites it (see "Owners"). Workers report; the owner transcribes.

## Single-session work keeps state too

- **When:** anything that will not finish in one answer. A single question answered and done needs no ledger.
- **Updating:** on start, whenever the stage or the next action changes, and at the end. If the conversation changes topic, write the state of what you were doing *before* answering about anything else.
- **Content:** stage, next action, what you are waiting on; history goes in `log.md`. If you edited code, record path, branch and uncommitted changes in the checkout table. Drop tables you are not using.
- **Keep facts current.** `state.md` is rewritten, not appended to — when something changes, fix the stale statements in it ("not read yet", "could not read", and so on) and put the event in `log.md` ("not read yet", "could not read", and so on).
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
| After orchestration | What was adopted and dropped, workers released, what was put on the user's checkout, what needs tidying. Reasons go in `decisions.md` |
| Tidying | Rows you removed become state `deleted`. When everything is finished, stage `closed` |

Write before you create the resource. If creation fails, the record is what lets you find the orphan.

Put `<topic> <description>` in the Orca worktree's `--comment` so it is identifiable in the Orca UI too.

## Layout

A topic is a folder of three files:

| File | What it holds | Size |
|---|---|---|
| `state.md` | The current state only: frontmatter, the resource tables, at most a few lines of context. Rewrite it; do not append to it | Small — `ledger-lint.py` warns past 4 KB |
| `log.md` | Append-only history: `- YYYY-MM-DD HH:MM point: what happened`. Never edit past lines | Grows |
| `decisions.md` | What was decided, the options rejected and why, verification output | Grows slowly |

A resuming session reads `state.md` first and opens the other two only when it needs history. That is the point of the split: the current state must never be buried under its own log.

Topics may be grouped by domain: `work/<domain>/<topic>/`. The flat `work/<topic>/` still works; pick one per workspace and do not mix within a domain. Closed topics older than 30 days move to `work/_archive/<topic>/` (keep the domain path under it if you use one). Archived ledgers are not reported as open, but their paths still count as known, so their worktrees are not reported as unlisted.

## Format

```markdown
---
id: <topic>                 # the folder name
domain: <domain>            # optional; matches domains/<domain>.md
stage: brief                # brief | working | verifying | user-review | waiting-external | done | closed
next: <one line, so the next session can act immediately>
waiting_on: none            # none | user: <the question> | external: <who or what>
owner: operator             # operator | <agent>:<session id>
repos: [<repo>, <repo>]
updated: YYYY-MM-DD HH:MM
verified_at:                # YYYY-MM-DD HH:MM of the last verification by the owner, or empty
---

# <topic>

<two or three lines of context a new session needs. Not history — that is log.md>

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

Stages:

| stage | Meaning |
|---|---|
| `brief` | Being scoped; nothing created yet |
| `working` | Someone is changing code |
| `verifying` | The owner is checking the result with code and tests |
| `user-review` | Waiting for the user to review an adopted result |
| `waiting-external` | Blocked on something outside — a review, a deploy, another team. Say what in `waiting_on` |
| `done` | Finished and verified; resources may still need tidying |
| `closed` | Nothing left. Eligible for `work/_archive/` after 30 days |

The stage is one of these words and nothing else — put explanation in `next` or the context lines. Free text defeats every filter. `next` is never empty or `?` while the topic is open.

**The field and column names are English even when you are answering the user in another language.** The scripts match on them literally, so a ledger with translated keys reconciles against nothing and reports `?` for every field. Write the *values* in whatever language you are speaking — `next: 통합 테스트 실행` is correct, `다음 할 일: ...` is not.

Paths are absolute and wrapped in backticks — `ledger-status.py` matches on that. Worker state is one of `planned`, `working`, `done`, `adopted`, `dropped`, `awaiting cleanup`, `deleted`.

The column names `path`, `state`, `last commit`, `run` and `dispatch` are what the script reads. Rename them and the reconciliation goes quiet, which is worse than noisy.

State `working` is a claim the script checks: it asks Orca whether that dispatch still exists. Orca answers an unknown run with an empty list rather than an error, so without the dispatch id a stale run reads as "all clear".

v1 ledgers (a `- stage:` bullet header, no frontmatter) are still read, and the lint warns once per file until they are migrated.

## Owners

`owner` names who may rewrite `state.md`. Everyone else appends to `log.md` only.

- **Per-session (default).** The session working the topic is the owner: `owner: claude:<session id>`.
- **Operator (optional).** When one long-lived operator agent or bot runs the workspace, set `owner: operator` on every ledger and record the operator's identity once in `AGENTS.md`. A delegated session becomes owner for the duration of its task (`owner: codex:<session id>`); when it finishes or its session ends, the operator takes the ledger back (`owner: operator`) and appends one log line. A dead session in `owner` is then always a bug, not a leftover.

## Domains

`domains/<domain>.md` is the knowledge module for one area: its vocabulary, invariants, risk rules, the repositories involved, and links to its representative topic ledgers. It carries the same `status`/`checked_at` frontmatter as other facts and is written from code, not at setup.

```markdown
---
status: assumed             # confirmed | assumed | historical
evidence: [<repo>/<path>:<line>, <commit>]
checked_at: YYYY-MM-DD
---

# <domain>

## Terms
## Invariants and risk rules
## Repositories
## Topics
- `work/<domain>/<topic>/state.md` — <one line>
```

## Committing records

Record files are committed by the owner at the end of every turn that changed them, with the files named explicitly:

```text
git commit -m "records: <topic> <summary>" -- work/<domain>/<topic>/state.md work/<domain>/<topic>/log.md
```

Never `git add -A` or `git commit -a`; another session may be mid-write in a neighbouring file. Uncommitted records are lost on a reset and leak into the next unrelated commit. This applies to records in this workspace only — commits to code repositories still follow the contract's permissions.

## The check

Run it when you start a session, when you pick work back up, and before tidying. It only reads.

```text
python3 scripts/ledger-status.py   # includes the lint
python3 scripts/ledger-lint.py     # lint alone; exits 1 on errors
```

| Output | Meaning | What to do |
|---|---|---|
| open | Topics whose stage is not `closed` | Continue from `next` |
| lint | Schema errors, stale `confirmed` facts, dead paths, bloated or unarchived ledgers | Fix errors now; re-verify or downgrade stale facts |
| unlisted worktrees | An Orca worktree in no ledger | Do not delete it. Ask the user |
| ledger mismatch | A path or commit differs from the ledger | Check reality, then fix the ledger |
| unreleased workers | A worker that is not `released` | Release finished ones. Ask about `user_takeover` |

## What may be deleted

Only resources the user has told you to remove *and* that the ledger marks `awaiting cleanup`. Unlisted worktrees and workers the user took over are never deleted without asking. Check for uncommitted changes first. Keep the session id in the ledger: deleting a worktree leaves the transcript findable through `orca search`, but the way back into it from the Orca list is gone.
