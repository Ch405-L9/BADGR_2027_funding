# Handoff — resume point
Last update: 2026-10-08 (America/New_York). Plan: `docs/PLAN.md`.

## State
**Phases 1-4 committed (latest 007bec8). Phase 5 done, awaiting Gate 5 owner review (uncommitted). Not pushed: repo still public.** Commits: 5c6afb7 Phase 1, ce22401 Gate 1 follow-up (amended; tax specifics purged), 89354a8 Phase 2. No remote configured.
The owner confirmed on 2026-10-08 that the permission switch was done ("perms authd") before Phase 2.

## Rebuild the private DB (gitignored) from tracked files
```
python3 -m badgr_funding.cli init
python3 -m badgr_funding.cli import-seed
python3 -m badgr_funding.cli load-findings research/phase2_findings_2026-10-08.json
python3 -m badgr_funding.cli rank -v
```

## Phase 2 outputs
- Engine: `badgr_funding/{db,dates,money,csv_safe,applicant,status,scoring,dedupe,csvio,cli}.py`, `migrations/0001_init.sql`
- Data:
  - `research/phase2_findings_2026-10-08.json` (20 rows, official sources dated)
  - `tracking/opportunity_tracker.csv` (export view)
  - `tracking/shortlist_2026-10-08.md` (ranked, with blockers)
- Docs: `docs/SCORING.md`, `docs/SEARCH_PLAYBOOK.md`, `docs/RESEARCH_QUEUE.md`, `docs/TESTING.md`
- Privacy: real finance inputs/outputs only under private/ and exports/private/; screening answers (citizenship, residency, employment, prior grants, Kiva items) resolve from private/screening.json; public shortlist shows them as unknown.
- Grant narrative (impact) added; copy fixes (no 'earned', no 'applicant-described' in external copy, no invented capacity rule).
- Tests: 80 passing
- Durable logs: `tracking/history.csv`, `tracking/source_checks.csv`

## Phase 3 outputs (Gate 3, uncommitted)
- Finance engine: `badgr_funding/loans.py`, `cashflow.py`, `finance_report.py`; `python3 -m badgr_funding.cli finance` writes `finance/` (loan comparison, debt schedules, blocked cash flow, repayment analysis, 3-year template)
- `finance/assumptions.csv` (A- IDs); `finance/equipment_quote_register.csv`; `finance/schedule_c_2025.md`
- Drafts (25 linted): exec summary, business plan, marketing/sales, 90-day plan, grant narratives (short/standard), loan narrative, use-of-funds scenarios, workspace, transport, property, two R&D concept sheets, NSF Project Pitch, Kiva profile, Verizon prep; outreach briefs (SBDC, APEX, Gwinnett center, lender)
- Checklists: ownership, allowable cost/match/reimbursement, SAM/Grants.gov, per-opportunity (Verizon, Kiva, NSF, ACE)
- `docs/DOCUMENT_INVENTORY.md`; private screening (migration 0002; `rank --private` in terminal only); archived section in rank
- Tests: 108 passing

## Gate 3 review items for the owner
1. DONE 2026-10-08: Q3 answered (stored privately); Kiva passes private screening.
2. DONE: Q1 confirmed (citizen and GA resident).
3. Push destination: owner's `Ch405-L9/BADGR_2027_funding` exists but is PUBLIC (empty as of 2026-10-08). Do not push until it is set to Private, or push only the Phase 5 sanitized export.
4. `drafts/).pdf`: what is it? Not opened; gitignored.
5. To unblock cash flow: copy `templates/financial_inputs.csv` to `private/financial_inputs.csv` (gitignored) and fill cash_on_hand, monthly_business_expenses, existing_debt_payments, 2026_ytd_revenue, 2026_ytd_through. `cli finance` then writes real balances only to `exports/private/`.
6. DONE: owner confirmed the tax preparer's 2025 Schedule C (D18 resolved). Services: device repair, IoT installs, OS re-imaging, drone photography, marketing. Asset list: ask the tax preparer.
7. Write the Kiva personal story yourself; review all drafts.
8. Approve the Phase 3 commit and the Phase 4 start (daily/weekly schedule, agenda command, dry run).

