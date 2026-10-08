import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from badgr_funding import backup, db, export, reports

ROOT = Path(__file__).resolve().parent.parent


class BackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "proj"
        (self.root / "private").mkdir(parents=True)
        (self.root / "private/secret.csv").write_text("x,1\n")
        (self.root / "planning").mkdir()
        (self.root / "planning/task_status.csv").write_text("id,status,date,evidence\n")
        conn = db.connect(self.root / "data/funding.sqlite")
        db.migrate(conn)
        db.insert(conn, "a", {"sponsor": "S", "program": "P", "funding_type": "grant"})
        conn.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip_verifies_hashes_and_integrity(self):
        archive, manifest = backup.create(self.root, stamp="T1")
        self.assertIn("private/secret.csv", manifest["files"])
        report = backup.restore_test(archive, Path(self.tmp.name) / "restore")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["db_integrity"], "ok")
        self.assertEqual(report["db_rows"]["opportunities"], 1)

    def test_tampered_backup_detected(self):
        archive, _ = backup.create(self.root, stamp="T2")
        tampered = Path(self.tmp.name) / "tampered.zip"
        with zipfile.ZipFile(archive) as src, zipfile.ZipFile(tampered, "w") as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                dst.writestr(item, b"changed\n" if item.filename == "private/secret.csv" else data)
        report = backup.restore_test(tampered, Path(self.tmp.name) / "r2")
        self.assertFalse(report["ok"])
        self.assertEqual(report["hash_mismatches"], ["private/secret.csv"])

    def test_unsafe_archive_rejected(self):
        bad = Path(self.tmp.name) / "bad.zip"
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../escape.txt", "x")
            z.writestr("MANIFEST.json", json.dumps({"files": {}}))
        with self.assertRaises(ValueError):
            backup.restore_test(bad, Path(self.tmp.name) / "r3")

    def test_backups_gitignored(self):
        self.assertIn("backups/private/", (ROOT / ".gitignore").read_text())


class ExportTests(unittest.TestCase):
    def test_sanitize_strips_tags_internal_sections_and_paths(self):
        text = ("# DRAFT x\nStatus: DRAFT. Claim IDs refer to context/claims_ledger.csv.\n## Body\n"
                "Fact here [C-BIZ-01] [A-FIN-05] (D6) see drafts/use_of_funds_scenarios.md\n"
                "## Missing inputs\n- secret thing\n## Review notes\n- internal\n")
        out = export.sanitize_markdown(text)
        for bad in ("[C-", "[A-", "(D6)", "Missing inputs", "Review notes", "secret thing", "context/", "drafts/"):
            self.assertNotIn(bad, out)
        self.assertIn("the use of funds scenarios document", out)

    def test_build_refuses_leaky_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "drafts").mkdir()
            for name in export.DRAFTS:
                (root / "drafts" / name).write_text("# DRAFT\nok\n")
            (root / "drafts" / export.DRAFTS[0]).write_text("# DRAFT\nUnemployment detail\n")
            with self.assertRaises(ValueError):
                export.build(root, stamp="t")
            self.assertFalse((root / "exports/public/badgr_packet_t").exists())

    def test_real_packet_builds_clean_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sub in ("drafts", "finance"):
                (root / sub).mkdir()
            for name in export.DRAFTS:
                (root / "drafts" / name).write_text((ROOT / "drafts" / name).read_text())
            (root / "finance/loan_offer_comparison.csv").write_text((ROOT / "finance/loan_offer_comparison.csv").read_text())
            pkt, archive, files = export.build(root, stamp="t")
            self.assertEqual(export.completeness(pkt), [])
            self.assertTrue(archive.exists())
            for p in pkt.iterdir():
                self.assertEqual(export.problems(p.read_text()), [], p.name)


class ReportTests(unittest.TestCase):
    def test_reports_generate(self):
        reg = reports.source_register(ROOT)
        self.assertIn("kiva", reg)
        miss = reports.missing_inputs(ROOT)
        self.assertIn("Open discrepancies", miss)
        self.assertNotIn("D18:", miss)  # resolved items excluded


if __name__ == "__main__":
    unittest.main()
