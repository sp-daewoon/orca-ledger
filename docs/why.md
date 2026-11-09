# Why it looks like this

Design notes, including the parts that were tried and dropped. If you are deciding whether to adopt this, the disagreements are more useful than the features.

## The problem it was built for

One person, several repositories, agents running in parallel in Orca. Three failures showed up repeatedly and none of them were model quality.

**Resources with no owner.** Spawn a worker, collect the result, move on. A week later: worktrees whose purpose nobody remembers, workers Orca still holds open, a branch that will not check out because a forgotten worktree holds it. Each is trivial alone. Together they make you stop trusting the tooling.

**Facts that rot.** A note written six weeks ago gets read back as current truth. The agent is not wrong to trust it — nothing told it the note had an age. This is worse than having no notes, because a confident wrong answer costs more than "I don't know".

**Unverified completion.** A worker reports success. The report is produced by the same process that did the work, so it carries no independent information. Running two agents and seeing them agree feels like verification and is not: they share training data, prompt and brief, so they fail together on exactly the cases you most need to catch.

## What was decided

### Markdown, not a service

No daemon, no database, no account. A git repository of Markdown plus one stdlib Python script.

The reason is not minimalism. The workspace's content *is* the agent's instructions, so whatever holds it has to be readable and editable by the user without a tool in the way, and diffable in review. A database would have made the ledger easier to query and the contract impossible to review.

The cost is real: no transactions, no concurrent-write protection. Two sessions writing the same `state.md` will clobber each other. That is handled socially — one owner per ledger, other sessions append a log line — which is weaker than a lock and was accepted anyway.

### Three fields, not a confidence score

Every fact carries `status`, `evidence`, `checked_at`, and the contract says only `confirmed` may be asserted.

A numeric confidence score was considered and dropped. Models produce confidence numbers freely and they do not mean anything stable. `confirmed` has a checkable definition — "I read this in the code, and here is the file and line" — and an agent can be held to it. `assumed` is not a failure state; asserting an assumption as a fact is.

What this does not do: `confirmed` means it is in the code, not that it is what runs in production. Config servers and environment overrides are invisible to this. The template says so in the map's header comment rather than pretending otherwise.

### The ledger is written before the resource

A row goes in with state `planned` before `worker-start` is called. This looks like bureaucracy until the first time a spawn half-fails and leaves a worktree behind with nothing pointing at it.

A ledger written after creation misses precisely the cases it exists for.

### Reconciliation reads, never writes

`ledger-status.py` compares the ledger with real worktrees and Orca workers, prints the differences, and stops. It does not clean up.

Automatic cleanup was rejected. The tool cannot tell a worktree the user created by hand from an orphan an agent abandoned — the only signal is the ledger, and the ledger is exactly what is unreliable when there is a mismatch. So an unlisted worktree is reported to the user, every time, even when it is obvious.

### Adopted work arrives uncommitted

The agent puts the result in the user's checkout and stops. The user reads the diff in their own editor, drops what they do not want, and commits.

This is slower than letting the agent commit, and it is the step people remove first. Keeping it is the difference between reviewing a change and reviewing a change that is already in your history.

### Permissions in tiers

Reading, editing a checkout, committing to an agent branch, and pushing are four different levels of trust. A single allow/deny switch forces a choice between an agent that interrupts constantly and one that pushes to main.

The boundary that matters: the agent may freely do anything it can undo, and must ask before anything that leaves the machine or touches the user's history.

### Built on Orca, on purpose

This could have been made tool-agnostic. It was not.

The orphan detection is the most useful thing here, and it exists only because Orca exposes dispatch and worker state over a CLI with `--json`. An abstraction layer over "any orchestrator" would have reduced that feature to `git worktree list`, which finds nothing interesting. Narrow and actually working beat broad and advisory.

The consequence: without Orca, this is a Markdown convention and a script that exits with an error.

## What is still unresolved

- **Concurrent writes to one ledger.** Handled by convention. A real answer is probably per-session log files merged on read, which has not been built.
- **Nothing expires on its own.** `checked_at` records when a fact was confirmed, but nothing flags a `confirmed` entry that is now eight months old. A staleness threshold per entry type is the obvious next step.
- **The map is only as good as the work done so far.** It fills in as repositories get touched, which means early on the honest answer to most questions is "not looked at yet". That was chosen over seeding it with guesses, but it does make the first weeks feel empty.
- **Single-author sample.** Every rule here comes from one person's workflow across two workspaces. Several are probably local habits wearing the costume of a principle. Issues saying which are more valuable than patches.
