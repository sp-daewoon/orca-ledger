---
name: ssStop
description: End the current orca-ledger work session in one step — save the topic ledger, commit only this session's ledger files, close browser task spaces, then close this Orca tab immediately. Use when the user types /ssStop or says to wrap up, save and close, end the session, 종료, 세션 닫아. The command itself is the approval; do not ask again.
---

# ssStop — save state, then close this session

The user is done. Do the whole sequence without asking. Answer in the user's language.

## 1. Find the records

Read the workspace's `AGENTS.md` for where records live. In a linked worktree, records belong in the main workspace, not this copy. The ledgers to close are the `work/**/state.md` files whose `owner` names this session (v1 ledgers: the `session` line), plus any ledger this session wrote today.

## 2. Save the ledger

For each ledger, update the frontmatter:

- `stage:` the real outcome, one of the stage words (usually unchanged, `user-review` or `done`) — never free text
- `next:` what a resumed session does first, or `none` if the stage is `done` or `closed`
- `waiting_on:` an open decision (`user: <question>`), or `none`
- `owner:` `operator` under the operator model; otherwise leave it, the session id is how the work is found again
- `updated:` now

Append one line to `log.md`: `- YYYY-MM-DD HH:MM session closed: <agent>:<session-id>, <outcome>`. For a v1 ledger (no frontmatter), update its `- stage/next/waiting on user/session` lines the same way and append to its Log section. Unfinished or unverified work goes in `next`, stated plainly; closing is not a reason to hide it. Another session's ledger gets at most one appended `log.md` line.

## 3. Commit

Commit **only the ledger files this session wrote**, by name: `git commit -- <files>`. Never `git add -A`; never sweep in another session's edits. Records are committed where the workspace says (normally its `main`). Do not push.

## 4. Release what this session holds

Finish browser task spaces this session opened and still owns (keep nothing). Leave spaces the user already ended. Do not remove worktrees, branches or workers; list any that remain in `next`.

## 5. Report, then close in the same reply

Write a short report first — ledgers updated and their next step, commit hash, what was released, anything unverified. Then, as the **last tool call of that same reply**, run:

```sh
<this skill's folder>/scripts/close-own-tab.sh
```

Orca names the session's own terminal (`ORCA_TERMINAL_HANDLE`, or `orca terminal show` with no handle), so the script needs no lookup. It checks the handle with Orca, then closes that tab two seconds later, detached so the final reply renders first and the close survives the turn ending. Never take the terminal id from a ledger: a resumed session lives in a new tab and the recorded id points at the old one. If the script prints `ERROR`, tell the user the exact `orca terminal close --terminal <id> --tab` command to run instead. Do not tell the user to check whether it closed; if the command was scheduled, the session ends.
