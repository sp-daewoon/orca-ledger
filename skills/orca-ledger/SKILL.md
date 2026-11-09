---
name: orca-ledger
description: Create or operate an orca-ledger workspace — a git repository of Markdown one level above the user's code repositories, holding the system map, work ledgers, cross-repo knowledge and the agent contract, built on Orca's worktrees and workers. Use when the user asks to set up, scaffold or initialise an orca-ledger workspace, an "agent workspace" or a "work ledger"; when they ask where their systems, past decisions or active worktrees are recorded; or when you are working in a folder whose AGENTS.md identifies it as an orca-ledger workspace and you need to know how it is meant to be used.
---

# orca-ledger

A workspace that sits above the code repositories. The agent starts there, so it knows the systems, the past decisions, the live resources and its own limits before it touches code.

## Is one already set up?

Look for a folder containing `AGENTS.md` plus `map/`, `work/` and `playbooks/`. Common spots: the parent of the user's code repositories, or a path they name. If `AGENTS.md` is there, **read it and follow it** — it is the contract and it wins over this skill. Then run `python3 scripts/ledger-status.py` and report where things stand.

If there is none and the user asked to set one up, scaffold it.

## Scaffolding one

The template ships inside this skill, in `template/` next to this file. Resolve it relative to this SKILL.md — the skill is copied into the agent's skills directory on install, so an absolute path from somebody else's machine will not exist. Copy it, then fill in the placeholders. Do not invent structure that is not in the template.

### 1. Find where their repositories already live

**If the user named a location, that is the location.** Use it, run the empty check below, and skip the rest of this step.

Otherwise: never assume a layout, and never hardcode a path like `~/projects` or `~/IdeaProjects`. People keep code in different places and at different depths. Work it out from what is on the machine, in this order, and stop at the first one that answers:

1. **Ask Orca.** It already knows the repositories this user works on:

   ```text
   orca repo list --json
   ```

   Read `ok` in the response before trusting it. `ok: false` with `runtime_unavailable` means the Orca app is not running — that is not an empty list. Say so, and either ask the user to start Orca or carry on to the next option; do not silently treat it as "no repositories".

   Discard any path that no longer exists on disk — Orca has no command to unregister a repo, so the list outlives deleted folders. Then take the `path` of each remaining repo and find their deepest common parent directory. If the user has repos in several unrelated trees, take the directory holding the most of them. That parent is where the workspace belongs, as a sibling of the repositories — not inside one of them.

2. **Use the current directory.** If Orca lists nothing, and the working directory is inside a git repository, use that repository's parent. `git rev-parse --show-toplevel` gives the repository root.

3. **Ask, with no default of your own.** Only if neither worked: ask where their code repositories live, and derive the parent from their answer.

Then propose `<that parent>/<name>` and let them correct both parts. Default the name to `ledger`; if a folder of that name is taken, say so and propose another rather than writing into it.

Check before you copy anything: the target must not already exist, or must be empty. If it exists with files in it, stop and ask — never merge the template into a folder that already has contents.

### 2. Ask only what you cannot infer

Two things, in one round, along with the path you propose. Do not ask more.

- **Scope:** what work this workspace covers, in one phrase ("our payments platform", "my personal projects"). This is the first line of the contract. If they want to keep it open, write "the repositories listed in `map/systems.yaml`" and leave the map empty.
- **Working preferences:** how the agent should behave. Always set a response language, and do not ask for it — infer it from the language the user is writing to you in. If they write to you in Korean, the line is `Answer in Korean, and always use formal speech (존댓말) — in progress reports as well as final answers.` Add anything else they have told you about how they want to work (tone, a review step they always want), and leave the rest out.

  The contract and the playbooks stay in English whichever language you set. They are instructions an agent reads, there is one copy to keep correct, and the response-language line is what makes the agent talk to the user in theirs. Do not translate the template.

  The same goes for the ledger: `work/<topic>/state.md` keeps its English field and column names in every language, because `ledger-status.py` matches them literally. Only the values are written in the user's language.

Do **not** populate `map/`, `domains/` or `knowledge/` at setup time. Those get filled from code, as the work happens, with evidence. A map invented at setup is exactly the stale-fact problem the workspace exists to prevent.

### 3. Copy and substitute

Copy `template/` (including its dotfiles — `.gitignore` and the `.gitkeep` files that carry the empty directories) to the chosen path, then replace in every file:

| Placeholder | Value |
|---|---|
| `{{WORKSPACE_NAME}}` | The workspace name — the folder name |
| `{{WORKSPACE_PATH}}` | Absolute path of the workspace, resolved — no `~`, no `..`, no relative path |
| `{{WORKSPACE_PARENT}}` | Absolute path of its parent, derived from `{{WORKSPACE_PATH}}`, not typed out by hand |
| `{{WORKSPACE_SCOPE}}` | The scope phrase from step 2 |
| `{{WORKSPACE_PREFERENCES}}` | The preferences paragraph, or remove the line entirely |

Paths must be written out in full. Agents read these files in sessions started from other folders, where `~` and relative paths resolve differently or not at all.

Check no `{{` remains anywhere before you report done.

### 4. Initialise and register

```text
git init -b main && git add . && git commit -m "orca-ledger workspace"
orca repo add --path <workspace path> --json
```

`orca repo add` needs the Orca app running. If it is not, the workspace is still complete and usable — report that registering it is the one step left, and the command to run once Orca is open.

The commit matters: Orca cannot create a worktree session from a branch with no commits. Do not add a remote — the workspace describes how the user's systems fit together, so pushing it is their decision, not a default.

### 5. Report

Give them: the path, that it is registered with Orca, the output of `python3 scripts/ledger-status.py`, and one line on what to do next — start the next piece of real work from this folder, and the map fills itself in.

## Operating one

Once it exists, `AGENTS.md` is the authority. The parts agents most often skip:

- **Status, evidence, date on every fact.** An entry that is not `confirmed` has to be re-read from code before you assert it. Writing `assumed` is not a failure; asserting an assumption as fact is.
- **Record where, do not copy.** Content inside a repository is referenced by path. Only what spans repositories is written here.
- **The ledger comes before the resource.** Write the `work/<topic>/state.md` row before spawning a worker or creating a worktree, so a failed spawn still leaves a trace. See `orca-ledger-reconcile`.
- **Never commit to the user's branch** unless told. Adopted work arrives uncommitted so they review it themselves.
- **Delete nothing on your own initiative.** `ledger-status.py` reads; it does not clean. Unlisted worktrees get reported to the user, not removed.
