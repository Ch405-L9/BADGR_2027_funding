# DRAFT — Repayment analysis
Generated 2026-10-08 by `python3 -m badgr_funding.cli finance`. Scenario tool only; lender disclosures govern.

## Status: BLOCKED
Affordability cannot be assessed. Missing: monthly_operating_revenue, existing_debt_payments.
No ratios or 'affordable' conclusions are produced until these are entered in `private/financial_inputs.csv` (gitignored) with evidence.

## Scenario payments (computed)
| Scenario | Monthly payment | Total cost of credit | Approx. APR | Availability |
|---|---|---|---|---|
| Kiva $5,000 / 24 mo / 0% | $208.33 | $0.00 | ~0.00% | Available now if screening passes |
| Kiva $10,000 / 36 mo / 0% | $277.78 | $0.00 | ~0.00% | Available now if screening passes |
| ACE $15,000 / 60 mo / 7.75% + $100 + 3% | $302.35 | $3,691.30 | ~9.34% | Not before 2027-01-20 (2-year rule) |

## What each payment would need
Using a debt-service coverage of 1.25 (common reference point, A-FIN-06), the business would need monthly net operating cash of at least:
- Kiva $5,000 / 24 mo / 0%: $260.41 per month
- Kiva $10,000 / 36 mo / 0%: $347.22 per month
- ACE $15,000 / 60 mo / 7.75% + $100 + 3%: $377.93 per month

2025 Schedule C showed a net loss (C-FIN-02), so repayment depends on 2026 operating results.

## Missing inputs
- Real figures in `private/financial_inputs.csv`: cash_on_hand, monthly_business_expenses, existing_debt_payments, 2026_ytd_revenue, 2026_ytd_through.
