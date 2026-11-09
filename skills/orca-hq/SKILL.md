---
name: orca-hq
description: Create or operate an orca-hq workspace — a git repository of Markdown one level above the user's code repositories, holding the system map, work ledgers, cross-repo knowledge and the agent contract, built on Orca's worktrees and workers. Use when the user asks to set up, scaffold or initialise an orca-hq workspace or "agent HQ"; when they ask where their systems, past decisions or active worktrees are recorded; or when you are working in a folder whose AGENTS.md identifies it as an orca-hq workspace and you need to know how it is meant to be used.
---

# orca-hq

A workspace that sits above the code repositories. The agent starts there, so it knows the systems, the past decisions, the live resources and its own limits before it touches code.

## Is one already set up?

Look for a folder containing `AGENTS.md` plus `map/`, `work/` and `playbooks/`. Common spots: the parent of the user's code repositories, or a path they name. If `AGENTS.md` is there, **read it and follow it** — it is the contract and it wins over this skill. Then run `python3 scripts/hq-status.py` and report where things stand.

If there is none and the user asked to set one up, scaffold it.

## Scaffolding one

The template lives in this skill's repository under `template/`. Copy it, then fill in the placeholders. Do not invent structure that is not in the template.

### 1. Ask only what you cannot infer

Three things, in one round. Do not ask more.

- **Where:** default is a sibling of their code repositories, e.g. `~/projects/hq`. Suggest a path and let them correct it.
- **Scope:** what work this workspace covers, in one phrase ("our payments platform", "my personal projects"). This is the first line of the contract. If they want to keep it open, write "the repositories listed in `map/systems.yaml`" and leave the map empty.
- **Working preferences:** anything about how they want the agent to behave — language to answer in, tone, a review step they always want. Optional; leave the section out if they have none.

Do **not** populate `map/`, `domains/` or `knowledge/` at setup time. Those get filled from code, as the work happens, with evidence. A map invented at setup is exactly the stale-fact problem the workspace exists to prevent.

### 2. Copy and substitute

Copy `template/` to the chosen path, then replace in every file:

| Placeholder | Value |
|---|---|
| `{{HQ_NAME}}` | The workspace name — usually the folder name |
| `{{HQ_PATH}}` | Absolute path of the workspace |
| `{{HQ_PARENT}}` | Absolute path of its parent folder |
| `{{HQ_SCOPE}}` | The scope phrase from step 1 |
| `{{HQ_PREFERENCES}}` | The preferences paragraph, or remove the line entirely |

Check no `{{` remains anywhere before you report done.

### 3. Initialise and register

```text
git init -b main && git add . && git commit -m "orca-hq workspace"
orca repo add --path <workspace path> --json
```

The commit matters: Orca cannot create a worktree session from a branch with no commits. Do not add a remote — the workspace describes how the user's systems fit together, so pushing it is their decision, not a default.

### 4. Report

Give them: the path, that it is registered with Orca, the output of `python3 scripts/hq-status.py`, and one line on what to do next — start the next piece of real work from this folder, and the map fills itself in.

## Operating one

Once it exists, `AGENTS.md` is the authority. The parts agents most often skip:

- **Status, evidence, date on every fact.** An entry that is not `confirmed` has to be re-read from code before you assert it. Writing `assumed` is not a failure; asserting an assumption as fact is.
- **Record where, do not copy.** Content inside a repository is referenced by path. Only what spans repositories is written here.
- **The ledger comes before the resource.** Write the `work/<topic>/state.md` row before spawning a worker or creating a worktree, so a failed spawn still leaves a trace. See `orca-hq-ledger`.
- **Never commit to the user's branch** unless told. Adopted work arrives uncommitted so they review it themselves.
- **Delete nothing on your own initiative.** `hq-status.py` reads; it does not clean. Unlisted worktrees get reported to the user, not removed.
