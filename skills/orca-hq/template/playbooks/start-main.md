# Starting a main session

The main session starts in `{{HQ_PATH}}`, in an Orca terminal.

## Claude

```text
orca agent launch --agent claude --worktree path:{{HQ_PATH}} --prompt "<request>"
```

Running `claude` directly in an Orca terminal works too.

## Codex

Run it directly in an Orca terminal:

```text
codex -c 'shell_environment_policy.inherit="all"' -c 'shell_environment_policy.include_only=["*"]' "<request>"
```

Those options matter. A main session started with `orca agent launch --agent codex`, or with a bare `codex`, cannot create a Run: `ORCA_TERMINAL_HANDLE` is missing from the command environment and the call is refused with `no_active_sender_terminal`. Codex does not need the options when it is the *worker*.

| How it was started | Result |
|---|---|
| `orca agent launch --agent codex` | Run creation refused |
| `codex` in a terminal, before sandbox rules | `orca` calls blocked, sandbox EPERM |
| `codex` in a terminal, after sandbox rules | Run creation refused |
| `codex` in a terminal, with the options above | Both workers started and their results collected |

Status: observed on one machine, 2026-11-02. Re-check on yours and correct this file.

Codex also needs a rule allowing `orca` in `~/.codex/rules/default.rules`.

## Skills

```text
orca skills install --skill orchestration --skill orca-cli --agent claude-code
```

The agent target is `claude-code`, not `claude` — `claude` is rejected with `Invalid agents: claude`.
