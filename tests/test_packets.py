import re
import tempfile
import unittest
from pathlib import Path

from badgr_funding import finance_report

ROOT = Path(__file__).resolve().parent.parent
PITCH = ROOT / "drafts/nsf_project_pitch.md"
LIMITS = {"1. The Technology Innovation": 3500, "2. The Technical Objectives and Challenges": 3500,
          "3. The Market Opportunity": 1750, "4. The Company and Team": 1750}
TAG = re.compile(r"\s*\[[CA]-[A-Z]+-\d{2}\]")


def pitch_sections():
    sections, current = {}, None
    for line in PITCH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {k: TAG.sub("", "\n".join(v)).strip() for k, v in sections.items()}


class NsfPitchTests(unittest.TestCase):
    def test_all_four_sections_present_and_within_limits(self):
        sections = pitch_sections()
        for name, limit in LIMITS.items():
            self.assertIn(name, sections)
            self.assertGreater(len(sections[name]), 200, name)
            self.assertLessEqual(len(sections[name]), limit, f"{name}: {len(sections[name])} > {limit}")

    def test_metric_stays_scoped(self):
        text = pitch_sections()["1. The Technology Innovation"]
        self.assertIn("controlled test dated 2026-08-12", text)


class FinanceReportTests(unittest.TestCase):
    def test_generate_blocks_on_missing_inputs_and_computes_scenarios(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            inputs = tmp / "in.csv"
            inputs.write_text("field,value,status,evidence\n2025_revenue,5550.00,verified,x\ncash_on_hand,,missing,\n")
            finance_report.generate(tmp / "out", inputs, tmp / "private")
            self.assertIn("BLOCKED", (tmp / "out/cashflow_12mo_base.csv").read_text())
            self.assertIn("Status: BLOCKED", (tmp / "out/repayment_analysis.md").read_text())
            comp = (tmp / "out/loan_offer_comparison.csv").read_text()
            self.assertIn("$208.33", comp)
            self.assertIn("$302.35", comp)
            self.assertIn("$550.00", comp)

    REAL = ("field,value,status,evidence\ncash_on_hand,1234.56,verified,x\n"
            "monthly_business_expenses,500.00,verified,x\nexisting_debt_payments,77.77,verified,x\n"
            "2026_ytd_revenue,9000.00,verified,x\n2026_ytd_through,2026-09-30,verified,x\n")

    def test_real_figures_only_in_private_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            inputs = tmp / "in.csv"
            inputs.write_text(self.REAL)
            finance_report.generate(tmp / "out", inputs, tmp / "private")
            tracked = "".join(p.read_text() for p in (tmp / "out").iterdir())
            for value in ("1,234.56", "77.77", "1,000.00"):  # inputs and derived monthly revenue
                self.assertNotIn(value, tracked)
            self.assertIn("COMPUTED_PRIVATELY", (tmp / "out/cashflow_12mo_base.csv").read_text())
            self.assertIn("$1,000.00", (tmp / "private/cashflow_12mo_base.csv").read_text())  # 9000 / 9 months
            self.assertIn("coverage", (tmp / "private/repayment_analysis_private.md").read_text())

    def test_ytd_without_through_date_blocks_and_is_date_independent(self):
        import datetime as dt
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            inputs = tmp / "in.csv"
            inputs.write_text(self.REAL.replace("2026_ytd_through,2026-09-30", "2026_ytd_through,"))
            finance_report.generate(tmp / "out", inputs, tmp / "private", ref=dt.date(2027, 1, 5))
            self.assertIn("monthly_operating_revenue", (tmp / "out/cashflow_12mo_base.csv").read_text())
            inputs.write_text(self.REAL)
            for ref in (dt.date(2027, 1, 5), dt.date(2026, 11, 1)):  # January must not break
                finance_report.generate(tmp / "out", inputs, tmp / "private", ref=ref)
                self.assertIn("COMPUTED_PRIVATELY", (tmp / "out/cashflow_12mo_base.csv").read_text())


class DocumentMarkerTests(unittest.TestCase):
    def test_checklists_and_finance_docs_have_draft_date_missing_inputs(self):
        docs = [*sorted((ROOT / "drafts/checklists").glob("*.md")), *sorted((ROOT / "finance").glob("*.md"))]
        self.assertTrue(docs)
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("DRAFT", text.splitlines()[0], path.name)
            self.assertRegex(text, r"\d{4}-\d{2}-\d{2}", path.name)
            self.assertIn("## Missing inputs", text, path.name)

    def test_tracked_template_stays_blank(self):
        import csv
        with open(ROOT / "templates/financial_inputs.csv", newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if row["field"] != "2025_revenue":  # verified business figure (C-FIN-02)
                    self.assertEqual(row["value"].strip(), "", row["field"])


if __name__ == "__main__":
    unittest.main()
