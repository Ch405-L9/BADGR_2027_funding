# Scheduling — DRAFT (automation is OFF)
Updated 2026-10-08. **No scheduled job is installed.** CLAUDE.md requires your approval of scope and destination before any automated daily job.

## Manual use (default)
```
python3 -m badgr_funding.cli agenda            # today's focus, overdue, due soon, stale sources, missing inputs
python3 -m badgr_funding.cli agenda --days 30  # wider look-ahead
python3 -m badgr_funding.cli plan --start 2026-10-12   # regenerate 30-day and 90-day plans from any start date
python3 -m badgr_funding.cli task done dr_account --evidence "account created"
```

## Holidays
`planning/holidays_user_maintained.csv` (columns `date,name`) is maintained by you. No holiday dates are pre-filled or invented. Listed dates become light days.

## Optional cron (documented only; do not install without explicit approval)
If you approve it later, a local-only, report-only entry could look like this. It writes a file and has no network, email or submission ability:
```
# m h dom mon dow  command   (crontab is evaluated in the system timezone; CRON_TZ sets it explicitly)
CRON_TZ=America/New_York
30 7 * * 1-5  cd /home/t0n34781/projects/BADGR_Funding_Project_Starter && /usr/bin/python3 -m badgr_funding.cli agenda > exports/private/agenda_$(date +\%F).md 2>&1
```
- Output goes to `exports/private/` (gitignored).
- It never runs research, sends messages or submits anything.
- Check `CRON_TZ` support on your system (`man 5 crontab`) before relying on it; otherwise set the system timezone.

## Missing inputs
- Your approval of scope and destination, if you ever want this enabled.

## Calendar split (2026-10-08)
- **Time blocks** come from the owner's 12-week growth calendar (six lanes, afternoons, from 2026-10-12). Funding work, the SAM.gov status check and records work go in its **Thursday 1:00 PM funding and financial readiness** block. The Monday 2:30 PM brief includes `cli agenda --days 14`.
- **This project's calendar** (`cli calendar`) now holds only all-day due dates, focus days and milestones. Its former Mon/Wed/Fri timed blocks were removed to avoid duplicating that calendar and to keep mornings free; `ics.build(..., weekly=[...])` can still add timed blocks if wanted.
- **Gap:** the growth calendar's recurring blocks end around 2026-12-31, but the Verizon decision date (2027-01-12) and the two-year mark (2027-01-20) come later. Extend or replace the blocks at the 12-30 next-quarter review.
- **Focus tasks** are timed events at 8:00 AM ET (owner's choice, 2026-10-08), at least 30 minutes or the task's estimate if longer, with a 10-minute alert. Due dates and milestones stay all-day.
