---
name: orca-ledger-handoff
description: Handle a mid-conversation topic switch in an orca-ledger workspace — decide whether the new request continues the current work, hand it to a new Orca session when the user wants that, carry the context across in a state file, and reopen a session whose tab was closed. Use when the user raises something unrelated to the work in progress, says "open a new session for this", "pick that session back up", or "where did we get to on that other thing".
---

# Topic switches and handoffs

One session may cover several topics. Splitting is a choice you offer and the user makes — never do it on your own.

## 1. Read the situation

Run `python3 scripts/ledger-status.py`, then look for the same topic in `work/*/state.md` and with `orca search "<keyword>"`.

| Call | Handling |
|---|---|
| A continuation of the current work | Just continue; do not ask |
| A question answered in one reply | Answer it, return to the work. No ledger |
| Work done in another session | Ask, as "existing work" |
| New work | Ask, as "new work" |

## 2. Write state before you ask

Put how far you got and the next action into the current topic's `state.md`. If the user then switches, nothing is lost.

## 3. Ask once

Give a one-line reason for your read. Ask once per topic. If they say "here", never ask again for that topic.

- **New work:** "This looks like a different topic. Continue here, or should I open a session for it?"
- **Existing work:** "This looks like `<topic>` (session `<id>`). Pick that session back up, or do it here?"

## 4. If it stays here

Create `work/<topic>/state.md` with this session in `session`, or continue the existing ledger. Write the state of the topic you leave, every time you switch. When one finishes, say what is still waiting and ask which to take.

## 5. If it goes to a new session

The new session cannot see this conversation. The state file is the entire handoff, so write it first: the user's request in their own words, the relevant parts of this conversation, your first plan, and the originating session id.

```text
orca worktree create --repo path:<workspace path> --name <topic> --base-branch main --no-parent --comment "<description>" --agent <claude|codex> --prompt "The rules in this worktree may be a stale copy. Read <workspace>/AGENTS.md and <workspace>/work/<topic>/state.md and follow them. Write records in that folder. Start by telling the user briefly what you understand and what you plan. Do not change code before the user confirms." --json
```

- Without `--no-parent` it nests under the worktree you are in.
- `--name feature/X` creates the branch as `feature-X`; rename it with `git -C <worktree> branch -m feature/<topic>`.
- Set a readable label: `orca worktree set --worktree path:<worktree> --display-name "<topic> <description>"`.

Then record the worktree path (backticks) and the session id in the ledger. Find the id in the newest file whose prompt contains the ledger path — for Claude, the filename under `~/.claude/projects/<transformed path>/`; for Codex, `payload.id` on the first line of a file under `~/.codex/sessions/<y>/<m>/<d>/`.

Finally, in *this* session: say what you handed off and where, restate the work in progress and its next action, and carry on. The user should never have to re-explain context you already had.

## 6. Reopening a closed session

A closed tab disappears from the Orca list but the session resumes with its memory. Never close a tab the user is using; reopen from the ledger's session id.

```text
orca terminal create --worktree path:<worktree from the ledger> --title "<topic>" --command "claude --resume <session id>" --json
```

For Codex, `codex resume <session id>`. The start folder has to still exist, which is why session worktrees stay until the user says otherwise. Claude and Codex cannot read each other's conversations, so the ledger records the agent name too.

## Cost

A new session re-reads context from scratch — measured once at roughly 54k tokens for Claude just to read a handoff file and answer one line. Small things are cheaper here. Long work, or work starting from an already-long conversation, is cheaper split out.
