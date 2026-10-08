import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINDINGS = sorted((ROOT / "research").glob("phase*_findings_*.json"))
# Personal income detail lives only in private/; these markers must never appear in tracked outputs.
GENERIC_MARKERS = ("1099", "unemployment", "Roth", "W-2 wages")
PRIVATE_MARKERS_FILE = ROOT / "private/privacy_markers.txt"  # personal values live only in the gitignored file


def personal_markers():
    extra = []
    if PRIVATE_MARKERS_FILE.exists():
        extra = [l.strip() for l in PRIVATE_MARKERS_FILE.read_text().splitlines() if l.strip() and not l.startswith("#")]
    return [*GENERIC_MARKERS, *extra]


MARKER_EXEMPT = {"tests/test_research_data.py", "badgr_funding/export.py", "tests/test_phase5.py"}  # files that list markers in order to block them


def commit_eligible_files():
    """Tracked files plus untracked files git would add (i.e. not ignored)."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    return [f for f in out if f and f not in MARKER_EXEMPT]


class FindingsDataTests(unittest.TestCase):
    def test_findings_exist(self):
        self.assertTrue(FINDINGS)

    def test_admitted_rows_have_dated_official_source(self):
        for path in FINDINGS:
            for o in json.loads(path.read_text())["opportunities"]:
                if o.get("source_status", "UNVERIFIED_CURRENT") == "UNVERIFIED_CURRENT":
                    continue
                official = [s for s in o.get("sources", []) if s["kind"] == "official"]
                self.assertTrue(official, o["id"])
                for s in official:
                    self.assertRegex(s["checked_at"], r"^\d{4}-\d{2}-\d{2}T", o["id"])
                    self.assertTrue(s["method"], o["id"])
                self.assertTrue(o.get("source_checked_at"), o["id"])

    def test_criteria_tri_state_with_evidence(self):
        for path in FINDINGS:
            for o in json.loads(path.read_text())["opportunities"]:
                for c in o.get("criteria", []):
                    if c.get("private_key"):
                        self.assertNotIn("status", c, (o["id"], "private criteria must not carry a tracked status"))
                        self.assertEqual(c["evidence"], "owner-screened (private)")
                        self.assertIn(c["pass_when"], ("true", "false"))
                        continue
                    self.assertIn(c["status"], ("yes", "no", "unknown"), o["id"])
                    if c["status"] == "yes":
                        self.assertTrue(c.get("evidence"), (o["id"], c["criterion"]))

    def test_no_stale_seed_note_on_checked_rows(self):
        for path in FINDINGS:
            ids = {o["id"] for o in json.loads(path.read_text())["opportunities"]
                   if o.get("source_status", "UNVERIFIED_CURRENT") != "UNVERIFIED_CURRENT"}
        tracker = (ROOT / "tracking/opportunity_tracker.csv").read_text()
        for line in tracker.splitlines()[1:]:
            if line.split(",", 1)[0] in ids:
                self.assertNotIn("not freshly checked", line, line[:40])

    def test_no_seed_marked_open_without_check(self):
        for path in FINDINGS:
            for o in json.loads(path.read_text())["opportunities"]:
                if o.get("source_status") in ("VERIFIED_OPEN", "ROLLING_CONFIRMED"):
                    self.assertTrue(o["source_checked_at"].startswith("2026-"), o["id"])


class PrivacyOfOutputsTests(unittest.TestCase):
    def test_no_personal_income_in_commit_eligible_files(self):
        files = commit_eligible_files()
        self.assertIn("context/discrepancies.md", files)
        for rel in files:
            path = ROOT / rel
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            low = text.lower()
            for marker in personal_markers():
                self.assertNotIn(marker.lower(), low, f"{marker!r} in {rel}")

    def test_private_dirs_not_commit_eligible(self):
        for rel in commit_eligible_files():
            self.assertFalse(rel.startswith(("private/", "badgr_legal/", "college_xscripts/", ".env", "data/")), rel)

if __name__ == "__main__":
    unittest.main()