## 2026-10-08 late updates
- BADGR_Harness and badgr_bolt-src made public by owner; current config files checked: no secrets. Git history not scanned.
- Kiva passes private screening (eligibility yes; only repayment analysis blocks).

## Phase 4 outputs (Gate 4)
- `planning/tasks.json` (editable task list with dependencies, effort, proof of done, escalation), `planning/task_status.csv`, `planning/holidays_user_maintained.csv` (empty by design)
- `badgr_funding/planner.py`; CLI: `plan --start`, `agenda --date --days`, `task done|skipped|todo ID --evidence`
- Generated `planning/plan_30_day.md` and `planning/plan_90_weekly.md`; `docs/SCHEDULING.md` (cron OFF)
- Tests: 123 passing

## Gate 4 review items
1. Review `planning/plan_30_day.md`: task order and due dates; add any holidays you observe.
2. Mark tasks as you finish them (`cli task done ...`), then `cli agenda` each morning.
3. DONE 2026-10-08: BofA 2025 statements reviewed; income reconciled and business items logged privately (see private/tax_2025_summary.md). Next: business-account statements and customer tagging (tasks added).
4. Mark which Cash App person-to-person payments and cash deposits were customers (privately).
5. Approve the Phase 4 commit and the Phase 5 start (quality/security/export, sanitized packet, backup/restore).
6. Push: `BADGR_2027_funding` must be set to Private first.

## Phase 5 / Gate 5 summary
**Created:**
- badgr_funding/backup.py, export.py, reports.py; CLI backup, restore-test, export-packet, reports
- exports/public/badgr_packet_2026-10-08/ (+ .zip)
- docs/SOURCE_REGISTER.md, docs/MISSING_INPUTS.md, docs/PERMISSIONS_RECOMMENDATION.md
- tests/test_phase5.py

**Checks:** 131 tests pass; redaction 0 findings; backup restore verified; packet complete and clean.

**Unresolved claims:** C.Walts repo still private (metric stays scoped, kept off the capability statement); BADGR Bolt "24 deployments" excluded; GMSDC MBE fees unverified; SBIR 2026 rule changes unconfirmed on an agency page.

**Readiness blockers (nothing is submission-ready):**
- Cash flow and repayment blocked until private/financial_inputs.csv is filled.
- Tax follow-up (amended return question) open.
- Signed operating agreement unconfirmed.
- SAM pending.
- Verizon courses not started.
- NSF pitch needs a prior-art review and customer interviews.

**Next owner actions:**
1. Today's agenda: request an SBDC appointment.
2. Fill private/financial_inputs.csv.
3. Tax help with private/tax_2025_summary.md.
4. Optionally apply the permissions recommendation.
5. Set the repo to Private if you want a push; otherwise share only the exports/public packet.
6. Approve the Phase 5 commit.

## Push disclosure (read before any push)
- Pushing this repo sends its **entire git history**, not just the packet. To share only the packet, copy `exports/public/badgr_packet_<date>/` into a separate folder or repo.
- **What tracked files contain:**
  - UEI, legal and professional names, Georgia address (city/ZIP);
  - 2025 business tax figures (receipts, depreciation, net loss);
  - 100% ownership, education record, SAM self-certified demographic designations;
  - program eligibility statuses.
- **Older commits contain items since made private:**
  - `89354a8` holds citizenship, residency and employment answers recorded as "yes" before they moved to private/screening.json.
  - `9e7e620` holds the owner's superseded 2025 estimates.
  - Removing them means rewriting history (e.g. a fresh orphan branch with the current tree). That's an owner decision, needed only if pushing.
- `BADGR_2027_funding` was public on 2026-10-08. Push only to a **private** repo.

