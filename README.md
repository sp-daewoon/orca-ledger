# orca-ledger

The record layer for running a fleet of coding agents in [Orca](https://github.com/stablyai/orca).

It does not orchestrate anything — Orca already does that, and so do several good projects built on it. This is what they leave out: a ledger of every worktree, branch, run and worker, reconciled against what is actually still running, next to a map of your systems that cannot quietly go stale.

You start your agent one level **above** your repos, in a small git repository of plain Markdown. It is where the agent learns what your systems are, what you already decided, which worktrees are still alive, and what it is not allowed to do.

No binary. No daemon. No service to sign up for. Markdown, three skills, and one stdlib Python script.

```bash
npx skills add sp-daewoon/orca-ledger --agent claude-code
```

Then tell your agent: **"set up my orca-ledger workspace"**.

## About the name

A ledger is a book of record you post entries to and reconcile against reality. That is the whole idea, so that is the name.

The `orca-` prefix is there because this only works on [Orca](https://github.com/stablyai/orca): the reconciliation reads worktree, dispatch and worker state from Orca's CLI as `--json`. Point it at anything else and what is left is a Markdown convention and a script that exits with an error. The prefix also matches how Orca's own skills are named (`orca-cli`, `orca-linear`, `orca-per-workspace-env`), so the people this is for can find it.

Unofficial, and not affiliated with Stably or the Orca project. If the Orca maintainers would rather it were named something else, open an issue and it gets renamed.

## What this is not

There are already several Orca-native projects that dispatch workers, gate decisions and coordinate multi-agent workflows — [dely](https://github.com/hieuphung97/dely), [orca-sdlc-kit](https://github.com/vankhangfet/orca-sdlc-kit) and [mogui-ADE-orchestrator](https://github.com/baksohyeon/mogui-ADE-orchestrator) among them. If you want an orchestrator, use one of those; some of them are good.

This is the other half. None of them keep a durable record of what was created, reconcile it against what is still alive, or put an expiry on a fact. Run this next to whichever orchestrator you use.

## The three things it fixes

Running one agent is fine. Running a fleet across several repos is where it falls apart.

**1. Resources leak.** You spawn a worker, it finishes, you move on. Three days later you have nine worktrees, two workers Orca still considers live, and a branch you cannot check out anywhere because a worktree you forgot is holding it.

orca-ledger keeps a ledger of every worktree, branch, worker and dispatch — written *before* the resource is created, so a failed spawn still leaves a trace. Then it reconciles the ledger against reality:

```
$ python3 scripts/ledger-status.py
[alert]
  none
[open]
  payments-retry | implementing | next: verify worker output against tests | waiting on user: no
[sessions]
  payments-retry | implementing | claude 0a3f… `/Users/me/orca/workspaces/ledger/payments-retry`
[unlisted worktrees]
  /Users/me/orca/workspaces/api/spike-3 (spike-3)
[ledger mismatch]
  payments-retry /Users/me/wt/api-retry: ledger a1b2c3d, actual 9f8e7d6
[unreleased workers]
  payments-retry dsp_4e2a reclaimable user_takeover: /Users/me/wt/api-retry
```

It only reads. It never deletes anything.

**2. Facts rot.** An agent reads your notes from six weeks ago and states them as current truth. So every fact in the knowledge base carries three fields, and the contract says an agent may only assert it if the status is `confirmed`:

```yaml
- from: checkout-api
  to: pricing-engine
  type: http
  summary: price quote on cart render
  status: confirmed        # confirmed | assumed | historical
  evidence:
    - checkout-api/src/main/java/.../PricingClient.java:42
  checked_at: 2026-11-09
```

Anything not `confirmed` has to be re-read from code before the agent answers. This is the whole trick, and it is three lines of YAML.

**3. "Done" is not done.** A worker reporting success is not verification. Two workers agreeing is not verification either — they share a prior. orca-ledger makes the main session verify with code and tests before adopting, and hands the result to you *uncommitted* so you review the diff in your own editor and commit it yourself. The agent never commits to your branch.

## What you get

```
your-ledger/
├─ AGENTS.md          the contract: routing, permissions, record rules, search order
├─ CLAUDE.md          @AGENTS.md
├─ map/
│  ├─ systems.yaml       system ↔ repo ↔ responsibility
│  ├─ dependencies.yaml  who calls whom
│  └─ data.yaml          tables, events, readers, writers
├─ domains/           one file per area of your product
├─ work/<topic>/      state.md ledger, briefs, decisions
├─ knowledge/         cross-repo decisions, incidents, fixes
├─ rules/<repo>.md    rules a worker cannot discover on its own
├─ playbooks/         start, ledger, handoff, cross-agent, verify, cleanup
└─ scripts/ledger-status.py
```

`AGENTS.md` is picked up by Claude Code, Codex, Cursor, Gemini CLI and anything else that reads an agent contract; `CLAUDE.md` is a one-line include so Claude Code gets the same file.

The contract is in English — one copy, kept correct. The agent answers you in **your** language: at setup it picks up whichever language you are writing in and records it as a preference, so the harness has no translations to keep in sync and you still get replies in Korean, Japanese, German or whatever you asked in.

## The skills

| Skill | What it does |
|---|---|
| `orca-ledger` | Scaffolds the workspace from the template it ships with, picks up your scope and language, registers it with Orca |
| `orca-ledger-reconcile` | Writes the ledger before the resource exists, then reconciles it against real worktrees and Orca workers |
| `orca-ledger-handoff` | Mid-conversation topic switches, spawning a session for a new topic, resuming a closed one |

Install all three, or just the ones you want:

```bash
npx skills add sp-daewoon/orca-ledger --skill orca-ledger --agent claude-code
```

## Requirements

- [Orca](https://github.com/stablyai/orca) — `orca-ledger` is built on Orca's worktrees, workers, dispatches and session search. It is not a generic harness and does not try to be.
- Python 3.9+ (stdlib only)
- git

## Design notes

- **Nothing is copied.** Content that lives in a repo is referenced by path, never duplicated here. The workspace holds only what spans repos.
- **The ledger is written first.** Before the worktree, before the worker. A spawn that fails still leaves you a record of the orphan.
- **Permissions are tiered, not binary.** Reading, editing a checkout, committing to a worker branch, and pushing are four different levels of trust. The contract spells out which need you.
- **Local by default.** No remote is added. Your workspace records how your company's systems fit together; that is usually not something to push to a public host by accident.

Longer rationale, including what was tried and discarded: [docs/why.md](docs/why.md).

한국어 안내: [docs/ko/README.md](docs/ko/README.md)

## Status

v0. It is in daily use by its author across two workspaces, which is a sample size of one. If you try it and it does not fit how you work, an issue describing the mismatch is more useful than a patch.

## License

MIT
