"""Transparent priority score (0-100). Prioritization only, never a likelihood of award.

Components (see docs/SCORING.md):
  value      0-25  amount band by maximum amount; in-kind services fixed at 15
  fit        0-25  share of material criteria answered 'yes'; unknown earns nothing
  readiness  0-25  prerequisite tier vs. applicant's current state
  effort     0-15  estimated preparation hours (unknown earns nothing)
  cost_risk  0-10  fees, repayment, guarantee and collateral count against
A material 'no' marks the row ineligible; it is listed separately, not ranked.
An owner override replaces the total and must carry a reason.
"""
from badgr_funding import dates, status

IN_KIND_TYPES = {"advisory", "workspace", "lever", "contracting"}
DEBT_TYPES = {"loan", "loan_support", "property"}

VALUE_BANDS = [  # (max amount cents upper bound, points)
    (100_000, 5),        # < $1k
    (500_000, 10),       # $1k-$5k
    (2_500_000, 15),     # $5k-$25k
    (10_000_000, 20),    # $25k-$100k
    (None, 25),          # >= $100k
]
READINESS = {"NONE": 25, "UEI_ONLY": 20, "SAM_ACTIVE": 10, "GRANTS_GOV_ROLE": 8,
             "CERTIFICATION_REQUIRED": 3, "COLLATERAL_REPAYMENT": 5, "UNKNOWN": 0}
EFFORT_BANDS = [(2, 15), (8, 12), (20, 8), (40, 4), (None, 1)]


def value_score(opp):
    if opp["funding_type"] in IN_KIND_TYPES:
        return 15, "in-kind service (fixed)"
    amount = opp["amount_max_cents"] if opp["amount_max_cents"] is not None else opp["amount_min_cents"]
    if amount is None:
        return 0, "amount unknown"
    for bound, pts in VALUE_BANDS:
        if bound is None or amount < bound:
            return pts, "amount band"


def fit_score(criteria_rows):
    material = [c for c in criteria_rows if c["material"]]
    if not material:
        return 0, "no criteria recorded"
    yes = sum(c["status"] == "yes" for c in material)
    return round(25 * yes / len(material)), f"{yes}/{len(material)} material criteria yes"


def readiness_score(opp, applicant, ref=None):
    tier = opp["prerequisite_tier"]
    if tier == "HISTORY_MIN":
        gate = dates.history_gate_date(applicant.formation_date, opp["min_months_in_business"])
        if gate is None:
            return 0, "history rule unknown"
        met = (ref or dates.today()) >= gate
        return (20, "history met") if met else (5, f"history met on {gate.isoformat()}")
    if tier in ("SAM_ACTIVE", "GRANTS_GOV_ROLE") and applicant.sam_active:
        return 20, f"{tier} (SAM active)"
    return READINESS[tier], tier


def effort_score(opp):
    hours = opp["effort_hours"]
    if hours is None:
        return 0, "effort unknown"
    for bound, pts in EFFORT_BANDS:
        if bound is None or hours <= bound:
            return pts, f"~{hours}h"


def cost_risk_score(opp):
    if opp["funding_type"] not in DEBT_TYPES:
        pts = 10 - (2 if opp["fees"] and opp["fees"].strip().lower() not in ("none", "no", "0") else 0)
        return pts, "non-debt"
    pts, why = 5, ["debt"]
    if opp["collateral"] and opp["collateral"].lower() not in ("none", "no"):
        pts -= 2; why.append("collateral")
    if opp["guarantee"] and opp["guarantee"].lower() not in ("none", "no"):
        pts -= 1; why.append("guarantee")
    if opp["fees"] and opp["fees"].strip().lower() not in ("none", "no", "0"):
        pts -= 1; why.append("fees")
    return max(pts, 0), "+".join(why)


def score(opp, criteria_rows, applicant, ref=None):
    parts = {
        "value": value_score(opp),
        "fit": fit_score(criteria_rows),
        "readiness": readiness_score(opp, applicant, ref),
        "effort": effort_score(opp),
        "cost_risk": cost_risk_score(opp),
    }
    computed = sum(p for p, _ in parts.values())
    eligibility = status.rolled_eligibility(criteria_rows)
    total = opp["override_score"] if opp["override_score"] is not None else computed
    return {
        "total": total,
        "computed": computed,
        "override": opp["override_score"] is not None,
        "override_reason": opp["override_reason"],
        "parts": parts,
        "eligibility": eligibility,
        "ranked": eligibility != "no",
    }
