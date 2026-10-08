import csv
import datetime as dt
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from badgr_funding import applicant, csv_safe, csvio, db, dates, dedupe, money, scoring, status

ROOT = Path(__file__).resolve().parent.parent
REF = dt.date(2026, 10, 8)


def synthetic_applicant(**over):
    base = dict(state="GA", county="Gwinnett", city="Lawrenceville", naics=["541511"], entity_type="LLC",
                formation_date=dt.date(2025, 1, 20), sam_active=False, uei="TESTUEI00001",
                receipts_2025_cents=555000, net_2025_cents=-1708400, ownership_pct=100,
                ownership_verified=False, self_cert_sdb=True, minority_owned_reported=True)
    base.update(over)
    return applicant.Applicant(**base)


def fresh_conn():
    conn = db.connect(":memory:")
    db.migrate(conn)
    return conn


def opp(conn, oid="x", **fields):
    base = dict(sponsor="Sponsor", program="Program", funding_type="grant")
    base.update(fields)
    db.insert(conn, oid, base)
    return db.get(conn, oid)


class MigrationTests(unittest.TestCase):
    def test_migrate_idempotent(self):
        conn = db.connect(":memory:")
        self.assertEqual(db.migrate(conn), ["0001_init.sql", "0002_private_criteria.sql"])
        self.assertEqual(db.migrate(conn), [])

    def test_override_requires_reason_at_db_level(self):
        conn = fresh_conn()
        with self.assertRaises(sqlite3.IntegrityError):
            opp(conn, override_score=90)

    def test_invalid_enum_rejected(self):
        conn = fresh_conn()
        with self.assertRaises(sqlite3.IntegrityError):
            opp(conn, eligibility="maybe")

    def test_amount_range_ordered(self):
        conn = fresh_conn()
        with self.assertRaises(sqlite3.IntegrityError):
            opp(conn, amount_min_cents=500, amount_max_cents=100)


