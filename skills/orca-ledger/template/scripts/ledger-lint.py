#!/usr/bin/env python3
"""Lint the records of an orca-ledger workspace.

Read-only. It reports; it never changes a file.

Checks:
  - work/**/state.md frontmatter: required keys, stage enum, empty `next`,
    `updated` that is not a date, a `working` ledger untouched for too long,
    a state.md that has grown past the size budget (the log belongs in log.md)
  - map/*.yaml, domains/*.md, knowledge/*.md: `confirmed` entries whose
    `checked_at` is older than the confirmation window, or missing
  - dead paths: absolute `path:` values in map/ and backticked absolute paths
    in domains/ and knowledge/ that no longer exist
  - closed topics past the archive window that are not under work/_archive/

Exit status is 1 when there is at least one `error`, otherwise 0. Warnings
never fail the run, so it is safe to call from ledger-status.py.

    python3 scripts/ledger-lint.py [--root PATH] [--today YYYY-MM-DD]
"""
import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

STAGES = ("brief", "working", "verifying", "user-review", "waiting-external", "done", "closed")
REQUIRED = ("id", "stage", "next", "owner", "updated")
FINISHED = ("done", "closed")

CONFIRM_DAYS = 30      # a `confirmed` fact older than this must be re-read
WORKING_DAYS = 7       # a `working` ledger untouched this long is suspect
ARCHIVE_DAYS = 30      # a `closed` topic older than this moves to work/_archive/
STATE_BUDGET = 4096    # bytes; the rest belongs in log.md / decisions.md

ARCHIVE = "_archive"


# ---------------------------------------------------------------- parsing

