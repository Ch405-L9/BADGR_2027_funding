# Testing record
Real results only. Environment: Python 3.12.3, SQLite 3.45.1, Ubuntu 24.04 (owner-reported), stdlib only.

## Commands
```
python3 -m unittest discover -s tests -t . -v
python3 -m badgr_funding.schema_check context/business_profile.json context/business_profile.schema.json
python3 -m badgr_funding.draft_lint drafts context/claims_ledger.csv
python3 -m badgr_funding.redact .
python3 -m badgr_funding.cli init && python3 -m badgr_funding.cli import-seed && python3 -m badgr_funding.cli load-findings research/phase2_findings_2026-10-08.json
python3 -m badgr_funding.cli rank -v
```

## Phase 1 run — 2026-10-08 (America/New_York)
| Check | Result |
|---|---|
| Unit tests | Intermediate run: 27 run, 1 failed (`test_project_tree_is_clean`, the PRIVACY.md false positive below). After the doc fix and 3 added lint tests: 30 run, 30 passed |
| Schema validation | First run: INVALID, 1 error (`$.projects[2]: missing required key 'evidence'`). Fixed by adding a provenance label to BADGR Bolt (logged). Rerun: VALID |
| Draft lint (4 drafts) | All OK |
| Redaction scan | After docs were added: 1 finding (`docs/PRIVACY.md:23 credential_assignment`). A false positive: the doc quoted the pattern itself. The doc was reworded; the scanner was not weakened. Rerun: 0 findings (heuristic; see PRIVACY.md limitations) |
| `git check-ignore .env_sam-gov.json` | Ignored via `.gitignore:4:.env*` |

## Coverage (Phase 1)
- Schema: valid profile; missing required null field rejected; string in place of a number rejected; UEI pattern; bool vs. integer; street-address field rejected; every project has evidence.
- Claims: column set, unique IDs, known statuses, dated verification, designations stay SELF_CERTIFIED, metric scoped to the controlled test, URL checks reference the ledger.
- Drafts: all pass the lint; the C.Walts metric keeps "controlled" plus its date; the excluded claim (C-PROJ-05) is never cited; the metric is barred from the capability statement; no assumed pronouns; uncited lines, unknown IDs, banned claims, a missing marker and a missing section all fail; a negated certification statement passes.
- Redaction: every synthetic pattern detected; dates/UEI/NAICS not flagged; `.env*` and `secret*` files never opened (spy test); findings masked; project tree clean.

Not yet covered (later phases): CSV roundtrip, formula injection, dedupe, Decimal finance, loan math, DST deadlines, backup/restore, export completeness.

## Gate 1 follow-up run — 2026-10-08
| Check | Result |
|---|---|
| Unit tests | First run: 30 run, 1 failed (`test_ownership_percentage_null_is_valid` asserted the old null value). Replaced with tests for null validity, evidence when set, and no silent name normalization. Rerun: 32 run, 32 passed |
| Schema | VALID |
| Draft lint | All OK |
| Redaction scan | 0 findings; `badgr_legal/` skipped by design |

## Phase 2 run — 2026-10-08 (America/New_York)
| Check | Result |
|---|---|
| Unit tests | First run of new tracker tests: 72 run, 1 failed. The test expected computed 0, but a no-fee grant correctly earns cost_risk 10; the test was fixed, not the code. After adding research-data and privacy tests: 77 run, 2 failed (both false positives, below). Final: 78 run, 78 passed |
| Redaction scan | 3 findings on `tracking/opportunity_tracker.csv`: integer-cents amounts (a $2M award is a 9-digit cents value) matched the account-number pattern. Fix: the scanner blanks only `*_cents` CSV columns before scanning; all other cells are still scanned (tested). Rerun: 0 findings |
| Privacy marker test | First failed on "AGI": SBA 8(a) program rule text, not personal data. Markers narrowed to the owner's actual personal figures. Rerun: pass |
| DB / CLI | `init` applied 0001_init.sql; `import-seed` inserted 12 rows (all UNVERIFIED_CURRENT); `load-findings` updated 12, inserted 8; `export` wrote 20 rows; `rank -v` written to tracking/shortlist_2026-10-08.md |

