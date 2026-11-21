# Migrating a workspace to ledger v2

A workspace scaffolded from an earlier template keeps working: `ledger-status.py` still reads v1 ledgers (the `- stage:` bullet header). v2 adds a frontmatter schema, splits each ledger into three files, allows grouping by domain, and adds `ledger-lint.py`. Upgrade when it suits you, one step at a time. Nothing here needs to happen in one go.

This is the manual "safe update" path. Your workspace's `AGENTS.md` and playbooks are yours — you have probably edited them — so they are never overwritten. You copy in what is new and merge the rest by hand.

## 0. Before you start

- Commit or set aside every uncommitted record first: `git status` in the workspace must be clean. A migration mixed with half-written records is how records get lost.
- Do it on a branch of the workspace (`git switch -c ledger-v2`), so you can diff it and throw it away.
- Make sure no other session is writing records while you migrate.

## 1. Add the scripts

Copy from the skill's `template/scripts/`:

- `ledger-lint.py` — new
- `ledger-status.py` — replace it, unless you changed yours; then merge. The new one loads `ledger-lint.py` from the same folder, reads both header formats, and looks in `work/<domain>/<topic>/` as well as `work/<topic>/`.

Run `python3 scripts/ledger-status.py`. The `[lint]` section lists every ledger still on v1 and every other problem. That list is your migration checklist. `python3 scripts/ledger-lint.py` exits 1 while there are errors.

## 2. Convert each ledger

For each `work/<topic>/state.md`:

1. Move the `## Log` section to `log.md` in the same folder, unchanged. Move decision write-ups (and any `decision.md`) to `decisions.md`.
2. Replace the bullet header with frontmatter:

   | v1 | v2 |
   |---|---|
   | `- stage: user review` | `stage: user-review` |
   | `- stage: awaiting cleanup` | `stage: done` (the rows still say `awaiting cleanup`) |
   | `- stage: <free text>` | the nearest stage word; the text goes in `next` or the context lines |
   | `- next: ...` | `next: ...` — never empty or `?` while open |
   | `- waiting on user: no` | `waiting_on: none` |
   | `- session: <agent> <id> \`<path>\`` | `owner: <agent>:<id>` (or `operator`); the path becomes an `Other resources` row |
   | `- updated: ...` | `updated: ...` |
   | — | `id`, `domain`, `repos`, `verified_at` |

3. Keep the Workers, User checkouts and Other resources tables exactly as they are. Their column names are what the reconciliation reads.
4. Leave `state.md` with the current state only. Aim for well under 4 KB.

Commit each converted topic separately, naming the files.

## 3. Re-check what is `confirmed`

The lint now flags any `confirmed` entry in `map/`, `domains/` or `knowledge/` whose `checked_at` is more than 30 days old, or that has none. For each: re-read the code and update `checked_at` and `evidence`, or change the status to `assumed`. Do not bump the date without reading.

## 4. Optional: group by domain and archive

- Move topic folders to `work/<domain>/<topic>/` with `git mv`, and set `domain:` in their frontmatter. Search the workspace for the old path (`grep -rn "work/<topic>/"`) and fix the links.
- Write `domains/<domain>.md` as you learn each area, from code, with status and `checked_at` — not all at once.
- Move topics that have been `closed` for more than 30 days to `work/_archive/`.

Worktree paths recorded in an archived ledger still count as known, so moving a ledger does not make its worktree show up as unlisted.

## 5. Merge the contract

Diff your `AGENTS.md` and `playbooks/work-state.md` against the new template and bring in the parts you want:

- the ledger layout, frontmatter and stages (`playbooks/work-state.md`)
- `confirmed` expiring after 30 days ("Where to look")
- committing record files every turn, by name ("Records accumulate", "Committing records")
- the owner model, and the operator option if one agent runs your workspace ("Managing several sessions")

Then merge the branch into the workspace's `main`.