class HistoryAndDedupeTests(unittest.TestCase):
    def test_update_writes_history_and_requires_reason(self):
        conn = fresh_conn()
        opp(conn, uses_allowed="equipment")
        with self.assertRaises(ValueError):
            db.update(conn, "x", {"uses_allowed": "x"}, "")
        db.update(conn, "x", {"uses_allowed": "equipment, workspace"}, "sponsor rule changed")
        h = [r for r in db.history(conn, "x") if r["field"] == "uses_allowed"]
        self.assertEqual((h[0]["old_value"], h[0]["new_value"]), ("equipment", "equipment, workspace"))

    def test_changed_rule_never_deletes(self):
        conn = fresh_conn()
        opp(conn)
        db.update(conn, "x", {"source_status": "DISCONTINUED"}, "program ended")
        self.assertIsNotNone(db.get(conn, "x"))

    def test_duplicate_cycle_merges_and_keeps_sources(self):
        conn = fresh_conn()
        r1 = dedupe.upsert(conn, "a", dict(sponsor="SBA", program="Microloan", funding_type="loan", cycle="2026"), "r")
        db.add_source(conn, "a", "https://sba.gov/1", "official", "test", checked_at="2026-10-01")
        r2 = dedupe.upsert(conn, "b", dict(sponsor="sba ", program="MICROLOAN", funding_type="loan", cycle="2026", fees="none"), "r")
        db.add_source(conn, r2[1], "https://sba.gov/2", "official", "test", checked_at="2026-10-02")
        self.assertEqual(r1, ("inserted", "a"))
        self.assertEqual(r2, ("updated", "a"))
        self.assertEqual(len(db.sources(conn, "a")), 2)
        self.assertIsNone(db.get(conn, "b"))

    def test_different_cycles_are_separate(self):
        conn = fresh_conn()
        dedupe.upsert(conn, "a", dict(sponsor="S", program="P", funding_type="grant", cycle="2026"), "r")
        self.assertEqual(dedupe.upsert(conn, "b", dict(sponsor="S", program="P", funding_type="grant", cycle="2027"), "r"),
                         ("inserted", "b"))

    def test_null_vs_set_cycle_is_flagged_not_merged(self):
        conn = fresh_conn()
        dedupe.upsert(conn, "a", dict(sponsor="S", program="P", funding_type="grant", cycle=None), "r")
        out = dedupe.upsert(conn, "b", dict(sponsor="S", program="P", funding_type="grant", cycle="2026"), "r")
        self.assertEqual(out, ("flagged", "b"))
        self.assertEqual(conn.execute("SELECT flag FROM review_flags").fetchone()[0], "cycle_conflict")


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.conn = fresh_conn()
        self.appl = synthetic_applicant()

    def ready_opp(self, **over):
        base = dict(source_status="VERIFIED_OPEN", source_checked_at="2026-10-05T10:00:00-04:00",
                    prerequisite_tier="NONE", deadline_date="2026-11-30", rolling="no")
        base.update(over)
        return opp(self.conn, **base)

    def test_all_yes_and_fresh_is_ready(self):
        o = self.ready_opp()
        db.set_criterion(self.conn, "x", "Georgia business", "yes")
        self.assertEqual(status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF), [])

    def test_unknown_material_criterion_blocks(self):
        o = self.ready_opp()
        db.set_criterion(self.conn, "x", "Georgia business", "yes")
        db.set_criterion(self.conn, "x", "revenue under cap", "unknown")
        blk = status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF)
        self.assertTrue(any("eligibility unknown" in b for b in blk))

    def test_no_criteria_blocks(self):
        o = self.ready_opp()
        self.assertTrue(any("no criteria" in b for b in status.blockers(o, [], self.appl, REF)))

    def test_ineligible_rollup(self):
        rows = [dict(criterion="a", status="yes", material=1), dict(criterion="b", status="no", material=1)]
        self.assertEqual(status.rolled_eligibility(rows), "no")

    def test_nonmaterial_unknown_does_not_block(self):
        rows = [dict(criterion="a", status="yes", material=1), dict(criterion="b", status="unknown", material=0)]
        self.assertEqual(status.rolled_eligibility(rows), "yes")

    def test_unverified_seed_never_ready(self):
        o = opp(self.conn)
        blk = status.blockers(o, [], self.appl, REF)
        self.assertTrue(any("UNVERIFIED_CURRENT" in b for b in blk))

    def test_stale_source_blocks(self):
        o = self.ready_opp(source_checked_at="2026-08-01T10:00:00-04:00")
        db.set_criterion(self.conn, "x", "a", "yes")
        self.assertTrue(any("not checked within" in b for b in status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF)))

    def test_missing_deadline_is_not_rolling(self):
        o = self.ready_opp(deadline_date=None, rolling="unknown")
        db.set_criterion(self.conn, "x", "a", "yes")
        self.assertTrue(any("deadline unknown" in b for b in status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF)))

    def test_passed_deadline_blocks(self):
        o = self.ready_opp(deadline_date="2026-10-01")
        db.set_criterion(self.conn, "x", "a", "yes")
        self.assertIn("deadline passed", status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF))

    def test_sam_tier_blocks_until_active(self):
        o = self.ready_opp(prerequisite_tier="SAM_ACTIVE")
        db.set_criterion(self.conn, "x", "a", "yes")
        crit = db.criteria(self.conn, "x")
        self.assertIn("SAM registration not Active", status.blockers(o, crit, self.appl, REF))
        self.assertNotIn("SAM registration not Active", status.blockers(o, crit, synthetic_applicant(sam_active=True), REF))

    def test_history_gate(self):
        o = self.ready_opp(prerequisite_tier="HISTORY_MIN", min_months_in_business=24)
        db.set_criterion(self.conn, "x", "a", "yes")
        crit = db.criteria(self.conn, "x")
        self.assertTrue(any("until 2027-01-20" in b for b in status.blockers(o, crit, self.appl, REF)))
        self.assertFalse(any("history" in b for b in status.blockers(o, crit, self.appl, dt.date(2027, 1, 20))))

    def test_loan_needs_repayment_analysis(self):
        o = self.ready_opp(funding_type="loan", rolling="yes", deadline_date=None)
        db.set_criterion(self.conn, "x", "a", "yes")
        self.assertIn("repayment analysis not done", status.blockers(o, db.criteria(self.conn, "x"), self.appl, REF))