### Phase 2 coverage
- **Migrations:** idempotent; DB rejects an override without a reason, invalid enums and an inverted amount range.
- **History/dedupe:** updates need a reason and write history; nothing is deleted; the same sponsor/program/cycle merges and keeps all sources; different cycles stay separate; a null-vs-set cycle is flagged, not merged.
- **Status:** fails closed on unknown or missing criteria, unverified or stale sources, unknown deadlines (never assumed rolling), passed deadlines, SAM not Active, the history gate (2027-01-20), and loans without a repayment analysis.
- **Scoring:** reproducible and ≤100; unknowns earn 0; debt scores lower; a material "no" is not ranked; override is shown with its reason; history readiness changes on the gate date.
- **Dates:** months in business, end-of-month add, date-only display, DST conversion (Nov 1 and Mar 8, 2026), staleness.
- **Money/CSV:** cents parsing incl. negatives and parentheses; formula-injection escape is reversible; full CSV round trip preserves every editable column; seed import is all unverified and idempotent; findings loader works.
- **Research data:** every admitted row has a dated official source; criteria are tri-state, and every "yes" has evidence; no personal income markers in tracked outputs.

## Gate 2 privacy correction run — 2026-10-08
- **Finding (advisor review):** commit 098210a (now replaced by ce22401) contained personal tax specifics in `context/discrepancies.md` (D16) and `business_profile.json` (`tax_filing_status`). The earlier privacy test missed them because it checked only a hand-picked file list.
- **Fix:**
  - D16, `tax_filing_status` and all loan cautions now say "tax follow-up pending (details in private/)".
  - The privacy test now scans every commit-eligible file (`git ls-files --cached --others --exclude-standard`) for personal markers, and checks that private folders are not commit-eligible.
  - Amended to ce22401 (owner-approved 2026-10-08), reflog expired, gc --prune=now; search of all git objects for the specifics returned 0 matches.
- **Other fixes:**
  - Stale seed notes are replaced when a fresh check lands (test added).
  - History and source checks export to `tracking/history.csv` and `tracking/source_checks.csv`, with cents fields shown as dollars.
  - In-kind services show `n/a-service` instead of a submit-ready flag.
- **Result:** 80 run, 80 passed. Redaction scan 0 findings, after rewording one TESTING.md example that tripped the account-number pattern. Draft lint all OK. Schema VALID. The database was rebuilt from tracked files with identical results.

## Phase 3 run — 2026-10-08 (America/New_York)
| Check | Result |
|---|---|
| Unit tests | Final: 105 run, 105 passed. New: finance (loans, cash flow, affordability, double-funding, reimbursement gap), finance report generation, NSF pitch section limits, private screening resolution, archive section, lint rules |
| Draft lint (24 drafts incl. outreach) | First run: 1 error, a C.Walts metric line missing its test date (draft fixed). Second run: 2 errors where "100%" ownership tripped the accuracy ban (rule narrowed to accuracy/success/uptime wording; ownership test added). Final: all OK |
| NSF pitch limits | 1144/3500, 1072/3500, 474/1750, 457/1750 characters (tags stripped) |
| Finance | Kiva $5k/24 = $208.33/mo; Kiva $10k/36 = $277.78/mo; ACE $15k/60 at 7.75% = $302.35/mo, total credit cost $3,691.30 incl. $550 fees, ~9.34% approx. APR. Cash flow and affordability BLOCKED (missing opening cash, monthly revenue/expenses, existing debt), as designed |
| Redaction scan | 0 findings |
| Privacy test (all commit-eligible files) | pass |

## Gate 3 fixes run — 2026-10-08 (after advisor review)
- **Real finance figures:** they now stay private. Inputs are read from `private/financial_inputs.csv`, and balances are written only to `exports/private/`. A test asserts that tracked outputs never contain the input or derived values, and another that the tracked template stays blank.
- **YTD averaging:** it now uses a `2026_ytd_through` date instead of today's month. A test runs it with January and November reference dates.
- **Copy fixes:**
  - "earned" changed to "gross receipts";
  - "applicant-described" removed from external copy (NSF pitch, founder bio);
  - the grant need statement no longer implies causation;
  - the invented capacity rule became an owner question.
- **Screening answers:** citizenship, residency, employment and prior Digital Ready answers now resolve from private/screening.json, like the Kiva items. The public shortlist shows them as unknown.
- **New docs and checks:**
  - `grant_narrative_impact.md` added;
  - checklists and finance docs now carry Missing-inputs sections (tested);
  - the NSF checklist notes that the SBIR 2026 rule changes are unconfirmed.
- **Result:** 108 run, 108 passed; draft lint 25 OK; redaction 0 findings; schema VALID.

## D18 update run — 2026-10-08
- Lint now auto-excludes DISPUTED and SUPERSEDED claims (test added). A same-day owner estimate was briefly applied, then superseded when the owner confirmed the preparer's figures; drafts were restored. Detail kept privately.
- Result: all tests pass; draft lint all OK; schema VALID; redaction 0 findings.

