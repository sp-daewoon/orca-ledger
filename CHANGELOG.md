# Changelog

## Unreleased — ledger v2

Existing workspaces keep working; see [docs/migrating-to-v2.md](docs/migrating-to-v2.md) to upgrade.

- **Frontmatter ledgers.** `state.md` carries YAML frontmatter: `id`, `domain`, `stage`, `next`, `waiting_on`, `owner`, `repos`, `updated`, `verified_at`. `stage` is an enum: `brief | working | verifying | user-review | waiting-external | done | closed`. v1 bullet headers are still read.
- **Split ledger.** `state.md` holds the current state only; history goes to append-only `log.md`, decisions to `decisions.md`.
- **Domains.** Topics may be grouped as `work/<domain>/<topic>/`; `domains/<domain>.md` is the knowledge module for an area. Closed topics older than 30 days move to `work/_archive/`.
- **`scripts/ledger-lint.py`** (stdlib). Checks the frontmatter schema and stage enum, empty `next`, stale `working` ledgers, ledger size, `confirmed` facts whose `checked_at` is over 30 days old, dead paths, and unarchived closed topics. `ledger-status.py` prints it as `[lint]`.
- **`confirmed` expires** after 30 days without a re-read.
- **Owner model.** `owner` replaces `session`. Optional operator model: one operator agent owns every ledger, delegated sessions own one temporarily.
- **Records are committed every turn**, by the owner, with the files named.
- Tests: `python3 -m unittest discover tests`, run in CI.
