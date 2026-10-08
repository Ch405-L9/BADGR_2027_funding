# Priority scoring
Updated 2026-10-08. Code: `badgr_funding/scoring.py`. Tests: `tests/test_tracker.py::ScoringTests`.

**The score is a prioritization aid. It is never a probability or likelihood of award.** It answers: "Given what we know today, where should the owner spend the next hour?"

| Component | Points | Rule |
|---|---|---|
| value | 0–25 | Published maximum (or minimum if no max): <$1k 5, $1k–5k 10, $5k–25k 15, $25k–100k 20, ≥$100k 25. Free services (advisory, workspace, contracting, levers) are fixed at 15. Unknown amount scores 0 |
| fit | 0–25 | 25 × (material criteria answered **yes**) ÷ (material criteria). Unknown earns 0. No criteria recorded scores 0 |
| readiness | 0–25 | Prerequisite tier: NONE 25, UEI_ONLY 20, SAM_ACTIVE 10 (20 once SAM is Active), GRANTS_GOV_ROLE 8, HISTORY_MIN 5 before the gate date and 20 after, COLLATERAL_REPAYMENT 5, CERTIFICATION_REQUIRED 3, UNKNOWN 0 |
| effort | 0–15 | Estimated prep hours: ≤2 15, ≤8 12, ≤20 8, ≤40 4, more 1. Unknown scores 0 |
| cost_risk | 0–10 | Non-debt 10, minus 2 for fees. Debt starts at 5, minus 2 for collateral, 1 for a personal guarantee, 1 for fees |

## Rules
- A material criterion answered **no** puts a row under "INELIGIBLE NOW". Those rows are listed but not ranked.
- **Owner override:** `update ID --set override_score=N override_reason="..." --reason "..."`. The database rejects an override without a reason. Rank output marks overridden scores with `*` and keeps the computed score.
- History gates (e.g. 24 months in business) are computed from `business_profile.json` formation date, so scores change automatically on the gate date (2027-01-20).
- Ready-to-submit is separate from score and fails closed (`badgr_funding/status.py`). It needs:
  - fresh source (≤30 days) that is VERIFIED_OPEN or ROLLING_CONFIRMED
  - all material criteria yes
  - prerequisites met
  - a known deadline, or rolling confirmed
  - a repayment analysis for any debt

## Known limitations
- **Value uses the published maximum.** Large programs (SBA 7(a) $5M) earn full value points even when the realistic amount for this business is far smaller. Readiness and cost_risk temper this. Once the owner sets a target amount, value can be re-banded.
- **Effort hours are planning estimates,** not measurements.
- **Eligibility evidence comes from WebFetch summaries,** not raw page text. Confirm with the sponsor before submission.
