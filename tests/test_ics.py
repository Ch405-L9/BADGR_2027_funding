import datetime as dt
import unittest
from pathlib import Path

from badgr_funding import ics, planner

ROOT = Path(__file__).resolve().parent.parent
NOW = dt.datetime(2026, 10, 8, 14, 0, tzinfo=dt.timezone.utc)


class IcsTests(unittest.TestCase):
    def setUp(self):
        self.data = planner.load_tasks(ROOT / "planning/tasks.json")
        self.text = ics.build(self.data, dt.date(2026, 10, 8), {}, {}, False, NOW)
        self.lines = self.text.split("\r\n")

    def test_structure_and_crlf(self):
        self.assertTrue(self.text.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertTrue(self.text.endswith("END:VCALENDAR\r\n"))
        self.assertNotIn("\n", self.text.replace("\r\n", ""))
        self.assertEqual(self.text.count("BEGIN:VEVENT"), self.text.count("END:VEVENT"))
        self.assertIn("BEGIN:VTIMEZONE", self.text)

    def test_lines_folded_to_75_octets(self):
        for line in self.lines:
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)

    def test_uids_unique(self):
        unfolded = self.text.replace("\r\n ", "")
        uids = [l for l in unfolded.split("\r\n") if l.startswith("UID:")]
        self.assertEqual(len(uids), len(set(uids)))

    def test_deadlines_all_day_and_details(self):
        unfolded = self.text.replace("\r\n ", "")
        self.assertIn("DTSTART;VALUE=DATE:20261207", unfolded)          # Verizon hard stop
        self.assertIn("DTEND;VALUE=DATE:20261208", unfolded)
        self.assertIn("2530 Sever Road\\, Suite 202\\, Lawrenceville\\, GA 30043", unfolded)  # escaped commas
        self.assertIn("URL:https://georgiasbdc.org/intake-form/", unfolded)
        self.assertIn("800-906-9887", unfolded)

    def test_no_timed_blocks_by_default(self):
        self.assertNotIn("RRULE:FREQ=WEEKLY", self.text)

    def test_one_off_events_timed_with_alarm(self):
        unfolded = self.text.replace("\r\n ", "")
        self.assertIn("DTSTART;TZID=America/New_York:20261030T100000", unfolded)
        self.assertIn("DTEND;TZID=America/New_York:20261030T113000", unfolded)
        self.assertIn("TRIGGER:-PT30M", unfolded)
        self.assertIn("DTSTART;TZID=America/New_York:20261015T090000", unfolded)  # APEX intro class
        self.assertIn("DTEND;TZID=America/New_York:20261015T120000", unfolded)
        self.assertEqual(unfolded.count("BEGIN:VALARM"), unfolded.count("END:VALARM"))

    def test_milestone_skipped_when_task_done(self):
        text = ics.build(self.data, dt.date(2026, 10, 8), {"dr_course2": {"status": "done"}}, {}, False, NOW)
        self.assertNotIn("milestone-2026-12-07@", text.replace("\r\n ", ""))
        self.assertIn("milestone-2026-12-07@", self.text.replace("\r\n ", ""))

    def test_weekly_blocks_timezone_and_rrule(self):
        weekly = [("MO", "09:00", 30, "Review", "desc"), ("TH", "13:00", 60, "Funding block", "desc")]
        text = ics.build(self.data, dt.date(2026, 10, 8), {}, {}, False, NOW, weekly)
        unfolded = text.replace("\r\n ", "")
        self.assertIn("DTSTART;TZID=America/New_York:20261012T090000", unfolded)  # first Monday after start
        self.assertIn("DTSTART;TZID=America/New_York:20261008T130000", unfolded)  # start day itself is a Thursday
        self.assertIn("DTEND;TZID=America/New_York:20261008T140000", unfolded)
        self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=TH;UNTIL=20270120T235959Z", unfolded)

    def test_milestones_do_not_claim_eligibility(self):
        self.assertNotIn("eligible to apply", self.text.replace("\r\n ", "").lower())

    def test_done_tasks_excluded(self):
        text = ics.build(self.data, dt.date(2026, 10, 8), {"sbdc_request": {"status": "done"}}, {}, False, NOW)
        self.assertNotIn("due-sbdc_request@", text.replace("\r\n ", ""))

    def test_escape_and_fold_units(self):
        self.assertEqual(ics.escape("a,b;c\\d\ne"), "a\\,b\;c\\\\d\\ne")
        folded = ics.fold("X" * 200)
        self.assertTrue(all(len(f) <= 75 for f in folded))
        self.assertEqual("".join(f.lstrip(" ") if i else f for i, f in enumerate(folded)), "X" * 200)


if __name__ == "__main__":
    unittest.main()
