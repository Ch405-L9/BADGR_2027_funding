"""iCalendar (RFC 5545) export of the funding plan: due dates, focus days, milestones, weekly blocks.

Deadlines are all-day (date-only stays date-only). Weekly blocks are timed in
America/New_York with a VTIMEZONE so calendar apps handle DST correctly.
Contact details are public office information from official pages (checked 2026-10-08).
"""
import datetime as dt
from pathlib import Path

from badgr_funding import dates, planner

SBDC = {"url": "https://georgiasbdc.org/intake-form/",
        "location": "UGA SBDC Gwinnett Office, 2530 Sever Road, Suite 202, Lawrenceville, GA 30043",
        "info": "Request form: https://georgiasbdc.org/intake-form/ | Office: https://georgiasbdc.org/locations/gwinnett/ | (678) 985-6820 | gwinnett@georgiasbdc.org | By appointment only; consulting is free."}
APEX = {"url": "https://gtapexaccelerator.org/getting-started/",
        "location": "Georgia Tech APEX Accelerator (virtual or in-person classes)",
        "info": "Getting started: https://gtapexaccelerator.org/getting-started/ | Class calendar: https://gtapexaccelerator.ecenterdirect.com/events/ | +1 404.894.2000 | Steps: intro class, New Client Application, counselor appointment."}
VERIZON = {"url": "https://digitalready.verizonwireless.com/",
           "location": "Online",
           "info": "Courses: https://digitalready.verizonwireless.com/ | Grant rules: https://digitalready.verizonwireless.com/funding/details | Administrator: https://www.lisc.org/our-initiatives/small-business/our-work/verizon-small-business-digital-ready/grant-program/ | Two courses/events by 2026-12-07 unlock the $10,000 application."}
GEC = {"url": "https://gec1.wildapricot.org/tours",
       "location": "Gwinnett Entrepreneur Center, 75 Langley Drive, Lawrenceville, GA 30046",
       "info": "Tours: https://gec1.wildapricot.org/tours | County page: https://www.gwinnettcounty.com/government/departments/planning-development/economic-development/entrepreneur-center | 770.822.8000 | Free; ask about the incubator cohort and desk access."}
ATDC = {"url": "https://atdc.org/", "location": "Online",
        "info": "https://atdc.org/ (quiz: 'Which ATDC Program is Right For Me?') | info@atdc.org | (404) 894-3575 | State-funded, zero equity."}
VITA = {"url": "https://irs.treasury.gov/freetaxprep/", "location": "VITA site near ZIP 30044 (from locator)",
        "info": "VITA locator: https://irs.treasury.gov/freetaxprep/ | 800-906-9887 | Eligibility: https://www.irs.gov/individuals/free-tax-return-preparation-for-qualifying-taxpayers | Bring private/tax_2025_summary.md, IRS transcripts and your tax forms. Off-season: ask SBDC for a referral."}
KIVA = {"url": "https://www.kiva.org/borrow", "location": "Online", "info": "https://www.kiva.org/borrow | 0% loans $1,000-$15,000; apply only after the repayment check."}
NSF = {"url": "https://seedfund.nsf.gov/project-pitch/", "location": "Online",
       "info": "https://seedfund.nsf.gov/project-pitch/ | Draft: drafts/nsf_project_pitch.md | One pitch at a time."}
ACE = {"url": "https://aceloans.org/apply-for-a-loan/small-business-loans/", "location": "Online",
       "info": "ACE: https://aceloans.org/apply-for-a-loan/small-business-loans/ | SBA 8(a): https://www.sba.gov/federal-contracting/contracting-assistance-programs/8a-business-development-program | Both need 2 years in business (2027-01-20)."}
SAM = {"url": "https://sam.gov/", "location": "Online", "info": "https://sam.gov/ | https://www.grants.gov/ | Record CAGE and expiration when Active."}