## Permissions actually configured
- This project has **no** `.claude/settings.json` or `.claude/settings.local.json` (checked 2026-10-08), so no project deny rules exist yet. See docs/PERMISSIONS_RECOMMENDATION.md.
- "Bypass-permissions mode is off" is the owner's statement ("perms authd"); this session cannot verify it.

## Review limits
- Same-model review only; not independent professional, legal or tax verification. Program rules came from WebFetch summaries and need re-checking with sponsors before any application.

## 2026-10-08 push prep
- private/financial_inputs.csv partly filled (2025 revenue; monthly business expenses as an estimate floor). Cash flow still needs cash on hand, 2026 YTD revenue + through-date, and current debt payments.
- Remote `origin` set to github.com/Ch405-L9/BADGR_2027_funding. Push held: repo was still PUBLIC when checked 2026-10-08.
- One personal item set aside by the owner (not recorded here).

## 2026-10-08 final session state
- **Calendar:** planning/badgr_funding_calendar.ics (import into Google/Apple/Outlook). Verified links table is in planning/DAILY_GUIDE.md.
- **Private inputs:** cash on hand recorded. Cash flow still needs 2026 YTD revenue + through-date and current debt payments.
- **Push:** `publish` branch = clean single-commit snapshot (no history, no personal values). Push with `git push -u origin publish:main` ONLY after the GitHub repo is Private. `main` keeps full local history and must not be pushed as-is.
- **Resume:** `python3 -m badgr_funding.cli agenda`.

## 2026-10-08 calendar consolidation
- Owner adopted a 12-week, six-lane growth calendar (badgr_growth_starter.zip, owner's file, unchanged). This project's calendar no longer has timed weekly blocks: 49 all-day events (due dates, focus days, milestones). SAM check and records work moved to the growth calendar's Thursday 1:00 PM funding block; agenda text updated.
- SBDC request submitted by owner 2026-10-08 (task marked done).
- **Google Calendar:** an earlier version was imported. Google import does not remove events dropped from a file: delete the imported "BADGR Funding" calendar and re-import; import the growth calendar into its own separate calendar.
- **Gap:** recurring blocks end ~2026-12-31; milestones on 2027-01-12 and 2027-01-20 follow. Decide at the 12-30 review.
- **Open:** Manus review files not yet reviewed. (Two root .txt files with personal data moved to private/notes/ 2026-10-08.)
- **Manus review fixes (2026-10-08):** (1) cash-flow `existing_debt_payments` now defaults to unknown (None) and blocks the forecast instead of silently meaning $0; (2) the 2027-01-20 calendar milestone and DAILY_GUIDE no longer say "eligible to apply": 2 years from formation may not equal the programs' history test, and other criteria apply. Manus also found the repo was anonymously readable while public (business profile with UEI and 2025 business tax figures); it is private again. Manus's funding revalidation never completed; no program facts came from it.

## 2026-10-08 evening update
- **Verizon Digital Ready:** owner completed 2/2 courses and submitted the application 2026-10-08 (LISC confirmation; active through end of 2026; finalists emailed from notifications@lisc.org). Tracker `verizon` = SUBMITTED_BY_OWNER, follow-up 2026-11-01. Calendar drops the 12-07 course hard stop and adds monthly inbox checks (11-01, 12-01, 12-31).
- **GT APEX:** client profile choices recorded in docs/APEX_PROFILE.md (9 NIGP codes verified against the owner's catalog copy). Mentor-Protege webinar 2026-10-30 10:00 ET added to the calendar as a timed event with a 30-minute alert; Atlanta office contact added.
- **HUBZone:** owner's SBA map screenshot (2026-10-08, private) shows the business address just outside the shaded qualified areas, so HUBZone does not look available on the current map. Confirm with the map's text result before treating as final.
- New root files moved to private/notes/ (owner notes, NIGP catalog, screenshots, a Verizon course transcript).
