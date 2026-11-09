# {{WORKSPACE_NAME}}

This is where an agent starts work on {{WORKSPACE_SCOPE}}. It sits one level above the code repositories and takes requests directly.

Repositories in scope are listed in `map/systems.yaml`. A repository that is not listed has not been looked at yet — that is not the same as out of scope.

{{WORKSPACE_PREFERENCES}}

## How work is done

### Default: one session

Whichever session the user spoke to handles the request itself. Direct work happens in the target repository's existing checkout, without a worktree. Delegation follows "Routing" below.

- **Before editing:** read the target repository's own rules (`.claude/`, `CLAUDE.md`, `AGENTS.md`) and `rules/<repo>.md` here. Starting in this folder does not apply a repository's rules automatically.
- **Checkout check:** switch the target repository to the working branch and edit there; that switch is part of the assigned task. Before editing, look at the branch and the working tree. If the user has uncommitted changes that overlap the edit, stop and ask before touching anything — offer a worktree at `{{WORKSPACE_PARENT}}/<repo>-<topic>` and create it only once they agree.
- **Verification:** run the relevant tests yourself. Anything you could not run, report as not run.
- **Commits:** never to the user's branch unless asked. Worker branches follow "Delegation".
- **Work state:** keep `work/<topic>/state.md` current — stage and next action. Write it *before* the conversation moves on, so the work can be resumed at any time. Follow `playbooks/work-state.md`.
- **Where records live:** a worktree of this workspace is just a seat for a session. Wherever you started, read and write `work/`, `map/`, `domains/`, `knowledge/`, `rules/` at the main folder `{{WORKSPACE_PATH}}` by absolute path, and commit there. Do not commit to a worktree branch. If you started in a worktree, run `git merge --ff-only main` first to pick up current rules — and note that uncommitted rule changes do not arrive through that merge, so a clean merge does not mean you are current.
- **Where code lives:** in the target repository's checkout. Branches are per repository; a branch name here has nothing to do with a branch of the same name in a code repository.
- **Records accumulate without being asked.** Decisions and the reasoning go in `work/`; newly confirmed facts go to `map/`, `domains/`, `knowledge/`. Committing those files is the user's call.
- **Sessions:** a worktree of this workspace per topic is recommended — Orca then lists them separately and the user can walk into the right one. One session may cover several topics. When a different topic comes up mid-conversation, follow `playbooks/topic-switch.md`.

### Routing

The main session decides. When it is a close call, choose the smaller option. If the user specifies an approach, use it.

| Situation | Handling |
|---|---|
| Questions, lookups, records, tidying a topic | Main session, directly |
| A fix whose cause and location are both known | Main session edits the checkout |
| Behaviour or background answerable by reading code | Main session investigates |
| Broad behaviour that is slow to read directly | Read-only subagents in parallel |
| A bug with an unknown cause | Main session, following `playbooks/debug.md` if present; delegate only if the repro is expensive |
| A change that is hard to implement, has an independent contract, and a clear proof of completion | Delegate to an Orca worker |
| A design choice that genuinely forks | Write the options down and ask the user; do not pick silently |
| Comparing two approaches, or checking one agent's work with another | Cross-agent work — `playbooks/cross-work.md`, only when the user asks |

#### Scope of change

This is running software. Every code task is a small change by default.

- Before editing, find everything the change has to touch — callers, tests, configuration. That is the scope.
- Take the first option that works, in this order: not building it at all, something already in the repository, a standard library feature, an installed dependency, the smallest new code.
- Keep existing layers, interfaces, conventions and compatibility code. Do not add abstractions, options or cleanups nobody asked for.
- A large task is still about adding what is needed, not restructuring. Split it into small verifiable units.
- Unless the task needs it: do not add documents, do not change scripts or build configuration, do not change the behaviour of existing functions. If it is needed, say so in the report.
- Small, but finished. Validation, data-loss prevention, security and the tests that matter are not optional.
- Problems found outside the scope get reported, not fixed.

#### Delegation

- Doing it yourself is the default. Size alone is not a reason to delegate.
- **Writing code:** an Orca worker in the target repository's worktree and branch. Tell the user the path and branch in one line when you start, and write it to `state.md`.
- **Read-only investigation and review:** do it yourself. Use subagents only when the search is broad or genuinely parallel. Do not use a copy-the-start-folder isolation mode for writing code.
- **Verification and adoption:** confirm with code and tests, then put the result on the user's branch **uncommitted**, per `playbooks/verify-and-adopt.md`.
- **Follow-up fixes:** once the user has reviewed and asked for changes, make them yourself. Re-delegate only if the scope genuinely grew.
- **Commits:** often, on worker branches. On the user's branch, only when told.
- **PRs, pushes, merges:** the user does these, unless they explicitly tell you otherwise.
- **Tickets and chat:** only within the assigned task. If the requirement is not written down anywhere, ask a specific question — never invent a requirement and build it.
- **Questions:** reason it out first; ask only what is genuinely the user's to decide or what blocks you.

A worker's "done" is not verification. Two workers agreeing is not verification either. The main session confirms with code and tests.