def parse_scalar(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [v.strip().strip("'\"") for v in raw[1:-1].split(",") if v.strip()]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def frontmatter(text):
    """Return the flat `key: value` frontmatter of a Markdown file, or None.

    Only the subset the ledger uses: scalars, inline lists `[a, b]`, and
    block lists of `- item`. Comments after ` #` are dropped.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        stripped = re.sub(r"\s+#.*$", "", line).rstrip()
        if not stripped.strip():
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", stripped)
        if m:
            key = m.group(1)
            data[key] = parse_scalar(m.group(2)) if m.group(2) else ""
        elif key and stripped.lstrip().startswith("- "):
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(parse_scalar(stripped.lstrip()[2:]))
    return None  # unterminated


def legacy_field(text, name):
    m = re.search(rf"^- {name}: (.*)$", text, re.M)
    return m.group(1).strip() if m else None


def ledger_fields(text):
    """Frontmatter if present, else the v1 `- key: value` header, normalised."""
    fm = frontmatter(text)
    if fm is not None:
        return fm, True
    legacy = {}
    for key, name in (("stage", "stage"), ("next", "next"), ("waiting_on", "waiting on user"),
                      ("owner", "session"), ("updated", "updated")):
        value = legacy_field(text, name)
        if value is not None:
            legacy[key] = value
    return legacy, False


def parse_date(value):
    """`YYYY-MM-DD`, optionally followed by a time; anything else is None."""
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|[ T])", value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def yaml_entries(text):
    """Split a map/*.yaml file into its top-level `- ` entries as flat dicts."""
    entries, current = [], None
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#") or not line.strip():
            continue
        m = re.match(r"^- (\w[\w-]*):\s*(.*)$", line)
        if m:
            current = {"_line": lineno, m.group(1): m.group(2).strip()}
            entries.append(current)
            continue
        m = re.match(r"^\s+(\w[\w-]*):\s*(.*)$", line)
        if m and current is not None:
            current[m.group(1)] = re.sub(r"\s+#.*$", "", m.group(2)).strip()
    return entries


# ---------------------------------------------------------------- checks

class Report:
    def __init__(self):
        self.items = []

    def add(self, level, where, message):
        self.items.append((level, where, message))

    @property
    def errors(self):
        return [i for i in self.items if i[0] == "error"]

    def lines(self):
        return [f"{level}: {where}: {message}" for level, where, message in self.items]


def ledgers(root):
    """Every work/**/state.md, as (topic, path, archived)."""
    work = root / "work"
    for path in sorted(work.glob("**/state.md")):
        rel = path.parent.relative_to(work)
        archived = rel.parts[:1] == (ARCHIVE,)
        yield str(rel), path, archived


def check_ledger(topic, path, text, today, report, archived=False):
    where = f"work/{topic}/state.md"
    fields, has_fm = ledger_fields(text)
    if not has_fm:
        report.add("warn", where, "no frontmatter (v1 ledger) — migrate per docs/migrating-to-v2.md in orca-ledger")
    else:
        for key in REQUIRED:
            if key not in fields:
                report.add("error", where, f"missing `{key}`")
    stage = fields.get("stage")
    if stage is None:
        report.add("error", where, "no stage")
    elif stage not in STAGES:
        level = "error" if has_fm else "warn"
        report.add(level, where, f"stage `{stage}` is not one of {'|'.join(STAGES)}")
    nxt = fields.get("next")
    if stage not in FINISHED and (nxt is None or str(nxt).strip() in ("", "?", "-", "none", "tbd", "TBD")):
        report.add("error", where, "`next` is empty for an open topic")
    updated = parse_date(fields.get("updated"))
    if "updated" in fields and updated is None:
        report.add("error", where, f"`updated` is not a date: {fields.get('updated')!r}")
    if updated and stage == "working" and (today - updated).days > WORKING_DAYS:
        report.add("warn", where, f"stage working but not updated for {(today - updated).days} days")
    if has_fm and fields.get("verified_at") not in (None, ""):
        if parse_date(fields["verified_at"]) is None:
            report.add("error", where, f"`verified_at` is not a date: {fields['verified_at']!r}")
    size = len(text.encode())
    if size > STATE_BUDGET:
        report.add("warn", where, f"{size} bytes (budget {STATE_BUDGET}) — move history to log.md")
    if stage == "closed" and not archived and updated and (today - updated).days > ARCHIVE_DAYS:
        report.add("warn", where, f"closed {(today - updated).days} days ago — move to work/{ARCHIVE}/")


def check_fact(where, status, checked_at, today, report):
    if status != "confirmed":
        return
    checked = parse_date(checked_at)
    if checked is None:
        report.add("error", where, "confirmed without a valid `checked_at`")
    elif (today - checked).days > CONFIRM_DAYS:
        report.add("warn", where, f"confirmed {(today - checked).days} days ago — re-read the code "
                                  f"or downgrade to assumed")


def check_map(root, today, report):
    for path in sorted((root / "map").glob("*.yaml")):
        for entry in yaml_entries(path.read_text()):
            where = f"map/{path.name}:{entry['_line']}"
            check_fact(where, entry.get("status"), entry.get("checked_at"), today, report)
            p = entry.get("path", "").strip("'\"`")
            if p.startswith("/") and not Path(p).exists():
                report.add("warn", where, f"path is gone: {p}")


def md_status(text):
    """status / checked_at of a knowledge or domain note: frontmatter, or `**key:** value` lines."""
    fm = frontmatter(text) or {}
    status, checked = fm.get("status"), fm.get("checked_at")
    if status is None:
        m = re.search(r"^\*\*status:\*\*\s*(\w+)", text, re.M)
        status = m.group(1) if m else None
    if checked is None:
        m = re.search(r"^\*\*checked_at:\*\*\s*(\S+)", text, re.M)
        checked = m.group(1) if m else None
    return status, checked


def check_notes(root, today, report):
    for folder in ("domains", "knowledge"):
        for path in sorted((root / folder).glob("**/*.md")):
            text = path.read_text()
            where = f"{folder}/{path.relative_to(root / folder)}"
            status, checked = md_status(text)
            check_fact(where, status, checked, today, report)
            for p in sorted(set(re.findall(r"`(/[^`\s]+)`", text))):
                if not Path(p).exists():
                    report.add("warn", where, f"path is gone: {p}")


def lint(root, today=None):
    root = Path(root)
    today = today or date.today()
    report = Report()
    for topic, path, archived in ledgers(root):
        check_ledger(topic, path, path.read_text(), today, report, archived)
    check_map(root, today, report)
    check_notes(root, today, report)
    return report


def workspace_root():
    out = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse",
         "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip()).parent


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", help="workspace folder (default: the main folder of this script's repo)")
    ap.add_argument("--today", help="YYYY-MM-DD, for reproducible runs")
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else workspace_root()
    today = date.fromisoformat(args.today) if args.today else None
    report = lint(root, today)
    for line in report.lines() or ["none"]:
        print(line)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
