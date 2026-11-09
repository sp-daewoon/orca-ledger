# When a different topic comes up

One session may cover several topics. Splitting sessions is a choice the main session offers and the user makes, not a requirement. Either way, each topic keeps its own state.

## 1. Decide

If the request looks unrelated to the current work, run `python3 scripts/ledger-status.py` and look for the same topic in `work/*/state.md` and `orca search "<keyword>"`.

| Call | Handling |
|---|---|
| A continuation of the current work | Just continue; do not ask |
| A question answered in one reply | Answer it, go back. No ledger |
| Work done in another session | Ask, as "existing work" below |
| New work | Ask, as "new work" below |

## 2. Before you ask

Write how far you got and the next action into the current topic's `state.md`.

## 3. Ask

Never open or hand off a session without the user's say-so. Give a one-line reason for your read, and ask once per topic. If they say to do it here, do not ask again. If they already said "do it here", do not ask at all.

- **New work:** "This looks like a different topic. Continue here, or should I open a session for it?"
- **Existing work:** "This looks like `<topic>` (session `<id>`). Pick that session back up, or do it here?"

## 4. Doing it here

- Create `work/<topic>/state.md` for the new work, with this session in `session`. For existing work, continue that ledger.
- Every time you switch topics, write the state of the one you are leaving.
- When a topic finishes, say what is still waiting and ask which to pick up. If only one thing is waiting, say what its next action is and ask whether to continue.

## 5. Handing off to a new session

1. Write the new topic's `state.md` first: the user's request in their own words, the relevant parts of this conversation, your first plan, and the originating session id. The new session cannot see this conversation — that file has to be enough to start from.

2. Open the session. It appears as its own entry in the Orca list.

   ```text
   orca worktree create --repo path:{{WORKSPACE_PATH}} --name <topic> --base-branch main --no-parent --comment "<description>" --agent <claude|codex> --prompt "The rules in this worktree may be a stale copy. Read {{WORKSPACE_PATH}}/AGENTS.md and {{WORKSPACE_PATH}}/work/<topic>/state.md and follow them. Write records in that folder. Start by telling the user briefly what you understand and what you plan. Do not change code before the user confirms." --json
   ```

   To make it look like an entry the user created themselves:

   - **Parent:** without `--no-parent` it nests under the worktree you opened it from.
   - **Branch:** `--name feature/X` creates the branch as `feature-X`. Rename it afterwards with `git -C <worktree> branch -m feature/<topic>`.
   - **Display name:** `orca worktree set --worktree path:<worktree> --display-name "<topic> <description>"`.

3. Record the created worktree path in the ledger's `session`, in backticks.
4. Record the session id. Find it in the newest file whose prompt contains the ledger path.
   - **Claude:** the filename under `~/.claude/projects/<transformed worktree path>/`
   - **Codex:** `payload.id` on the first line of a file under `~/.codex/sessions/<year>/<month>/<day>/`
5. In the original session, say what you handed off and where, restate the current work and its next action, and carry on. Do not make the user explain the context again.

## 6. Starting as the new session

- Read `state.md` and say the request, what you understand, and your plan, before anything else.
- Point the ledger's `session` at yourself.
- For anything the ledger does not cover, find the original session with `orca search`.

## Going back to a closed session

Closing a tab removes that session from the Orca list. So never close a tab the user is using, and reopen a missing session from the session id in the ledger. A session whose tab was closed still resumes with its memory intact.

```text
orca terminal create --worktree path:<worktree from the ledger> --title "<topic>" --command "<resume command>" --json
```

- **Claude:** `claude --resume <session id>`
- **Codex:** `codex resume <session id>`

The folder the session started in has to still exist. Deleting a session's worktree also removes the Orca entry, which is why they stay until the user says otherwise.

Without an explicit agent, it reopens with the same agent as the current session. Claude sessions and Codex sessions cannot see each other's conversation, so record the agent name in the ledger too.

A Codex session started without the environment options cannot be the orchestration main. Open sessions meant for cross-agent work the way `playbooks/start-main.md` describes.

## Cost

A new session reads its context from scratch. Measured once: reading the handoff file and answering one line cost Claude roughly 54k tokens. Small things are cheaper here; long work, or work starting from an already-long conversation, is cheaper split out.
