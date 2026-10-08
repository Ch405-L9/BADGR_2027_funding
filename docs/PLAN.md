# BADGR Funding Operations — Implementation Plan (DRAFT, pending owner approval)

## Context
BADGRTECHNOLOGIES LLC (Georgia LLC, formed 2025-01-20, Lawrenceville/Gwinnett, NAICS 541511/541519, UEI U9GUGKVFGCA9, SAM "Submitted", CAGE pending) needs a private, local-first system to find, rank, prepare and track every funding avenue it may qualify for. That includes grants, loans, prizes, workspace, equipment, business-purpose transport, R&D and later building ownership. It also covers "odds-improving" levers: advisory services, certifications, college or accelerator affiliation, and memberships. The work splits into **pre-SAM-activation** and **post-activation** tracks. The project is starter-only today. This plan implements prompts/BUILD_PROMPT.md in five gated phases. Nothing is submitted, sent, purchased or scheduled.

Today: 2026-10-08 (America/New_York). Seed date 2026-10-07 is historical evidence only.

---

## 1. Audit findings

### 1a. Security / privacy (resolve before Phase 1)
1. **Credential-bearing original is inside the project.** On 2026-10-08 the owner renamed it to `.env_sam-gov.json`. It now matches the `.gitignore` `.env*` rule, but it is still in the project root.
   - **I have not read it.** The project rules prohibit it.
   - `.gitignore` only affects git. It does not stop Claude's tools or other programs from reading the file.
   - Execution-phase control: add a `/permissions` deny rule for `Read(./.env*)` (exact syntax to be confirmed against the official permissions docs), or move the file outside the project.
   - Rotating any credentials inside it is still recommended (README).
   - The phase scanners (`redact-scan`, export) must skip `.env*` files rather than open them.
   - Owner to confirm the sanitized profile still reflects the original (its mtime is newer than as_of 10-07).
2. **Bypass-permissions mode** is on for planning only. The owner will switch to normal mode with project-scoped `/permissions` before execution. **Phase 1 starts only after that.**
3. The project is not a git repo. `git init` is optional and needs owner approval. `.gitignore` is not access control.

### 1b. Factual discrepancies (flag, do not resolve)
| Item | Conflict | Handling |
|---|---|---|
| Legal/signing name | "Anthony Grant" / "Brandon Anthony Grant" / "Brandon A Grant" | Keep all three; signing name = null until official doc |
| Ownership % | null; control evidence absent | Blocks submission; not build |
| Receipts | SAM $815 metric vs. unknown tax revenue | `sam_metric_not_tax_revenue`; actuals null |
| Entity classification | LLC vs. possible sole-prop SAM classification | APEX review task |
| SAM expiration | unknown (older extract ignored) | null; refresh on activation |
| CAGE | pending | null |
| Designations | Self-cert SDB, minority/Black-owned | Never equated with 8(a)/MBE/HUBZone |
| Business age | ~20.5 months on 2026-10-08 | Computed field. Gates any "N years in business" rule (e.g. ACE 2-yr → eligible on or after 2027-01-20, if confirmed) |
| Education | Northeast State Technical College (Tennessee), degree not completed | Do not assume Georgia college affiliation |
| Project metrics | C.Walts 17/17, 10/10, 84/125 ms (controlled 2026-08-12) | Scope-locked wording in claim ledger |
| Bolt deployments | 24 GitHub Pages deploys | Not users or revenue |
| Credentials/URLs | Coursera verify links, GitHub, portfolio | Unverified until approved network check |

### 1c. Tooling (verified read-only)
- Python 3.12.3, SQLite 3.45.1, `zoneinfo` with America/New_York tzdata works. Stdlib only: `sqlite3`, `csv`, `json`, `decimal`, `datetime`, `zoneinfo`, `argparse`, `unittest`, `hashlib`, `re`, `shutil`.
- **No PDF renderer** (no pandoc, wkhtmltopdf or reportlab). Deliverables are Markdown/CSV, and PDF is recorded as a blocker. No empty PDFs.
- **Network:** only WebSearch/WebFetch on official sponsor domains, after approval. Firecrawl and other paid scrapers are excluded (paid API, forbidden). If research is denied, the fallback is a manual research queue, never fabricated rows.

---

## 2. Ranking model (meets "highest to lowest" without odds)
Each opportunity gets a transparent **priority score (0–100)**. It is not a likelihood of award. Separate sub-scores are shown:
- `value_score`: amount range relative to stated needs (null amount → 0 points, flagged).
- `fit_score`: matched known facts (geography, NAICS, for-profit, ownership, stage). Each criterion is yes/no/unknown, and unknown earns no points.
- `readiness_score`: prerequisites met now vs. blocked.
- `effort_score`: inverse prep hours.
- `cost_risk_score`: fees, debt, guarantee and collateral count against.

