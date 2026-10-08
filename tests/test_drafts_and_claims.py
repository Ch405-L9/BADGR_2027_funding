import csv
import re
import unittest
from pathlib import Path

from badgr_funding.draft_lint import lint_dir, lint_text

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "context/claims_ledger.csv"
URL_CHECKS = ROOT / "context/url_checks.csv"

LEDGER_COLUMNS = ["claim_id", "category", "exact_wording", "source", "source_date", "verified_at",
                  "verification_method", "verification_status", "scope", "confidence", "permitted_reuse"]
STATUSES = {"APPLICANT_REPORTED", "SELF_CERTIFIED", "PARTIAL", "UNVERIFIED_NOT_PUBLIC",
            "VERIFIED_ISSUER_PAGE", "VERIFIED_SOURCE_DOC", "VERIFIED_OFFICIAL_PAGE", "DISPUTED", "SUPERSEDED", "RESOLVES", "RESOLVES_MINIMAL", "NOT_CHECKED", "PROPOSED"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class ClaimsLedgerTests(unittest.TestCase):
    def setUp(self):
        self.rows = read_csv(LEDGER)

    def test_columns(self):
        with open(LEDGER, newline="", encoding="utf-8") as fh:
            self.assertEqual(next(csv.reader(fh)), LEDGER_COLUMNS)

    def test_ids_unique_and_well_formed(self):
        ids = [r["claim_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        for cid in ids:
            self.assertRegex(cid, r"^C-[A-Z]+-\d{2}$")

    def test_statuses_known_and_reuse_stated(self):
        for r in self.rows:
            self.assertIn(r["verification_status"], STATUSES, r["claim_id"])
            self.assertTrue(r["permitted_reuse"].strip(), r["claim_id"])

    def test_verified_claims_have_date_and_method(self):
        for r in self.rows:
            if r["verification_status"] in {"VERIFIED_ISSUER_PAGE", "PARTIAL", "RESOLVES", "UNVERIFIED_NOT_PUBLIC"}:
                self.assertRegex(r["verified_at"], r"^\d{4}-\d{2}-\d{2}$", r["claim_id"])
                self.assertNotEqual(r["verification_method"], "none", r["claim_id"])

    def test_designation_never_marked_certified(self):
        des = [r for r in self.rows if r["category"] == "designation"]
        self.assertTrue(des)
        for r in des:
            self.assertEqual(r["verification_status"], "SELF_CERTIFIED")
            self.assertIn("never as SBA 8(a)", r["permitted_reuse"])

    def test_metric_claim_scoped_to_controlled_test(self):
        metric = next(r for r in self.rows if r["claim_id"] == "C-PROJ-02")
        self.assertIn("controlled", metric["exact_wording"])
        self.assertIn("never as general accuracy", metric["permitted_reuse"])

    def test_url_checks_reference_ledger(self):
        ids = {r["claim_id"] for r in self.rows}
        for r in read_csv(URL_CHECKS):
            for cid in r["claim_ids"].split(";"):
                self.assertIn(cid, ids, r["url"])


class DraftLintTests(unittest.TestCase):
    def test_all_drafts_pass(self):
        results = lint_dir(ROOT / "drafts", LEDGER)
        self.assertTrue(results, "no drafts found")
        self.assertEqual({k: v for k, v in results.items() if v}, {})

    def test_drafts_use_no_assumed_pronouns(self):
        for path in (ROOT / "drafts").glob("*.md"):
            self.assertFalse(re.search(r"\b(he|she|his|hers|him)\b", path.read_text(), re.I), path.name)

    def test_uncited_line_fails(self):
        text = "# DRAFT x\nChecked 2026-10-08\n## Body\nUncited fact.\n## Missing inputs\n- x\n"
        self.assertTrue(any("no claim citation" in e for e in lint_text(text, {"C-BIZ-01"})))

    def test_unknown_id_fails(self):
        text = "# DRAFT x\nChecked 2026-10-08\n## Body\nFact [C-ZZZ-99]\n## Missing inputs\n"
        self.assertTrue(any("unknown claim id" in e for e in lint_text(text, {"C-BIZ-01"})))

    def test_banned_claims_fail_even_when_cited(self):
        ids = {"C-BIZ-01"}
        for bad in ("Our system is 100% accurate [C-BIZ-01]",
                    "We are an 8(a) certified firm [C-BIZ-01]",
                    "A certified MBE vendor [C-BIZ-01]",
                    "Our clients include Acme [C-BIZ-01]",
                    "This guarantees the grant award [C-BIZ-01]"):
            text = f"# DRAFT x\nChecked 2026-10-08\n## Body\n{bad}\n## Missing inputs\n"
            self.assertTrue(any("banned claim" in e for e in lint_text(text, ids)), bad)

    def test_ownership_percentage_allowed_but_accuracy_banned(self):
        ok = "# DRAFT x\nChecked 2026-10-08\n## Body\nSole member with 100% ownership. [C-BIZ-01]\n## Missing inputs\n"
        self.assertEqual(lint_text(ok, {"C-BIZ-01"}), [])
        for bad in ("Retrieval accuracy of 100% [C-BIZ-01]", "It is 100% reliable [C-BIZ-01]", "100 % accurate answers [C-BIZ-01]"):
            text = f"# DRAFT x\nChecked 2026-10-08\n## Body\n{bad}\n## Missing inputs\n"
            self.assertTrue(any("banned claim" in e for e in lint_text(text, {"C-BIZ-01"})), bad)

    def test_disputed_claims_blocked_in_drafts(self):
        from badgr_funding.draft_lint import disputed_ids
        self.assertTrue({"C-FIN-05", "C-FIN-06", "C-OFF-02"} <= disputed_ids(LEDGER))  # superseded estimates
        text = "# DRAFT x\nChecked 2026-10-08\n## Body\nReceipts were X. [C-FIN-02]\n## Missing inputs\n"
        self.assertTrue(any("excluded claim" in e for e in lint_text(text, {"C-FIN-02"}, excluded={"C-FIN-02"})))

    def test_negated_certification_statement_allowed(self):
        text = ("# DRAFT x\nChecked 2026-10-08\n## Body\n"
                "No SBA 8(a), third-party MBE or HUBZone certification is held. [C-BIZ-01]\n## Missing inputs\n")
        self.assertEqual(lint_text(text, {"C-BIZ-01"}), [])

    def _body(self, line):
        return f"# DRAFT x\nChecked 2026-10-08\n## Body\n{line}\n## Missing inputs\n"

    def test_metric_without_controlled_scope_fails(self):
        ids = {"C-PROJ-02"}
        ok = "In one controlled test dated August 12, 2026, 17 of 17 cases were useful. [C-PROJ-02]"
        self.assertEqual(lint_text(self._body(ok), ids), [])
        no_scope = "In one test dated August 12, 2026, 17 of 17 cases were useful. [C-PROJ-02]"
        self.assertTrue(any("missing scope" in e for e in lint_text(self._body(no_scope), ids)))
        no_date = "In a controlled test, 17 of 17 cases were useful. [C-PROJ-02]"
        self.assertTrue(any("missing scope" in e for e in lint_text(self._body(no_date), ids)))

    def test_excluded_claim_fails(self):
        errs = lint_text(self._body("Deployed 24 times. [C-PROJ-05]"), {"C-PROJ-05"})
        self.assertTrue(any("excluded claim" in e for e in errs))

    def test_metric_not_allowed_in_capability_statement(self):
        line = "A controlled test on 2026-08-12 found 17/17. [C-PROJ-02]"
        errs = lint_text(self._body(line), {"C-PROJ-02"}, "capability_statement.md")
        self.assertTrue(any("not allowed" in e for e in errs))

    def test_missing_draft_marker_and_section_fail(self):
        errs = lint_text("# Bio\nno date\n## Body\nx [C-BIZ-01]\n", {"C-BIZ-01"})
        self.assertEqual(len(errs), 3)


if __name__ == "__main__":
    unittest.main()
