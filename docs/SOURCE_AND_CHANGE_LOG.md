# Source and transformation record
Inputs: secret_sam-gov_cu_ci_badgr_a.grant_business_info.json; 04_Anthony_Grant_Resume_09-30-2026-3.pdf; 04_Anthony_Grant_conf-mstr-file_09-30-2026-2.txt; 04_Anthony_Grant_BASE_Cover-Letter_09-30-2026.txt; user Oct 7 SAM text and screenshot interpretation.
Original business file mixed invalid JSON, branding, credentials, hardware and SAM extracts. Replaced with valid funding-specific JSON plus Markdown; originals not overwritten.
Preserved corrected UEI and current pending status; expiration set unknown. Formation January 20 overrides older conversational dates. Full address, credentials, bank/TIN details and contact identifiers omitted. Legal identity and receipts conflicts flagged, not resolved. Employment/certificate/project claims sourced from applicant documents, not independently verified. Excluded job-authorization placeholders and broad 100%-accuracy cover-letter phrasing.
Seed URLs are research starting points, not open/eligible assertions. All financial actuals remain unknown pending reconciliation.

## 2026-10-08 — Phase 1 changes
- Original credential-bearing file renamed by owner to `.env_sam-gov.json` (gitignored via `.env*`). Not read by Claude.
- business_profile.json: added missing `evidence` field to BADGR Bolt project ("Resume/master profile; independent artifact review required") so every project carries provenance. No factual values changed.
- Added business_profile.schema.json, claims_ledger.csv, discrepancies.md, url_checks.csv and DRAFT positioning documents.
- C-PROJ-05 (24 deployments) downgraded to APPLICANT_REPORTED and excluded from drafts: the GitHub API shows 1 github-pages deployment (2026-07-30) on the public badgr_bolt repo.
- Capability statement: removed the C.Walts metric (repo not public) and corrected 'Meta-certified coursework' to 'Meta course certificates via Coursera'.
- Founder bio: removed assumed pronouns (owner's pronouns not stated); certificate wording corrected.

## 2026-10-08 — Gate 1 follow-up (owner: "Brandon Anthony Grant or w/e it says on my licenses. Check badgr_legal")
- badgr_legal/ found in project; gitignored; scanner skips it. Read text of: GA Articles of Organization (2 copies), 2026 Annual Registration, Initial Resolutions, Operating Agreement. Not read: EIN/CP575 letters, bank statement, BOI report, other files.
- Verified entity name/type/effective date 01/20/2025 from GA filing copy (C-BIZ-01/02).
- GA documents name "Brandon Grant"; no government ID in folder; signing name stays owner-directed pending ID match.
- ownership_percentage set to 100 from single-member operating agreement (C-OWN-04, PARTIAL: signature/date not detected).

## 2026-10-08 — IRS transcripts (owner authorized use of .env_2025_tax/)
- Extracted filing status and income totals with masking; personal income detail kept in gitignored private/tax_2025_summary.md. Scratch text deleted.
- 2025_revenue_verified = 5550 (Schedule C gross receipts); tax_filing_status recorded; owner's 'waived' statement superseded.
- New claims C-FIN-02, C-FIN-03; discrepancies D3 updated, D16, D17 added.

## 2026-10-08 — College transcript (owner-supplied college_xscripts/, gitignored)
- Education corrected from transcript: AAS Computer & Information Sciences (Personal Computer Management), 12 credits, GPA 3.00; UoPhoenix transfer 2009. Resume 'systems security focus' wording superseded. Founder bio updated. Personal identifiers not recorded; scratch renders deleted.

## 2026-10-08 — Phase 2
- Tracker engine, 20 researched rows (official sources fetched 2026-10-08; times approximate), ranked shortlist, scoring/search/queue docs.
- Privacy correction: personal tax specifics removed from D16 and tax_filing_status in working files ; Amended to ce22401 (owner-approved 2026-10-08), reflog expired, gc --prune=now; search of all git objects for the specifics returned 0 matches..
- Verizon: added LISC administrator source, follow-up date 2026-10-22, account criterion.
- Phase 2 committed as 89354a8. Owner screening answers stored in private/screening.json; Q3 (PayPal vs. bankruptcy/liens/convictions) ambiguous, left unknown.

## 2026-10-08 — Phase 3
- Program-rule claims C-PRG-01..11 (official pages checked 2026-10-08); C-FIN-04 (unexplained $25).
- Assumptions register finance/assumptions.csv; lint accepts A- IDs and covers drafts/outreach.
- Kiva sensitive criteria now private_key-based (migration 0002); tracked files show 'owner-screened (private)'.
