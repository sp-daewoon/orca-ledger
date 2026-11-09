#!/usr/bin/env python3
"""Reconcile the work/*/state.md ledgers against real worktrees and Orca workers.

Read-only. It never creates, changes or deletes anything.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# Run from a worktree and still read the records in the main folder.
ROOT = Path(subprocess.run(
    ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse",
     "--path-format=absolute", "--git-common-dir"],
    capture_output=True, text=True, check=True,
).stdout.strip()).parent

ORCA_FALLBACKS = [
    "/Applications/Orca.app/Contents/Resources/bin/orca",
    str(Path.home() / ".local/bin/orca"),
]


def find_orca():
    found = shutil.which("orca") or next((p for p in ORCA_FALLBACKS if os.access(p, os.X_OK)), None)
    if not found:
        sys.exit(
            "orca CLI not found. orca-hq is built on Orca.\n"
            "Install Orca (https://github.com/stablyai/orca), or set ORCA_BIN to its path."
        )
    return found


ORCA = os.environ.get("ORCA_BIN") or find_orca()


def orca(*args):
    """Call the Orca CLI and return its result payload, or None if it failed."""
    out = subprocess.run([ORCA, *args, "--json"], capture_output=True, text=True)
    try:
        payload = json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    return payload.get("result")


def cells(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def parse_rows(text):
    """Group each table's rows under its own header."""
    rows, header = [], None
    for line in text.splitlines():
        if not line.startswith("|"):
            header = None
        elif header is None:
            header = cells(line)
        elif not set(line) <= set("|-: "):
            rows.append(dict(zip(header, cells(line))))
    return rows


def field(text, name):
    m = re.search(rf"^- {name}: (.*)$", text, re.M)
    return m.group(1).strip() if m else "?"


def head(path):
    out = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip()


def expiry_notices():
    """Warn when a `**expires:** YYYY-MM-DD` line in knowledge/ is within 14 days."""
    notices = []
    for path in sorted(ROOT.glob("knowledge/*.md")):
        for m in re.finditer(r"\*\*expires:\*\* (\d{4}-\d{2}-\d{2})", path.read_text()):
            left = (date.fromisoformat(m.group(1)) - date.today()).days
            if left <= 14:
                notices.append(f"{path.name}: expires in {left} day(s) ({m.group(1)}) — tell the user to renew")
    return notices or ["none"]


def main():
    texts = {p.parent.name: p.read_text() for p in sorted(ROOT.glob("work/*/state.md"))}
    all_text = "\n".join(texts.values())

    print("[alert]")
    for notice in expiry_notices():
        print(f"  {notice}")

    print("[open]")
    open_topics = {t: x for t, x in texts.items() if field(x, "stage") != "closed"}
    for t, x in open_topics.items():
        print(f"  {t} | {field(x, 'stage')} | next: {field(x, 'next')} "
              f"| waiting on user: {field(x, 'waiting on user')}")
    if not open_topics:
        print("  none")

    print("[sessions]")
    for t, x in texts.items():
        print(f"  {t} | {field(x, 'stage')} | {field(x, 'session')}")
    if not texts:
        print("  none")

    print("[unlisted worktrees]")
    listed = orca("worktree", "list")
    if listed is None:
        print("  could not read Orca worktrees (is Orca running?)")
    else:
        unknown = [
            w for w in listed["worktrees"]
            if not w.get("isMainWorktree") and f"`{w['path']}`" not in all_text
        ]
        for w in unknown:
            print(f"  {w['path']} ({w['branch'].removeprefix('refs/heads/')})")
        if not unknown:
            print("  none")

    print("[ledger mismatch]")
    found = False
    for t, x in texts.items():
        for row in parse_rows(x):
            m = re.fullmatch(r"`(/[^`]+)`", row.get("path", ""))
            if not m or "state" not in row:
                continue
            path, state = m.group(1), row["state"]
            exists = Path(path).exists()
            problem = None
            if state == "deleted" and exists:
                problem = "recorded as deleted but still present"
            elif state not in ("deleted", "planned") and not exists:
                problem = f"state is {state} but the path is gone"
            elif exists and row.get("last commit", "").strip("`-"):
                recorded = row["last commit"].strip("`")
                if not head(path).startswith(recorded):
                    problem = f"ledger {recorded}, actual {head(path)[:9]}"
            if problem:
                found = True
                print(f"  {t} {path}: {problem}")
    if not found:
        print("  none")

    print("[unreleased workers]")
    found = False
    for t, x in open_topics.items():
        # Rows the ledger believes are still running, so we can tell a released
        # worker apart from a run Orca has never heard of.
        working = {
            (row.get("run", ""), row.get("dispatch", ""))
            for row in parse_rows(x)
            if row.get("state") == "working" and row.get("run", "").startswith("run_")
        }
        for run in sorted(set(re.findall(r"run_[0-9a-f]+", x))):
            result = orca("orchestration", "worker-list", "--run", run)
            if result is None:
                print(f"  {t} {run}: could not read workers")
                found = True
                continue
            seen = set()
            for w in result["workers"]:
                res = w["resource"]
                path = res["worktreeId"].split("::")[-1]
                seen.add(w["dispatchId"])
                # If the worktree is already gone, only Orca's record remains.
                if w["terminalState"] != "released" and Path(path).exists():
                    found = True
                    print(f"  {t} {w['dispatchId']} {w['terminalState']} "
                          f"{res.get('retainedReason')}: {path}")
            # Orca answers an unknown run with an empty list, not an error.
            # Without this, a stale run id in the ledger reads as "all clear".
            for ledger_run, dispatch in sorted(working):
                if ledger_run == run and dispatch not in seen:
                    found = True
                    print(f"  {t} {dispatch or '(no dispatch)'}: ledger says working, "
                          f"but {run} has no such worker in Orca")
    if not found:
        print("  none")


if __name__ == "__main__":
    main()
