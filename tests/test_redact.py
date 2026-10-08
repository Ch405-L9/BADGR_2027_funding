import tempfile
import unittest
from pathlib import Path
from unittest import mock

from badgr_funding import redact

# Synthetic values only; none belong to the business or owner.
SYNTHETIC = """\
ein: 12-3456789
ssn 123-45-6789
routing 021000021
card 4111 1111 1111 1111
password = hunter2
-----BEGIN RSA PRIVATE KEY-----
token ghp_abcdefghijklmnopqrstuvwxyz0123
contact someone@example.com
phone (555) 555-0100
"""


class RedactScanTests(unittest.TestCase):
    def test_detects_each_synthetic_pattern(self):
        kinds = {kind for _, kind, _ in redact.scan_text(SYNTHETIC)}
        for expected in ("ein_like", "ssn_like", "routing_or_account_like", "card_like",
                         "credential_assignment", "private_key", "github_token", "email", "us_phone"):
            self.assertIn(expected, kinds)

    def test_ignores_dates_uei_and_naics(self):
        clean = "Formed 2025-01-20. UEI U9GUGKVFGCA9. NAICS 541511. Latency 84/125 ms. $815."
        self.assertEqual(list(redact.scan_text(clean)), [])

    def test_env_and_secret_files_are_never_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env_sam-gov.json").write_text("password = x")
            (root / "secret_original.json").write_text("password = x")
            (root / "ok.md").write_text("clean")
            opened = []
            real_read = Path.read_text

            def spy(self, *a, **k):
                opened.append(self.name)
                return real_read(self, *a, **k)

            with mock.patch.object(Path, "read_text", spy):
                findings = redact.scan_tree(root)
            self.assertEqual(findings, [])
            self.assertEqual(opened, ["ok.md"])

    def test_findings_are_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "leak.md").write_text("ein: 12-3456789")
            findings = redact.scan_tree(root)
            self.assertEqual(len(findings), 1)
            self.assertNotIn("3456789", findings[0][3])

    def test_cents_columns_skipped_but_other_csv_cells_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "t.csv").write_text("id,amount_max_cents,notes\nx,200000000,ok\ny,500000000,acct 021000021\n")
            kinds = [(f[1], f[2]) for f in redact.scan_tree(root)]
            self.assertEqual(kinds, [(3, "routing_or_account_like")])

    def test_project_tree_is_clean(self):
        root = Path(__file__).resolve().parent.parent
        findings = redact.scan_tree(root, exclude=("badgr_funding/redact.py", "tests/test_redact.py"))
        self.assertEqual(findings, [], findings)


if __name__ == "__main__":
    unittest.main()
