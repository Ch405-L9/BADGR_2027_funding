# Claims policy
Updated 2026-10-08.

Every factual statement in a draft must cite a claim ID from `context/claims_ledger.csv`. Run `python3 -m badgr_funding.draft_lint` to enforce this.

## Verification statuses
| Status | Meaning | May appear in drafts? |
|---|---|---|
| VERIFIED_ISSUER_PAGE | Issuer's own public verification page confirmed on `verified_at` | Yes, with issuer and date |
| VERIFIED_SOURCE_DOC | Read from an official/legal document copy supplied by the owner (e.g. GA filing); not a live registry check | Yes, citing the document |
| VERIFIED_OFFICIAL_PAGE | Program rule read from the sponsor's official page on `verified_at` (summary-derived) | Yes, with the check date; re-verify before applying |
| RESOLVES / RESOLVES_MINIMAL | Link loads; content not evaluated (or only title) | Link only, after owner review |
| PARTIAL | Some elements confirmed, others not | Only the confirmed part |
| APPLICANT_REPORTED | Owner/resume/SAM statement; not independently checked | Yes, as the applicant's statement |
| SELF_CERTIFIED | SAM self-representation | Only as "self-certified"; never as 8(a)/MBE/HUBZone |
| UNVERIFIED_NOT_PUBLIC | Source link checked and not publicly accessible | Description only; no link. Metrics only verbatim with "controlled" and the test date, and never in buyer-facing summaries (capability statement) |
| DISPUTED | Owner or evidence contradicts this record; under review | No. Draft lint blocks any citation |
| SUPERSEDED | Replaced by a later statement or record; kept for history | No. Draft lint blocks any citation |
| PROPOSED | Plan or concept, not an established fact | Clearly labeled as proposed |
| NOT_CHECKED | Not fetched (e.g. behind a login wall) | Owner confirms first |

## Source of truth
`context/claims_ledger.csv` is authoritative for verification status. Older flags elsewhere (e.g. `independent_verification: false` on credentials in business_profile.json) reflect the 2026-10-07 package and are superseded by the ledger.

## Hard rules
- A source statement is not independent verification. Same-model review is not professional verification.
- Controlled-test metrics stay verbatim with their date and scope.
- Deployments are not users. Employer projects are not BADGR revenue.
- Unknown financial values stay null, never zero.
- Changing a claim means editing the ledger row and logging the change in `docs/SOURCE_AND_CHANGE_LOG.md`.
