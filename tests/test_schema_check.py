import copy
import json
import unittest
from pathlib import Path

from badgr_funding.schema_check import validate

ROOT = Path(__file__).resolve().parent.parent
PROFILE = json.loads((ROOT / "context/business_profile.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "context/business_profile.schema.json").read_text(encoding="utf-8"))


class ProfileSchemaTests(unittest.TestCase):
    def test_profile_is_valid(self):
        self.assertEqual(validate(PROFILE, SCHEMA), [])

    def test_unknown_financials_must_stay_null_not_missing(self):
        bad = copy.deepcopy(PROFILE)
        del bad["financials"]["cash_balance"]
        self.assertTrue(any("cash_balance" in e for e in validate(bad, SCHEMA)))

    def test_financial_null_allowed_but_string_rejected(self):
        bad = copy.deepcopy(PROFILE)
        bad["financials"]["2025_revenue_verified"] = "unknown"
        self.assertTrue(validate(bad, SCHEMA))

    def test_uei_pattern_enforced(self):
        bad = copy.deepcopy(PROFILE)
        bad["registration"]["uei"] = "U9GUGKVFGCA"  # 11 chars
        self.assertTrue(any("uei" in e for e in validate(bad, SCHEMA)))

    def test_boolean_is_not_integer(self):
        bad = copy.deepcopy(PROFILE)
        bad["business"]["employees_reported_in_sam"] = True
        self.assertTrue(validate(bad, SCHEMA))

    def test_ownership_percentage_null_is_valid(self):
        unknown = copy.deepcopy(PROFILE)
        unknown["owner"]["ownership_percentage"] = None
        self.assertEqual(validate(unknown, SCHEMA), [])

    def test_ownership_percentage_requires_evidence_and_range(self):
        pct = PROFILE["owner"]["ownership_percentage"]
        if pct is not None:
            self.assertTrue(0 <= pct <= 100)
            self.assertTrue(PROFILE["owner"].get("ownership_evidence", "").strip())

    def test_signing_name_not_silently_normalized(self):
        owner = PROFILE["owner"]
        self.assertIn("government-issued ID", owner["signing_name_owner_directive"])
        self.assertEqual(owner["legal_name_in_ga_filings_and_operating_agreement"], "Brandon Grant")

    def test_every_project_has_evidence(self):
        for project in PROFILE["projects"]:
            self.assertIn("evidence", project)

    def test_location_rejects_street_address_field(self):
        bad = copy.deepcopy(PROFILE)
        bad["business"]["operating_location"]["street"] = "redacted"
        self.assertTrue(any("street" in e for e in validate(bad, SCHEMA)))


if __name__ == "__main__":
    unittest.main()