Owner override requires a reason and is logged. **Ready-to-submit fails closed** if any material eligibility field is unknown.

**Prerequisite tier** (sorts pre/post registration):
`NONE` → `UEI_ONLY` → `SAM_ACTIVE` → `GRANTS_GOV_ROLE` → `HISTORY_MIN_YEARS` → `CERTIFICATION_REQUIRED` → `COLLATERAL/REPAYMENT_PROOF`.

**Separate lists, never merged:** grant/prize · loan/credit support · advisory/no-cost service · workspace · equipment · transport · R&D (SBIR/STTR-type) · contracting readiness · odds-improvement levers.

**Odds-improvement lever categories** (research queue only, all UNVERIFIED, using search strategies rather than recalled facts):
- Advisory: SBDC, APEX, SCORE, Gwinnett Entrepreneur Center, Women's/Minority Business centers (MBDA-type).
- Certifications the owner could pursue: third-party MBE (e.g. regional NMSDC affiliate), SBA 8(a) (with reasons it is not established now), GA state/local vendor registrations, HUBZone (address-based check, owner-run).
- Affiliation: Georgia college/university incubators, accelerators, maker/innovation centers.
- Memberships: chambers (Gwinnett), NASE, industry groups. Track membership cost against benefit.
- Capacity: credit-builder steps, business banking separation, bookkeeping, a capability statement for procurement.

---

## 3. File tree by phase

```
CLAUDE.md                      (unchanged unless owner approves)
.gitignore                     (+ secret_*, data/; .env* already present)
docs/
  PRIVACY.md  SCHEMA.md  SEARCH_PLAYBOOK.md  SCORING.md  TESTING.md  HANDOFF.md
  RESEARCH_QUEUE.md  CLAIMS_POLICY.md
context/
  business_profile.schema.json        (P1)
  claims_ledger.csv                   (P1: id, exact_wording, source, source_date,
                                       verified_at, method, scope, confidence, permitted_reuse)
  discrepancies.md                    (P1)
drafts/ (every file headed DRAFT + verification date + missing-inputs list)
  founder_bio.md  company_overview.md  capability_statement.md  service_menu.md   (P1)
  exec_summary.md business_plan.md marketing_sales_plan.md 90_day_delivery.md     (P3)
  grant_narrative_{short,standard,impact}.md  loan_narrative.md                   (P3)
  use_of_funds_scenarios.md ($5k/$10k/$15k/$25k/$50k, labeled planning scenarios)
  workspace_comparison.md transport_alternatives.md property_readiness.md
  rd_concept_retrieval_reliability.md  rd_concept_routing_validation.md
  checklists/{ownership,allowable_cost_match,sam_activation_grantsgov,per_opportunity/*}.md
  outreach/{sbdc,apex,gwinnett_center,lender_intro}.md   (drafts only, never sent)
badgr_funding/  (Python package, stdlib)
  __init__.py  cli.py  db.py  migrations/0001_init.sql 0002_*.sql
  models.py  importer.py  exporter.py  dedupe.py  scoring.py  status.py
  dates.py  money.py  cashflow.py  loans.py  agenda.py  packet.py  redact.py
  csv_safe.py  backup.py  handoff.py
data/        private: funding.sqlite (gitignored)
research/    seed_opportunities.csv (kept) · sources/ (short excerpts + URL + checked_at)
tracking/    opportunity_tracker.csv (export view, regenerated) · source_checks.csv · history.csv
templates/   quote_register.csv financial_inputs.csv (kept; extended columns via migration)
finance/     cashflow_12mo_{base,downside}.csv projection_3yr_template.csv
             debt_schedule.csv loan_offer_comparison.csv repayment_analysis.md
planning/    DAILY_GUIDE.md (kept) · plan_30_day.md · plan_90_weekly.md · holidays_user_maintained.csv
exports/public/   sanitized packet (P5) · exports/private/ (gitignored)
backups/private/  (gitignored)
tests/       test_*.py + fixtures/synthetic_*.csv|json
MANIFEST.json  README.md  (updated each phase)
```

**Tracker schema change.** The existing `tracking/opportunity_tracker.csv` header lacks: sponsor, cycle, source_quote/locator, checked_at_tz, lifecycle_status, geography, for_profit_eligible, ownership_requirements, revenue_history_rules, rolling, registrations_required, prerequisite_tier, match/reimbursement, disallowed_uses, term, repayment_gate, contact, owner, submission_status, scores, override_reason.
- SQLite becomes canonical. The CSV becomes an export view.
- All 12 seed rows import as `UNVERIFIED_CURRENT` with eligibility `unknown`.

