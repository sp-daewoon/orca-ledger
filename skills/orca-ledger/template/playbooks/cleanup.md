# Recording and tidying up

## 1. Record the decision

In `work/<topic>/decision.md`:

- What was adopted, and why
- What was rejected
- Verification results — the commands you ran and what they printed
- What was deferred
- The original sessions, recorded well enough to find them again with `orca search`

## 2. Promote what is reusable

Move it to `knowledge/` with status, evidence and the date checked. Content that lives in a repository is referenced by path, not copied.

## 3. Update the map

If you found something that contradicts `map/`, fix it and update the evidence and date. If you worked on a repository that was not in the map, register it.

## 4. Tidy up

- Release a finished worker: `orca orchestration worker-release --dispatch <dispatch_id> --json`
- What is left: `orca orchestration worker-list --run <run_id> --terminal-state reclaimable --json`
- Reconcile first with `python3 scripts/ledger-status.py`.
- Worktrees and branches stay until the user says to remove them. When told, delete only what the ledger marks `awaiting cleanup`, and set those rows to `deleted`. Ask about unlisted worktrees and `user_takeover` workers. Never touch files or branches the user created.
- When everything is finished, set the ledger's stage to `closed`.
- `orca worktree rm` is asynchronous. The folder lingers after the response returns and the branch cannot be deleted until it is gone. Confirm with `git worktree list` once the folder disappears.
- Within one clone on one machine, a branch can only be checked out in one worktree. Leaving a worktree in place keeps that branch locked out of every other folder.
