# BADGR Funding Project Starter
This starter contains sanitized context, an execution prompt, seed research and blank templates. It is NOT the finished tracker/application packet. Claude Code builds those after plan approval.

## Start
1. Unzip into a NEW private project folder. Preserve original files elsewhere.
2. Read context/business_profile.md and pending_questions.md.
3. Review Claude Code /permissions. Do not grant broad home-directory or credential access. Restrict writes to this project. Do not enable permission bypass.
4. Launch Claude Code in this folder. Enter Plan Mode; ask it to read prompts/BUILD_PROMPT.md and create a plan without implementation.
5. Review the plan, then approve phase 1 only. Continue by explicit phase gates.
6. Copy in SANITIZED evidence files only. Never copy the original secret-bearing source file.

## Initial instruction
Read CLAUDE.md and prompts/BUILD_PROMPT.md. Remain in Plan Mode. Audit the supplied context and propose the complete project implementation plan, phase gates and tests. Do not implement yet. Ask only blocking questions; preserve unknowns.

## Scope
Draft packet, local grant/loan tracking, source-backed discovery, daily guide, equipment/workspace/transport budgets, financial templates, handoffs and tested exports. No automated applications, emails, purchases or awards guarantees.

## Provenance
Business/SAM: user supplied registration materials and Oct 7 screen.
Founder: Sept 30 resume, master profile and cover-letter sources. Claims preserved as applicant-reported; URLs and metrics require independent verification.
Methods: official Anthropic and community URLs in docs/CLAUDE_CODE_METHODS.md.
Credentials removed. Full address/contact/banking/tax information omitted. Redaction does not remediate exposure in the original source: review credential rotation separately.

## Tracker CLI (implemented in Phase 2; stdlib only, local only)
The database `data/funding.sqlite` is private and gitignored. You can rebuild it from tracked files at any time:
```
python3 -m badgr_funding.cli init                       # create/migrate the database
python3 -m badgr_funding.cli import-seed                # 12 starter seeds, all UNVERIFIED_CURRENT
python3 -m badgr_funding.cli load-findings research/phase2_findings_2026-10-08.json
python3 -m badgr_funding.cli rank -v                    # ranked by category, with blockers and next actions
python3 -m badgr_funding.cli export                     # tracking/opportunity_tracker.csv + history.csv + source_checks.csv
python3 -m badgr_funding.cli list --type loan --tier NONE --status ROLLING_CONFIRMED
python3 -m badgr_funding.cli show kiva                  # one row with criteria and sources
python3 -m badgr_funding.cli history kiva               # every change, with reason
python3 -m badgr_funding.cli update kiva --set next_action="Call Kiva" --reason "owner note"
python3 -m badgr_funding.cli update kiva --set override_score=80 override_reason="owner priority" --reason "override"
python3 -m badgr_funding.cli check-source kiva --url https://www.kiva.org/borrow --status ROLLING_CONFIRMED --method "manual browser check"
python3 -m badgr_funding.cli import tracking/opportunity_tracker.csv --reason "spreadsheet edits"
python3 -m badgr_funding.cli finance                    # finance/: loan scenarios, schedules, cash flow (blocked until inputs exist)
python3 -m badgr_funding.cli rank --private             # terminal only: applies private/screening.json
python3 -m badgr_funding.draft_lint                     # every draft line cites a claim (C-) or assumption (A-)
python3 -m badgr_funding.cli agenda                     # daily agenda: focus task, overdue, due soon, stale sources
python3 -m badgr_funding.cli plan --start 2026-10-12    # regenerate 30-day / 90-day plans
python3 -m badgr_funding.cli task done sbdc_request --evidence "appointment booked"
python3 -m badgr_funding.cli backup                     # private backup (backups/private/, gitignored)
python3 -m badgr_funding.cli restore-test               # verify latest backup in a temp folder
python3 -m badgr_funding.cli export-packet              # sanitized shareable packet in exports/public/
python3 -m badgr_funding.cli reports                    # docs/SOURCE_REGISTER.md + docs/MISSING_INPUTS.md
python3 -m badgr_funding.cli calendar                   # planning/badgr_funding_calendar.ics (import into any calendar)
python3 -m unittest discover -s tests -t . -v           # full test suite
```
Scores are a prioritization aid, not odds of award (docs/SCORING.md). Nothing is ever submitted or sent by these tools.