## Phase 4 run — 2026-10-08 (America/New_York)
| Check | Result |
|---|---|
| Unit tests | 123 run, all passed. New planner tests: weekends/holidays light, dependency and due-date order, not_before, done tasks, SAM-only tasks, deterministic start date, weekly leftovers, real task file valid (Verizon course 2 lands before 2026-12-07), agenda overdue/due-soon/stale/archived exclusion, DST deadline display, blank private inputs listed without values, SAM activation trigger, weekend agenda, status-file roundtrip |
| Dry run | `cli plan` wrote the 30-day and 90-day plans starting 2026-10-08; `cli agenda` shows today's focus (SBDC request), 8 items due within 14 days, 1 never-checked source (GMSDC MBE), missing private financial inputs, SAM pending |
| Automation | None installed; cron documented OFF in docs/SCHEDULING.md |

## Phase 5 run — 2026-10-08 (America/New_York)
| Check | Result |
|---|---|
| Unit tests | 131 run, all passed. New: backup/restore roundtrip (hashes + SQLite integrity), tampered backup detected, unsafe archive path rejected, backups gitignored, sanitizer strips tags/internal sections/discrepancy refs/repo paths, leaky packet refused and removed, real packet clean and complete, reports generate. First full run failed once: the privacy test flagged `export.py` because it lists blocked words; exempted as a guard file (same as the test file) |
| Backup | `cli backup` wrote 34 files to backups/private/ (gitignored) |
| Restore test | `cli restore-test`: 34 files, 0 hash mismatches, db integrity ok, rows: 20 opportunities, 51 criteria, 23 sources, 220 history |
| Shareable packet | First build REFUSED (internal discrepancy refs in marketing plan and shortlist). Sanitizer extended; shortlist kept internal. Rebuilt: 16 files + zip in exports/public/, completeness check: none missing, 0 sanitization problems |
| Redaction scan | 0 findings |
| Push | Not performed: BADGR_2027_funding is still public (checked 2026-10-08) |

### Coverage against BUILD_PROMPT Phase 5 list
- nulls, Decimal cash flows, loan calculations, dates/timezones, DST: test_finance, test_tracker (DateTests), test_planner
- duplicate cycles and changed source rules: test_tracker (HistoryAndDedupeTests)
- ineligible and unknown candidates: test_tracker (StatusTests, ScoringTests)
- CSV roundtrip and formula-injection-safe cells: test_tracker (MoneyAndCsvTests)
- backup/restore: test_phase5
- sanitized exports and package completeness: test_phase5
- secret/identifier scanning: test_redact, test_research_data

## Gate 5 fixes run — 2026-10-08 (after advisor review)
- **Outsider read-through:** all 16 packet files read in full. Fixed in the source drafts:
  - internal process lines (unexplained $25, blocked cash flow, "not for distribution", "not stored in repository") moved to Review notes;
  - "applicant-described" removed from the R&D sheets;
  - links to non-packet documents removed;
  - the stale "revenue not reconciled" line updated;
  - impact narrative changed from "already participates" to "plans to use";
  - service menu now lists the device repair/re-imaging and IoT work delivered in 2025.
  The packet README states its audience: advisors, not public posting.
- **Retracted owner estimates:** removed from tracked files (ledger rows now neutral placeholders; D17/D18, TESTING and HANDOFF neutralized). Full detail preserved in private/superseded_claims.csv.
- **Result:** 131 tests pass; draft lint all OK; redaction 0 findings; packet rebuilt (16 files, none missing, 0 sanitization problems).
- **Review limits:** this was a same-model review (Claude reviewing Claude's work, with an automated advisor). It is not independent professional, legal or tax verification.

## Calendar and push-prep run — 2026-10-08
- New `cli calendar` writes planning/badgr_funding_calendar.ics: 53 events at the time; 49 after the 2026-10-08 consolidation, which made weekly blocks optional and off by default (all-day due dates and focus days, 3 milestones, 3 weekly timed blocks with VTIMEZONE America/New_York). Tests check CRLF, 75-octet folding, unique UIDs, escaping, all-day DTEND, RRULE/TZID, and done-task exclusion.
- **First run caught:**
  - the redaction scanner flagged public office emails/phones, now allowlisted explicitly;
  - the privacy test caught a tax-form word in calendar text, reworded.
- **Privacy test hardened:** case-insensitive, with personal values loaded from gitignored private/privacy_markers.txt instead of being hard-coded in the tracked test.
- **Result:** 138 tests pass; redaction 0 findings.
