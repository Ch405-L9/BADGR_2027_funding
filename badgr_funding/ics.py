"""iCalendar (RFC 5545) export of the funding plan: due dates, focus days, milestones, optional weekly blocks.

Deadlines are all-day (date-only stays date-only). Timed weekly blocks are off by default:
recurring time blocks come from the owner's growth calendar (Thursday 1:00 PM funding block).
When passed, weekly blocks are timed in America/New_York with a VTIMEZONE so DST is handled.
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
        "info": "Getting started: https://gtapexaccelerator.org/getting-started/ | Class calendar: https://gtapexaccelerator.ecenterdirect.com/events/ | Atlanta office: Jennifer White, (404) 894-3512, 75 5th St NW Ste 3000, Atlanta, GA 30308-1068 | Steps: intro class, New Client Application, counselor appointment."}
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
       "info": "ACE: https://aceloans.org/apply-for-a-loan/small-business-loans/ | SBA 8(a): https://www.sba.gov/federal-contracting/contracting-assistance-programs/8a-business-development-program | Both list a 2-year history requirement; formation date (2027-01-20 mark) may not be how it is counted, and all other criteria still apply. Not an eligibility determination."}
SAM = {"url": "https://sam.gov/", "location": "Online", "info": "https://sam.gov/ | https://www.grants.gov/ | Record CAGE and expiration when Active."}

TASK_INFO = {
    "sbdc_request": SBDC, "tax_review": VITA, "tax_packet": VITA, "apex_class": APEX,
    "dr_account": VERIZON, "dr_course1": VERIZON, "dr_course2": VERIZON, "dr_apply": VERIZON,
    "ec_tour": GEC, "atdc_quiz": ATDC, "kiva_decide": KIVA, "kiva_story": KIVA,
    "nsf_pitch": NSF, "prior_art": NSF, "discovery": NSF, "ace_8a_revisit": ACE,
    "sam_record": SAM, "sam_grantsgov": SAM, "sam_rank": SAM,
}
LISC_WATCH = {"url": "https://digitalready.verizonwireless.com/funding/details", "location": "Email",
              "info": "Application submitted 2026-10-08; active through end of 2026. LISC picks 10 finalists monthly. Finalist emails come from notifications@lisc.org (check spam). If selected: W-9 and ACH only through the official LISC channel. Not selected by year end = official decline letter."}
MILESTONES = [  # (date, summary, info, skip when this task is done)
    ("2026-12-07", "HARD STOP: Verizon Digital Ready courses must be complete", VERIZON, "dr_course2"),
    ("2026-11-01", "Verizon grant: check inbox/spam for notifications@lisc.org", LISC_WATCH, None),
    ("2026-12-01", "Verizon grant: check inbox/spam for notifications@lisc.org", LISC_WATCH, None),
    ("2026-12-31", "Verizon grant: last monthly finalist round of 2026", LISC_WATCH, None),
    ("2027-01-12", "Verizon Digital Ready final decisions due", VERIZON, None),
    ("2027-01-20", "2-year mark since formation: confirm ACE and SBA 8(a) criteria with APEX/SBDC", ACE, None),
]
APEX_ATL = {"url": "https://gtapexaccelerator.ecenterdirect.com/events/", "location": "Online (live webinar)"}
EVENTS = [  # owner-registered one-off events: (start YYYY-MM-DDTHH:MM, minutes, summary, info)
    ("2026-10-15T09:00", 180, "GT APEX: Introduction to Government Contracting",
     dict(APEX_ATL, info="Registered. Free live webinar; first step of APEX onboarding (then New Client Application, then counselor). Contact: Gerardo Arias-Chong (404) 894-8122. Covers the 7 phases of government procurement, SAM, FAR basics, DSBS, USASpending, subcontracting, state/local buying and BidMatch.")),
    ("2026-10-30T10:00", 90, "GT APEX: Mentor-Protege Programs Overview (DoD and SBA)",
     dict(APEX_ATL, info="Registered. Free live webinar. Contact: Jennifer White (404) 894-3512. Covers SBA and DoD mentor-protege programs and application criteria. Class calendar: https://gtapexaccelerator.ecenterdirect.com/events/")),
    ("2026-10-13T12:00", 120, "Webinar: The AI scheduler",
     {"url": "", "location": "Online", "info": "Registered (owner list 2026-10-08). Live setup demo of AI scheduling tools. Times shown in ET."}),
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


FOCUS_START = "08:00"   # owner's preferred daily focus time (2026-10-08)
FOCUS_MIN_MINUTES = 30


def _timed(uid, start_dt, minutes, summary, info=None, extra="", stamp="", alarm_min=10):
    end_dt = start_dt + dt.timedelta(minutes=minutes)
    desc = "\n".join(x for x in (extra, info["info"] if info else "") if x)
    ev = ["BEGIN:VEVENT", f"UID:{uid}@badgr-funding.local", f"DTSTAMP:{stamp}",
          f"DTSTART;TZID=America/New_York:{start_dt:%Y%m%dT%H%M%S}", f"DTEND;TZID=America/New_York:{end_dt:%Y%m%dT%H%M%S}",
          f"SUMMARY:{escape(summary)}"]
    if desc:
        ev.append(f"DESCRIPTION:{escape(desc)}")
    if info:
        ev.append(f"LOCATION:{escape(info['location'])}")
        if info.get("url"):
            ev.append(f"URL:{info['url']}")
    ev += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{escape(summary)}", f"TRIGGER:-PT{alarm_min}M", "END:VALARM", "END:VEVENT"]
    return ev


def build(data, start, statuses=None, holidays=None, sam_active=False, now=None, weekly=(), events=None):
    """weekly: optional (weekday code, HH:MM, minutes, summary, description) timed recurring blocks."""
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    statuses = statuses or {}
    events = EVENTS if events is None else events
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
            h, m = map(int, FOCUS_START.split(":"))
            s = dt.datetime(d["date"].year, d["date"].month, d["date"].day, h, m)
            lines += _timed(f"focus-{t['id']}-{d['date']:%Y%m%d}", s, max(FOCUS_MIN_MINUTES, t["effort_min"]),
                            f"Focus (~{t['effort_min']} min): {t['title']}", TASK_INFO.get(t["id"]),
                            f"Proof of done: {t['evidence']}\nDone? Run: python3 -m badgr_funding.cli task done {t['id']}", stamp)
    for day, summary, info, skip_task in MILESTONES:
        if skip_task and statuses.get(skip_task, {}).get("status") == "done":
            continue
        lines += _allday(f"milestone-{day}", dt.date.fromisoformat(day), summary, info, "", stamp)
    for when, minutes, summary, info in events:
        s = dt.datetime.fromisoformat(when)
        lines += _timed(f"event-{s:%Y%m%dT%H%M}", s, minutes, summary, info, "", stamp, alarm_min=30)
    until = "20270120T235959Z"
    first = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
    for code, hhmm, minutes, summary, desc in weekly:
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