## Starting a session

Run `python3 scripts/ledger-status.py` when you start a session or pick work back up. Single-session work keeps state too. Format and handling: `playbooks/work-state.md`.

## Where to look, in order

1. `map/` — systems, repositories, call paths, data
2. `domains/` — what each area of the product does
3. `work/<topic>/` — briefs and adoption decisions, open or closed
4. `knowledge/` — decisions, incidents and fixes that span repositories
5. `orca search "<keyword>"` — transcripts of past sessions
6. The repository's own code and team docs

When a requirement looks empty, look for the parent issue, title keywords, linked documents and attachments before concluding there is nothing. Compare a document's description of current behaviour against the code and report the differences. Judge behaviour by reading the implementation, not by the name — and if you did not read it, record it as assumed.

Trust an entry in `map/` or `knowledge/` according to its status. If it is not `confirmed`, re-read the code before answering.

## Record rules

- Do not copy what lives inside a repository; record where it is. This workspace holds only what spans repositories.
- Every entry in `map/` and `knowledge/` carries a status (`confirmed`, `assumed`, `historical`), evidence (code location, commit, document, session) and the date it was checked.
- Do not copy session transcripts; record enough to find the session again.
- This repository is local by default. Add a remote only when the user asks — it describes how their systems fit together.

## Permissions

| Level | Scope | Handling |
|---|---|---|
| Free | Lookups, analysis, search, starting sessions, running tests, records in this workspace | Go ahead |
| One session | Editing the checkout for the assigned task, without committing | Go ahead; ask if "Checkout check" above applies |
| Delegation | Starting a worker that fits the routing table | Go ahead, and report path and branch |
| Inside a worktree | Editing and committing on an agent branch | Go ahead |
| Adoption | Putting an adopted result on the user's checkout, uncommitted | Go ahead and report — `playbooks/verify-and-adopt.md` |
| Ask first | Deleting or moving the user's files, changing the user's branch, committing to it, push, PR, merge, posting anywhere outside | Confirm with the user |
| Never | Changing production data or environments, storing credentials in a file or a record | Only on an explicit instruction |

Worktrees a worker created stay until the user says to remove them, so the session can be reopened. Where a repository's own rules are stricter, those win.

## Branches

Unless told otherwise:

- Fetch `main` and branch from the current `origin/main`. Where there is no remote, branch from local `main`.
- Name it `feature/<topic>`, in short kebab-case.
- Where a repository uses a ticket scheme, follow it. This workspace does not assume one.
- When one topic needs several branches — cross-agent work — distinguish them as `feature/<topic>-codex`, `feature/<topic>-claude`.

## Tools

Orchestration is Orca's own. Read `orca skills get orchestration` for usage. If `orca` is not on PATH, use the binary inside the app bundle (on macOS, `/Applications/Orca.app/Contents/Resources/bin/orca`).

## External connections

Nothing is connected yet. Fill this table in when you add a tracker, a wiki or monitoring.

| Target | Server | Tools | Credentials file |
|---|---|---|---|
| (none) | | | |

Rules that apply the moment something is added:

- **Token values** live only in the credentials file. They are never copied into records, conversation or commits, and never printed. Check that a key exists and has a value, nothing more. If a value has to move, give the user a command to run themselves. Keep the folder holding them out of git.
- **Expiry:** record the expiry date in `knowledge/` as a `**expires:** YYYY-MM-DD` line and `ledger-status.py` will warn 14 days out. If a call fails with 401 or 403, tell the user and point them at renewal.
- **Writes** — creating or editing a ticket, changing status, commenting, editing a page — are posting outside. Confirm first, and record target, content, time and session straight afterwards. With one shared token, the tracker's own history cannot tell your sessions apart.
- **Registration:** tools only appear in sessions started *after* they were registered. Their absence in an older session is not a connection failure.
- **Production write tools** — creating, editing or deleting monitors, dashboards and pipelines — are production changes. Only on an explicit instruction.

## Managing several sessions

Procedure: `playbooks/topic-switch.md`.

- **Current state:** `[sessions]` in `python3 scripts/ledger-status.py`. When you open or switch a session, fix the `session` line in that topic's `state.md`.
- **One owner per ledger:** a topic's ledger is written by that topic's session. Other sessions append a log line; they do not overwrite its content.
- **Tabs:** do not close a tab the user is using, and do not type into that session. Unless they ask you to.
- **Commits:** name the files. Never `git add -A`. If another session is mid-write in a record, tell the user before including it.
- **Credentials:** tokens and credential files never enter this workspace's records.

## Repository rules

Workers do not read this workspace. Where `rules/<repo>.md` exists, the main session copies its content into the brief and checks it was followed at adoption time.

## Playbooks

- `playbooks/start-main.md` — starting a main session
- `playbooks/work-state.md` — the ledger and the orphan check
- `playbooks/topic-switch.md` — a different topic mid-conversation; handing off and resuming
- `playbooks/cross-work.md` — running two agents on one brief
- `playbooks/verify-and-adopt.md` — compare, verify, adopt, hand to the user
- `playbooks/cleanup.md` — recording and tidying up
