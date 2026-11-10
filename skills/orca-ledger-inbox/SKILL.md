---
name: orca-ledger-inbox
description: Capture passing ideas, future plans, deferred tasks and follow-ups in an orca-ledger workspace inbox, list what remains, and connect an item to its topic ledger when work starts. Use when the user says they might or will build something later, asks to remember a task, or asks about their backlog. Does not schedule reminders or authorize implementation.
---

# Ideas and deferred work

Read the workspace's `AGENTS.md` and follow its record location. In a linked worktree, records belong in the main workspace, not a new copy here. Do not guess a workspace or create a whole workspace if none can be identified; ask where the list belongs.

## Capture

Read `work/inbox.md` immediately before editing. If absent, create it with a short “capture is not permission to start” note and this table; do not seed invented sample tasks:

```markdown
| id | status | item | source | topic | updated |
|---|---|---|---|---|---|
```

- Reuse a matching item; otherwise choose an unused stable ID such as `IN-001`. Record a concise summary, date, originating session or existing ledger link, and a topic link if there is one. Keep the headers English and the values in the user's language. Do not copy a transcript, store credentials, or infer deadlines or requirements.
- Use `idea` for possibilities; `planned` for an explicit decision to do it later; `in_progress` when work has started; `on_hold` when deferred; `done` only after the actual outcome is confirmed. A ledger closed to defer work is not a done item.
- “Maybe build X” is an idea. “I'll build X later” is planned. “Only record X” captures without starting it. For “do X now”, follow normal task permissions, create/reuse the topic ledger, and link it; do not add an approval gate just because an inbox item exists.
- Future intent is not permission to implement, open a session/worker, change code or publish. Capturing alone does not require a new topic folder or a session-choice question. Preserve the current task and briefly tell the user what was recorded.

## Review and connect

For “what is left”, read the inbox and linked current `state.md` files, then distinguish ideas, decisions and deferred work. Do not silently execute the list. On actual work start, create/reuse `work/<topic>/state.md`, link the item and keep detailed progress in the ledger. The inbox is only the index; link existing TODOs rather than copying them. Update the item's status when the real state changes.

Preserve other sessions' entries. If the same item is being edited elsewhere, stop that update instead of overwriting. Record rejections or changes in the existing item without deleting its history. `ledger-status.py` reads topic ledgers, not this table; it is not an inbox display or a reminder scheduler.
