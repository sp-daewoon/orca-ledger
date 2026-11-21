"""Unit tests for the template's scripts/ledger-lint.py. Run: python3 -m unittest discover tests"""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/orca-ledger/template/scripts/ledger-lint.py"
spec = importlib.util.spec_from_file_location("ledger_lint", SCRIPT)
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)

TODAY = date(2026, 11, 21)

GOOD = """---
id: payments-retry
domain: payments
stage: working
next: run the integration tests
waiting_on: none
owner: operator
repos: [checkout-api, pricing-engine]
updated: 2026-11-20 10:00
verified_at:
---

# payments-retry
"""


class Workspace:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for d in ("work", "map", "domains", "knowledge"):
            (self.root / d).mkdir()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def run(self):
        return lint.lint(self.root, TODAY)

    def messages(self):
        return [f"{lvl} {where} {msg}" for lvl, where, msg in self.run().items]


class FrontmatterTest(unittest.TestCase):
    def test_parses_scalars_and_lists(self):
        fm = lint.frontmatter(GOOD)
        self.assertEqual(fm["stage"], "working")
        self.assertEqual(fm["repos"], ["checkout-api", "pricing-engine"])
        self.assertEqual(fm["verified_at"], "")

    def test_block_list_and_comment(self):
        fm = lint.frontmatter("---\nrepos:\n  - a\n  - b\nstage: done  # finished\n---\n")
        self.assertEqual(fm, {"repos": ["a", "b"], "stage": "done"})

    def test_no_or_unterminated_frontmatter(self):
        self.assertIsNone(lint.frontmatter("# title\n"))
        self.assertIsNone(lint.frontmatter("---\nid: x\n"))

    def test_legacy_header_is_normalised(self):
        fields, has_fm = lint.ledger_fields("# t\n\n- stage: brief\n- next: read\n- waiting on user: no\n"
                                            "- session: claude abc `/x`\n- updated: 2026-11-01 09:00\n")
        self.assertFalse(has_fm)
        self.assertEqual(fields["stage"], "brief")
        self.assertEqual(fields["waiting_on"], "no")
        self.assertEqual(fields["owner"], "claude abc `/x`")

    def test_parse_date(self):
        self.assertEqual(lint.parse_date("2026-11-20 10:00"), date(2026, 11, 20))
        self.assertEqual(lint.parse_date("2026-11-20T10:00:00Z"), date(2026, 11, 20))
        self.assertIsNone(lint.parse_date("yesterday"))
        self.assertIsNone(lint.parse_date("2026-13-01"))


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.tmp.cleanup)

    def test_good_ledger_is_clean(self):
        self.ws.write("work/payments-retry/state.md", GOOD)
        self.assertEqual(self.ws.run().items, [])

    def test_domain_grouping_is_found(self):
        self.ws.write("work/payments/retry/state.md", GOOD.replace("stage: working", "stage: bogus"))
        self.assertTrue(any("work/payments/retry/state.md" in m and "bogus" in m for m in self.ws.messages()))

    def test_stage_enum_and_missing_keys(self):
        self.ws.write("work/t/state.md", "---\nid: t\nstage: submitted\nupdated: 2026-11-20\n---\n")
        msgs = self.ws.messages()
        self.assertTrue(any("error" in m and "submitted" in m for m in msgs))
        self.assertTrue(any("missing `owner`" in m for m in msgs))
        self.assertTrue(any("`next` is empty" in m for m in msgs))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lint.main(["--root", str(self.ws.root), "--today", "2026-11-21"]), 1)

    def test_question_mark_next_is_empty(self):
        self.ws.write("work/t/state.md", GOOD.replace("next: run the integration tests", "next: ?"))
        self.assertTrue(any("`next` is empty" in m for m in self.ws.messages()))

    def test_done_needs_no_next(self):
        self.ws.write("work/t/state.md", GOOD.replace("stage: working", "stage: done")
                      .replace("next: run the integration tests", "next:"))
        self.assertEqual(self.ws.run().items, [])

    def test_stale_working(self):
        self.ws.write("work/t/state.md", GOOD.replace("2026-11-20 10:00", "2026-11-01"))
        self.assertTrue(any("not updated for 20 days" in m for m in self.ws.messages()))

    def test_bad_dates(self):
        self.ws.write("work/t/state.md", GOOD.replace("2026-11-20 10:00", "last week")
                      .replace("verified_at:", "verified_at: soon"))
        msgs = self.ws.messages()
        self.assertTrue(any("`updated` is not a date" in m for m in msgs))
        self.assertTrue(any("`verified_at` is not a date" in m for m in msgs))

    def test_bloat(self):
        self.ws.write("work/t/state.md", GOOD + "- log line\n" * 600)
        self.assertTrue(any("move history to log.md" in m for m in self.ws.messages()))

    def test_legacy_ledger_warns_only(self):
        self.ws.write("work/t/state.md", "# t\n\n- stage: user review\n- next: wait\n- updated: 2026-11-20\n")
        report = self.ws.run()
        self.assertEqual(report.errors, [])
        self.assertTrue(any("v1 ledger" in m for _, _, m in report.items))

    def test_archive_rule(self):
        closed = GOOD.replace("stage: working", "stage: closed").replace("2026-11-20 10:00", "2026-09-01")
        self.ws.write("work/old/state.md", closed)
        self.ws.write("work/_archive/older/state.md", closed)
        msgs = self.ws.messages()
        self.assertTrue(any("work/old/state.md" in m and "_archive" in m for m in msgs))
        self.assertFalse(any("older" in m for m in msgs))


class FactsTest(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.tmp.cleanup)

    def test_map_staleness_and_dead_path(self):
        self.ws.write("map/systems.yaml", (
            "# comment\n"
            "- name: fresh\n  status: confirmed\n  checked_at: 2026-11-10\n"
            "- name: stale\n  path: /definitely/not/here\n  status: confirmed\n  checked_at: 2026-09-01\n"
            "- name: old-but-assumed\n  status: assumed\n  checked_at: 2025-01-01\n"
            "- name: undated\n  status: confirmed\n"
        ))
        msgs = self.ws.messages()
        self.assertTrue(any("systems.yaml:5" in m and "81 days" in m for m in msgs))
        self.assertTrue(any("path is gone: /definitely/not/here" in m for m in msgs))
        self.assertTrue(any("systems.yaml:12" in m and "checked_at" in m for m in msgs))
        self.assertEqual(len(msgs), 3)

    def test_notes(self):
        self.ws.write("knowledge/a.md", "---\nstatus: confirmed\nchecked_at: 2026-01-01\n---\nsee `/no/such/file`\n")
        self.ws.write("domains/b.md", "# b\n\n**status:** confirmed\n**checked_at:** 2026-11-19\n")
        msgs = self.ws.messages()
        self.assertTrue(any("knowledge/a.md" in m and "days ago" in m for m in msgs))
        self.assertTrue(any("path is gone: /no/such/file" in m for m in msgs))
        self.assertFalse(any("domains/b.md" in m for m in msgs))


if __name__ == "__main__":
    unittest.main()
