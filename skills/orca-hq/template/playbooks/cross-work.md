# Cross-agent work

Giving the same brief to Codex and to Claude. Only when the user asks. The default is one session.

## 1. Write the brief

Search the map and past records, then write `work/<topic>/brief.md`: the goal, the repositories involved, references, and what counts as done.

What you hand a worker has to be workable on its own. State the target, the deliverable, the constraints, what it may change, and the evidence that proves it is finished.

Before you hand it over, check:

- **Repository rules:** where `rules/<repo>.md` exists, copy its content into the brief. Workers do not read this workspace.
- **Test commands:** do they actually run only the intended scope? In Gradle, `--tests` applies to the task immediately before it, so repeat it per task.
- **Known failures:** list the ones you already know about, so nobody re-runs the base commit to find them.
- **Toolchain:** is the version you specified actually on this machine?
- **Response contracts:** not just field names but where they sit in the payload — a wrapper type changes the path.
- **Order:** if the frontend depends on a backend contract, adopt the backend first and put that contract in the frontend brief.

## 2. Start the workers

Write the worker row as `planned` in `work/<topic>/state.md` first, then update it as you go. Follow `playbooks/work-state.md`.

```text
orca status --json
orca orchestration run-create --objective "<goal>" --json
```

Analysis runs in the same folder and changes no files:

```text
orca orchestration worker-start --spec "<brief>" --worktree <selector> --agent codex --json
orca orchestration worker-start --spec "<brief>" --worktree <selector> --agent claude --json
```

Implementation gets its own worktree and branch per agent, from the same base commit. Unless told otherwise, run `git fetch origin main` in the target repository first and base on `origin/main`.

```text
orca orchestration worker-start --spec "<brief>" --worktree new-top-level --repo <repo> --base-branch origin/main --name feature/<topic>-codex --comment "<description>" --agent codex --json
orca orchestration worker-start --spec "<brief>" --worktree new-top-level --repo <repo> --base-branch origin/main --name feature/<topic>-claude --comment "<description>" --agent claude --json
```

Check with `git worktree list` straight afterwards whether Orca prefixed the branch name — it has been observed adding an account prefix to `--name`.

If `worker-start` fails, do not just start it again. Read `failedStage` and `residualResources` in the response first.

## 3. Collect the results

```text
orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms 900000 --json
orca orchestration reply --id <message_id> --body "<answer>" --json
orca orchestration worker-release --dispatch <dispatch_id> --json
orca orchestration check --ack <delivery_id> --wait --types "worker_done,escalation,question" --timeout-ms 900000 --json
```

- A timeout or an empty response is not a failure. Keep waiting.
- Three empty responses in a row: check with `orca orchestration worker-list --run <run_id> --json`.
- `liveness: live` does not mean the worker is working. A worker stopped by a model capacity error never sends `worker_done`. Read the terminal with `orca terminal read --terminal <handle> --limit 20`, and if it is stuck, resume it with `orca terminal send --terminal <handle> --text "<what to do next>" --enter`.
- Heartbeats are deliveries too. Even when you filter by type, queued deliveries can come back first — check and move on.
- Do not stop or restart a worker without solid evidence that it is stuck.

Then go to `playbooks/verify-and-adopt.md`.