class PrivateScreeningAndArchiveTests(unittest.TestCase):
    def setUp(self):
        self.conn = fresh_conn()
        opp(self.conn)
        db.set_criterion(self.conn, "x", "No bankruptcy", "yes", private_key="bankruptcy", pass_when="false")
        db.set_criterion(self.conn, "x", "PayPal", "unknown", private_key="paypal", pass_when="true")

    def test_private_criteria_stored_unknown(self):
        for c in db.criteria(self.conn, "x"):
            self.assertEqual((c["status"], c["evidence"]), ("unknown", "owner-screened (private)"))

    def test_resolve_private(self):
        crit = db.criteria(self.conn, "x")
        got = {c["criterion"]: c["status"] for c in status.resolve_private(crit, {"bankruptcy": False, "paypal": True})}
        self.assertEqual(got, {"No bankruptcy": "yes", "PayPal": "yes"})
        got = {c["criterion"]: c["status"] for c in status.resolve_private(crit, {"bankruptcy": True, "paypal": None})}
        self.assertEqual(got, {"No bankruptcy": "no", "PayPal": "unknown"})
        self.assertEqual(status.resolve_private(crit, {}), [dict(c) for c in crit])

    def test_archive_reason(self):
        self.assertIsNone(status.archive_reason(db.get(self.conn, "x"), []))
        closed = opp(self.conn, "c", program="C", source_status="VERIFIED_CLOSED")
        self.assertEqual(status.archive_reason(closed, []), "source VERIFIED_CLOSED")
        parked = opp(self.conn, "p", program="P2", next_action="Parked: owner declined")
        self.assertEqual(status.archive_reason(parked, []), "parked by owner")

    def test_export_never_resolves_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.csv"
            csvio.export_tracker(self.conn, path, synthetic_applicant(), REF)
            self.assertNotIn("eligibility no", path.read_text())


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.conn = fresh_conn()
        self.appl = synthetic_applicant()

    def test_reproducible_and_bounded(self):
        o = opp(self.conn, amount_max_cents=1_000_000, prerequisite_tier="NONE", effort_hours=4)
        db.set_criterion(self.conn, "x", "a", "yes")
        crit = db.criteria(self.conn, "x")
        s1, s2 = scoring.score(o, crit, self.appl, REF), scoring.score(o, crit, self.appl, REF)
        self.assertEqual(s1, s2)
        self.assertEqual(s1["total"], 15 + 25 + 25 + 12 + 10)
        self.assertLessEqual(s1["total"], 100)

    def test_unknowns_earn_nothing(self):
        o = opp(self.conn)
        s = scoring.score(o, [], self.appl, REF)
        self.assertEqual(s["parts"]["value"][0], 0)
        self.assertEqual(s["parts"]["fit"][0], 0)
        self.assertEqual(s["parts"]["readiness"][0], 0)
        self.assertEqual(s["parts"]["effort"][0], 0)

    def test_debt_scores_lower_on_cost_risk(self):
        loan = opp(self.conn, "l", funding_type="loan", collateral="equipment lien", guarantee="personal", fees="1%")
        grant = opp(self.conn, "g", program="G")
        self.assertLess(scoring.cost_risk_score(loan)[0], scoring.cost_risk_score(grant)[0])

    def test_ineligible_not_ranked(self):
        o = opp(self.conn)
        s = scoring.score(o, [dict(criterion="a", status="no", material=1)], self.appl, REF)
        self.assertFalse(s["ranked"])

    def test_override_shown_with_reason(self):
        o = opp(self.conn, override_score=99, override_reason="owner priority: SBDC first")
        s = scoring.score(o, [], self.appl, REF)
        self.assertEqual((s["total"], s["override"]), (99, True))
        self.assertEqual(s["computed"], 10)  # only cost_risk (no-fee grant) scores

    def test_history_readiness_changes_with_date(self):
        o = opp(self.conn, prerequisite_tier="HISTORY_MIN", min_months_in_business=24)
        self.assertEqual(scoring.readiness_score(o, self.appl, REF)[0], 5)
        self.assertEqual(scoring.readiness_score(o, self.appl, dt.date(2027, 2, 1))[0], 20)


class DateTests(unittest.TestCase):
    def test_months_in_business(self):
        self.assertEqual(dates.months_between(dt.date(2025, 1, 20), REF), 20)
        self.assertEqual(dates.history_gate_date(dt.date(2025, 1, 20), 24), dt.date(2027, 1, 20))

    def test_add_months_end_of_month(self):
        self.assertEqual(dates.add_months(dt.date(2025, 1, 31), 1), dt.date(2025, 2, 28))

    def test_date_only_deadline_stays_date_only(self):
        self.assertIn("date only", dates.deadline_display("2026-11-30"))

    def test_unknown_deadline_not_rolling(self):
        self.assertEqual(dates.deadline_display(None), "Unknown deadline")
        self.assertEqual(dates.deadline_display(None, rolling="yes"), "Rolling (confirmed)")

    def test_dst_conversion(self):
        # 17:00 Pacific on 2026-11-01 (after DST ends) is 20:00 Eastern standard time
        self.assertEqual(dates.deadline_local("2026-11-01", "17:00", "America/Los_Angeles").strftime("%H:%M %Z"), "20:00 EST")
        # 17:00 Pacific on 2026-03-08 (US DST starts that day) is 20:00 EDT
        self.assertEqual(dates.deadline_local("2026-03-08", "17:00", "America/Los_Angeles").strftime("%H:%M %Z"), "20:00 EDT")

    def test_stale(self):
        self.assertTrue(dates.is_stale(None, 30, REF))
        self.assertFalse(dates.is_stale("2026-10-01T00:00:00-04:00", 30, REF))
        self.assertTrue(dates.is_stale("2026-09-01", 30, REF))