**Status model:**
- `source_status`: UNVERIFIED_CURRENT / VERIFIED_OPEN / VERIFIED_CLOSED / ROLLING_CONFIRMED / DISCONTINUED / CHANGED.
- `application_status`: NOT_STARTED / PREPARING / BLOCKED / READY_FOR_OWNER_REVIEW / SUBMITTED_BY_OWNER / AWARDED / DECLINED / WITHDRAWN.
- A missing deadline is never treated as rolling. Date-only deadlines stay date-only.

**CLI** (syntax documented only after implementation): `init`, `import`, `export`, `add`, `update`, `list --type --tier --status`, `rank`, `check-source`, `agenda`, `packet`, `backup`, `restore`, `handoff`, `redact-scan`.

---

## 4. Phases, gates, acceptance tests

**Phase 1 — Evidence & context**
- Work: JSON validation and schema, claims ledger (every resume/SAM claim), discrepancies.md, the four DRAFT positioning docs, PRIVACY.md, .gitignore hardening.
- Acceptance:
  - Profile validates against the schema.
  - Every factual sentence in the drafts maps to a claim ID.
  - No draft contains "100% accuracy", customer or revenue claims, or 8(a)/MBE claims.
  - `redact-scan` finds no TIN/EIN patterns, account numbers or credentials.
- **Gate 1:** owner reviews the audit and drafts.

**Phase 2 — Funding system**
- Work: SQLite and migrations, CLI, import/export, dedupe (sponsor+program+cycle), history, scoring, research queue, SEARCH_PLAYBOOK, and fresh official-source checks (if approved) for the seeds plus new candidates in all categories.
- Tests:
  - CSV roundtrip.
  - Formula-injection-safe cells (`=+-@` prefixed).
  - Duplicate cycles merge with sources preserved.
  - Changed rule produces a history row, never a delete.
  - Unknown eligibility means not ready.
  - Missing deadline is not rolling.
  - Timezone and DST deadline display.
  - Score reproducibility.
  - Override needs a reason.
- **Gate 2:** tested tracker plus an evidence-backed ranked shortlist, split by type and tier.

**Phase 3 — Preparation packet**
- Work: all drafts listed in §3, plus Decimal finance modules.
- Tests:
  - Null actuals block ratios and affordability (no zero substitution).
  - Loan amortization against known fixtures.
  - Cash-flow sources kept separate (owner/grant/pending/debt/revenue).
  - Reimbursement cash-flow gap gate.
  - Double-funding check.
  - Every doc carries DRAFT, a date and a missing-inputs list.
- **Gate 3:** packet, budgets and factual review.

**Phase 4 — Daily operation**
- Work:
  - 30-day daily and 90-day weekly plans (start date configurable).
  - `agenda` covering deadlines, stale sources (>N days), missing docs and lender questions.
  - A SAM-activation insert task set.
  - A user-maintained holiday file.
  - Cron documented but OFF.
- Tests: agenda fixtures, staleness, DST, and the activation trigger.
- **Gate 4:** dry run plus owner-reviewed schedule.

**Phase 5 — Quality, security, export**
- Work:
  - Full unittest suite with synthetic fixtures.
  - Backup/restore test.
  - Sanitized `exports/public/` packet with a completeness check.
  - Secret/PII scan with documented limitations.
  - TESTING.md with real results, plus HANDOFF, MANIFEST and README.
- **Gate 5:** a list of files, actual checks, unresolved claims, blockers and the next owner action.

Run command for all tests: `python3 -m unittest discover -s tests -v`.

---

## 5. Unresolved facts (kept null/placeholders, block submission not build)
Signing name · ownership % and control docs · 2025/2026 YTD revenue · tax filing status · cash and debt · bank records · SAM expiration/CAGE · entity classification · repayment source, guarantee and collateral tolerance · equipment quotes · workspace costs · trip frequency · owner contribution · target amount · first customer segment.

## 6. Owner decisions (2026-10-08)
- **Network:** approved for read-only WebSearch/WebFetch on official sponsor sources.
  - Third-party pages are leads only.
  - No logins or forms. No paid scrapers.
  - Used in Phase 2. Phase 1 may also check URLs (GitHub, portfolio, Coursera verify) as evidence that the links resolve, not proof of the claims.
- **Git:** local `git init` in Phase 1, before any other writes.
  - No remote, no push.
  - Commits only at gates, with the owner's OK.
  - Verify `.env_sam-gov.json` is ignored (`git check-ignore`) before the first commit.
- **Approval scope:** Phase 1 only, then stop at Gate 1.
- **Execution precondition:** the owner exits bypass mode and configures project-scoped `/permissions` with a deny rule for `.env*`.

## 7. Out of scope / prohibited
- Submissions, emails, calls, purchases, paid services or memberships, scheduling, cron enablement.
- Login scraping. Reading the secret file. Edits outside this project.
- Award probabilities.
