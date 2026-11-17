---
name: ssStop
description: End the current orca-ledger work session in one step — save the topic ledger, commit only this session's ledger files, close browser task spaces, then close this Orca tab immediately. Use when the user types /ssStop or says to wrap up, save and close, end the session, 종료, 세션 닫아. The command itself is the approval; do not ask again.
---

# ssStop — save state, then close this session

The user is done. Do the whole sequence without asking. Answer in the user's language.

## 1. Find the records

Read the workspace's `AGENTS.md` for where records live. In a linked worktree, records belong in the main workspace, not this copy. The ledgers to close are the `work/<topic>/state.md` files whose `session` line names this session, plus any ledger this session wrote today.

## 2. Save the ledger

For each ledger, update the header:

- `stage:` the real outcome, then "session closed YYYY-MM-DD"
- `next:` what a resumed session does first, or "none"
- `waiting on user:` an open decision, or `no`
- `session:` `closed YYYY-MM-DD (was <agent> <session-id>)`

Append one Log line. Unfinished or unverified work goes in `next`, stated plainly; closing is not a reason to hide it. Another session's ledger gets at most one appended Log line.

## 3. Commit

Commit **only the ledger files this session wrote**, by name: `git commit -- <files>`. Never `git add -A`; never sweep in another session's edits. Records are committed where the workspace says (normally its `main`). Do not push.

## 4. Release what this session holds

Finish browser task spaces this session opened and still owns (keep nothing). Leave spaces the user already ended. Do not remove worktrees, branches or workers; list any that remain in `next`.

## 5. Report, then close in the same reply

Write a short report first — ledgers updated and their next step, commit hash, what was released, anything unverified. Then, as the **last tool call of that same reply**, run:

```sh
<this skill's folder>/scripts/close-own-tab.sh 3
```

It resolves this session's terminal from `ORCA_TAB_ID`/`ORCA_AGENT_PANE` and closes the tab 3 seconds later, detached so it survives the turn ending. Do not take the terminal id from a ledger: a resumed session usually lives in a new tab and the recorded id points at the old one. If the script prints `ERROR`, tell the user the exact `orca terminal close --terminal <id> --tab` command to run instead. Do not tell the user to check whether it closed; if the command was scheduled, the session ends.