TASK_INFO = {
    "sbdc_request": SBDC, "tax_review": VITA, "tax_packet": VITA, "apex_class": APEX,
    "dr_account": VERIZON, "dr_course1": VERIZON, "dr_course2": VERIZON, "dr_apply": VERIZON,
    "ec_tour": GEC, "atdc_quiz": ATDC, "kiva_decide": KIVA, "kiva_story": KIVA,
    "nsf_pitch": NSF, "prior_art": NSF, "discovery": NSF, "ace_8a_revisit": ACE,
    "sam_record": SAM, "sam_grantsgov": SAM, "sam_rank": SAM,
}
MILESTONES = [
    ("2026-12-07", "HARD STOP: Verizon Digital Ready courses must be complete", VERIZON),
    ("2027-01-12", "Verizon Digital Ready final decisions due", VERIZON),
    ("2027-01-20", "BADGR reaches 2 years in business (ACE loan, SBA 8(a) eligible to apply)", ACE),
]
WEEKLY = [  # (weekday code, start HH:MM, minutes, summary, description)
    ("MO", "09:00", 30, "BADGR weekly review", "Run `python3 -m badgr_funding.cli agenda --days 14`; re-check sources older than 30 days; update the shortlist. Move this time as needed."),
    ("WE", "09:00", 30, "SAM.gov status check + one opportunity search", "https://sam.gov/ | Manual search from docs/SEARCH_PLAYBOOK.md. Move this time as needed."),
    ("FR", "15:00", 60, "Records hour", "Statements, order histories, invoices; update private/expense_records.csv and private/income_records.csv. Move this time as needed."),
]
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""


def escape(text):
    return (text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n"))


def fold(line):
    """Fold to 75 octets per RFC 5545 (continuation lines start with a space)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not out else 74
        if len(cur) + len(b) > limit:
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    out.append(cur.decode("utf-8"))
    return [out[0]] + [" " + s for s in out[1:]]


def _allday(uid, day, summary, info=None, extra="", stamp=""):
    nxt = day + dt.timedelta(days=1)
    desc = "\n".join(x for x in (extra, info["info"] if info else "") if x)
    ev = ["BEGIN:VEVENT", f"UID:{uid}@badgr-funding.local", f"DTSTAMP:{stamp}",
          f"DTSTART;VALUE=DATE:{day:%Y%m%d}", f"DTEND;VALUE=DATE:{nxt:%Y%m%d}",
          f"SUMMARY:{escape(summary)}", "TRANSP:TRANSPARENT"]
    if desc:
        ev.append(f"DESCRIPTION:{escape(desc)}")
    if info:
        ev += [f"URL:{info['url']}", f"LOCATION:{escape(info['location'])}"]
    ev.append("END:VEVENT")
    return ev


def build(data, start, statuses=None, holidays=None, sam_active=False, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    statuses = statuses or {}
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BADGR Technologies//Funding Plan//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:BADGR Funding Plan", "X-WR-TIMEZONE:America/New_York",
             *VTIMEZONE.splitlines()]
    open_ids = {t["id"] for t in planner.open_tasks(data["tasks"], statuses, sam_active)}
    for t in data["tasks"]:
        if t["id"] in open_ids and t.get("due"):
            lines += _allday(f"due-{t['id']}", dt.date.fromisoformat(t["due"]), f"DUE: {t['title']}", TASK_INFO.get(t["id"]),
                             f"Proof of done: {t['evidence']}\nIf stuck: {t['escalate']}", stamp)
    for d in planner.schedule(data, start, 30, statuses, holidays, sam_active):
        if d["focus"]:
            t = d["focus"]
            lines += _allday(f"focus-{t['id']}-{d['date']:%Y%m%d}", d["date"], f"Focus (~{t['effort_min']} min): {t['title']}",
                             TASK_INFO.get(t["id"]), f"Proof of done: {t['evidence']}", stamp)
    for day, summary, info in MILESTONES:
        lines += _allday(f"milestone-{day}", dt.date.fromisoformat(day), summary, info, "", stamp)
    until = "20270120T235959Z"
    first = {"MO": 0, "WE": 2, "FR": 4}
    for code, hhmm, minutes, summary, desc in WEEKLY:
        d0 = start + dt.timedelta(days=(first[code] - start.weekday()) % 7)
        h, m = map(int, hhmm.split(":"))
        s = dt.datetime(d0.year, d0.month, d0.day, h, m)
        e = s + dt.timedelta(minutes=minutes)
        lines += ["BEGIN:VEVENT", f"UID:weekly-{code}@badgr-funding.local", f"DTSTAMP:{stamp}",
                  f"DTSTART;TZID=America/New_York:{s:%Y%m%dT%H%M%S}", f"DTEND;TZID=America/New_York:{e:%Y%m%dT%H%M%S}",
                  f"RRULE:FREQ=WEEKLY;BYDAY={code};UNTIL={until}", f"SUMMARY:{escape(summary)}",
                  f"DESCRIPTION:{escape(desc)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    folded = [f for line in lines for f in fold(line)]
    return "\r\n".join(folded) + "\r\n"


def write(path=Path("planning/badgr_funding_calendar.ics"), start=None):
    data = planner.load_tasks()
    text = build(data, start or dates.today(), planner.load_status(), planner.load_holidays())
    Path(path).write_bytes(text.encode("utf-8"))
    return path, text.count("BEGIN:VEVENT")
