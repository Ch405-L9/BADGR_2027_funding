import csv
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from badgr_funding import db, planner
from tests.test_tracker import fresh_conn, opp, synthetic_applicant

ROOT = Path(__file__).resolve().parent.parent
MON = dt.date(2026, 10, 12)  # a Monday


def data(tasks):
    return {"tasks": tasks, "daily_blocks": [], "weekly": []}


def T(i, **kw):
    base = {"id": i, "title": i, "category": "records", "effort_min": 10, "evidence": "x", "escalate": "y"}
    base.update(kw)
    return base


class ScheduleTests(unittest.TestCase):
    def test_weekends_and_holidays_are_light(self):
        plan = planner.schedule(data([T("a"), T("b"), T("c"), T("d"), T("e"), T("f")]), MON, 7,
                                holidays={dt.date(2026, 10, 14): "owner holiday"})
        light = [d["date"].weekday() for d in plan if d["light"]]
        self.assertEqual(light, [2, 5, 6])  # Wed holiday, Sat, Sun
        self.assertTrue(all(d["focus"] is None for d in plan if d["light"]))

    def test_dependencies_and_due_order(self):
        tasks = [T("late", due="2026-12-01"), T("child", due="2026-10-13", depends_on=["parent"]),
                 T("parent", due="2026-10-30")]
        plan = planner.schedule(data(tasks), MON, 3)
        self.assertEqual([d["focus"]["id"] for d in plan], ["parent", "child", "late"])

    def test_not_before_respected(self):
        plan = planner.schedule(data([T("wait", not_before="2026-10-14")]), MON, 3)
        self.assertEqual([d["focus"]["id"] if d["focus"] else None for d in plan], [None, None, "wait"])

    def test_done_tasks_skipped_and_deps_satisfied(self):
        tasks = [T("a"), T("b", depends_on=["a"])]
        plan = planner.schedule(data(tasks), MON, 1, statuses={"a": {"status": "done"}})
        self.assertEqual(plan[0]["focus"]["id"], "b")

    def test_sam_only_tasks_appear_when_active(self):
        tasks = [T("sam", sam_active_only=True)]
        self.assertIsNone(planner.schedule(data(tasks), MON, 1)[0]["focus"])
        self.assertEqual(planner.schedule(data(tasks), MON, 1, sam_active=True)[0]["focus"]["id"], "sam")

    def test_start_date_configurable_and_deterministic(self):
        d = data([T("a"), T("b")])
        self.assertEqual(planner.schedule(d, MON, 5), planner.schedule(d, MON, 5))
        self.assertEqual(planner.schedule(d, MON + dt.timedelta(days=7), 1)[0]["date"], MON + dt.timedelta(days=7))

    def test_weekly_leftover(self):
        weeks, leftover = planner.weekly(data([T("a"), T("blocked", depends_on=["missing"])]), MON, 2)
        self.assertEqual([t["id"] for t in leftover], ["blocked"])

    def test_real_task_file_valid(self):
        d = planner.load_tasks(ROOT / "planning/tasks.json")
        ids = {t["id"] for t in d["tasks"]}
        self.assertEqual(len(ids), len(d["tasks"]))
        for t in d["tasks"]:
            for dep in t.get("depends_on", []):
                self.assertIn(dep, ids, t["id"])
            for k in ("title", "evidence", "escalate", "effort_min", "category"):
                self.assertIn(k, t, t["id"])
        plan = planner.schedule(d, dt.date(2026, 10, 8), 30)
        self.assertTrue(any(day["focus"] and day["focus"]["id"] == "dr_course2" for day in plan))
        c2 = next(day["date"] for day in plan if day["focus"] and day["focus"]["id"] == "dr_course2")
        self.assertLessEqual(c2, dt.date(2026, 12, 7))  # Verizon hard stop


class AgendaTests(unittest.TestCase):
    def setUp(self):
        self.conn = fresh_conn()
        self.tmp = tempfile.TemporaryDirectory()
        self.inputs = Path(self.tmp.name) / "fin.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def test_overdue_due_soon_and_stale(self):
        opp(self.conn, "g", program="Grant G", source_status="VERIFIED_OPEN",
            source_checked_at="2026-08-01T10:00:00-04:00", deadline_date="2026-10-20", followup_date="2026-10-15")
        opp(self.conn, "c", program="Closed C", source_status="VERIFIED_CLOSED", deadline_date="2026-10-16")
        d = data([T("old", due="2026-10-01"), T("soon", due="2026-10-20")])
        sec = planner.agenda(self.conn, d, MON, 14, statuses={}, holidays={}, appl=synthetic_applicant(),
                             private_inputs=self.inputs)
        self.assertTrue(any("old" in s for s in sec["Overdue"]))
        due = "\n".join(sec["Due in next 14 days"])
        self.assertIn("follow-up: Grant G", due)
        self.assertIn("deadline: Grant G", due)
        self.assertIn("date only", due)
        self.assertNotIn("Closed C", due)  # archived rows excluded
        self.assertTrue(any("Grant G" in s for s in sec["Stale sources (>30 days or never checked)"]))
        self.assertTrue(any("not created" in s for s in sec["Missing inputs"]))

    def test_dst_deadline_display(self):
        opp(self.conn, "d", program="DST", source_status="VERIFIED_OPEN", source_checked_at="2026-10-30T10:00:00-04:00",
            deadline_date="2026-11-02", deadline_time="17:00", deadline_tz="America/Los_Angeles")
        sec = planner.agenda(self.conn, data([]), dt.date(2026, 10, 31), 14, statuses={}, holidays={},
                             appl=synthetic_applicant(), private_inputs=self.inputs)
        self.assertTrue(any("20:00 EST" in s for s in sec["Due in next 14 days"]))

    def test_blank_private_inputs_listed_without_values(self):
        self.inputs.write_text("field,value,status,evidence\ncash_on_hand,,missing,\nexisting_debt_payments,12.00,est,\n")
        sec = planner.agenda(self.conn, data([]), MON, 14, statuses={}, holidays={}, appl=synthetic_applicant(),
                             private_inputs=self.inputs)
        text = "\n".join(sec["Missing inputs"])
        self.assertIn("cash_on_hand", text)
        self.assertNotIn("12.00", text)

    def test_sam_activation_trigger(self):
        sec = planner.agenda(self.conn, data([T("sam", sam_active_only=True)]), MON, 14, statuses={}, holidays={},
                             appl=synthetic_applicant(sam_active=True), private_inputs=self.inputs)
        self.assertIn("SAM Active", sec["SAM"][0])
        self.assertIn("sam", sec["Today"][0])

    def test_light_day_agenda(self):
        sec = planner.agenda(self.conn, data([T("a")]), dt.date(2026, 10, 17), 14, statuses={}, holidays={},
                             appl=synthetic_applicant(), private_inputs=self.inputs)
        self.assertIn("weekend", sec["Today"][0])


class StatusFileTests(unittest.TestCase):
    def test_set_status_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.csv"
            planner.set_status("a", "done", "proof", p, MON)
            planner.set_status("b", "skipped", "", p, MON)
            planner.set_status("a", "todo", "reopened", p, MON)
            rows = planner.load_status(p)
            self.assertEqual((rows["a"]["status"], rows["b"]["status"]), ("todo", "skipped"))


if __name__ == "__main__":
    unittest.main()