class MoneyAndCsvTests(unittest.TestCase):
    def test_money_parsing(self):
        self.assertEqual(money.to_cents("$5,550.00"), 555000)
        self.assertEqual(money.to_cents(-17084), -1708400)
        self.assertEqual(money.to_cents("(1,000.50)"), -100050)
        self.assertIsNone(money.to_cents(""))
        self.assertIsNone(money.to_cents(None))
        self.assertEqual(money.fmt(None), "unknown")
        self.assertEqual(money.fmt(-1708400), "-$17,084.00")
        with self.assertRaises(ValueError):
            money.to_cents("abc")

    def test_formula_injection_escaped_and_reversible(self):
        for bad in ("=HYPERLINK(\"x\")", "+1", "-cmd", "@SUM(A1)", "\tx", "'=already"):
            esc = csv_safe.escape(bad)
            self.assertTrue(esc.startswith("'"), bad)
            self.assertEqual(csv_safe.unescape(esc), bad)
        self.assertEqual(csv_safe.escape("normal text"), "normal text")
        self.assertEqual(csv_safe.unescape("'quoted but safe"), "'quoted but safe")

    def test_csv_roundtrip_preserves_values(self):
        conn = fresh_conn()
        opp(conn, "r1", program="=evil()", amount_min_cents=-500, amount_max_cents=100,
            notes="line, with comma \"quotes\"", effort_hours=3)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.csv"
            csvio.export_tracker(conn, path, synthetic_applicant(), REF)
            with open(path, newline="") as fh:
                row = next(csv.DictReader(fh))
            self.assertEqual(row["program"], "'=evil()")
            self.assertEqual(row["amount_min_cents"], "-500")
            conn2 = fresh_conn()
            csvio.import_tracker(conn2, path)
            a, b = db.get(conn, "r1"), db.get(conn2, "r1")
            for col in db.EDITABLE:
                self.assertEqual(a[col], b[col], col)

    def test_seed_import_all_unverified(self):
        conn = fresh_conn()
        results = csvio.import_seed(conn, ROOT / "research/seed_opportunities.csv")
        self.assertEqual(len(results), 12)
        for o in db.all_opportunities(conn):
            self.assertEqual(o["source_status"], "UNVERIFIED_CURRENT")
            self.assertEqual(o["eligibility"], "unknown")

    def test_seed_reimport_is_idempotent(self):
        conn = fresh_conn()
        csvio.import_seed(conn, ROOT / "research/seed_opportunities.csv")
        again = csvio.import_seed(conn, ROOT / "research/seed_opportunities.csv")
        self.assertTrue(all(o == "unchanged" for o, _ in again))

    def test_findings_loader(self):
        conn = fresh_conn()
        data = {"opportunities": [{
            "id": "f1", "sponsor": "S", "program": "P", "funding_type": "grant", "amount_max": "$10,000",
            "criteria": [{"criterion": "GA", "status": "yes", "evidence": "page"},
                         {"criterion": "revenue cap", "status": "unknown"}],
            "sources": [{"url": "https://example.org", "kind": "official", "method": "WebFetch summary",
                         "checked_at": "2026-10-08T06:00:00-04:00"}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "f.json"
            p.write_text(json.dumps(data))
            csvio.load_findings(conn, p)
        o = db.get(conn, "f1")
        self.assertEqual(o["amount_max_cents"], 1_000_000)
        self.assertEqual(o["eligibility"], "unknown")
        self.assertEqual(len(db.sources(conn, "f1")), 1)


class ApplicantTests(unittest.TestCase):
    def test_profile_load(self):
        a = applicant.load(ROOT / "context/business_profile.json")
        self.assertEqual((a.state, a.county), ("GA", "Gwinnett"))
        self.assertFalse(a.sam_active)
        self.assertEqual(a.receipts_2025_cents, 555000)
        self.assertIsNone(a.gender)
        self.assertIsNone(a.veteran)
        self.assertEqual(a.third_party_certs, [])


if __name__ == "__main__":
    unittest.main()
