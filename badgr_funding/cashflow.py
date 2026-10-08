"""12-month cash flow, repayment affordability and grant-budget checks.

Rules: missing inputs block results (never treated as zero); cash sources stay
separate (owner contribution, awarded grant cash, pending awards, debt proceeds,
operating revenue); pending awards are never counted as cash.
"""
from dataclasses import dataclass, field

SOURCES = ("owner_contribution", "grant_awarded", "debt_proceeds", "operating_revenue")
REQUIRED = ("opening_cash", "monthly_operating_revenue", "monthly_operating_expenses")


@dataclass
class Blocked:
    missing: list
    reason: str = "missing required inputs"

    def __str__(self):
        return f"blocked: {self.reason}: {', '.join(self.missing)}"


@dataclass
class CashFlowInputs:
    opening_cash: object = None                 # cents
    monthly_operating_revenue: object = None    # cents
    monthly_operating_expenses: object = None   # cents (excludes debt service)
    existing_debt_payments: object = 0          # cents/month; None = unknown -> blocks
    owner_contribution: dict = field(default_factory=dict)   # {month: cents}
    grant_awarded: dict = field(default_factory=dict)        # {month: cents}; awarded only
    grant_pending: dict = field(default_factory=dict)        # tracked, never counted as cash
    debt_proceeds: dict = field(default_factory=dict)        # {month: cents}
    new_debt_payment: object = 0                # cents/month from a loan scenario
    new_debt_start_month: int = 1


def missing_inputs(inp):
    miss = [k for k in REQUIRED if getattr(inp, k) is None]
    if inp.existing_debt_payments is None:
        miss.append("existing_debt_payments")
    return miss


def project(inp, months=12, revenue_factor=1.0):
    """Monthly rows or Blocked. revenue_factor < 1 models a downside case."""
    miss = missing_inputs(inp)
    if miss:
        return Blocked(miss)
    rows, cash = [], inp.opening_cash
    for m in range(1, months + 1):
        revenue = int(inp.monthly_operating_revenue * revenue_factor)
        debt_service = inp.existing_debt_payments + (inp.new_debt_payment if m >= inp.new_debt_start_month else 0)
        inflows = {
            "owner_contribution": inp.owner_contribution.get(m, 0),
            "grant_awarded": inp.grant_awarded.get(m, 0),
            "debt_proceeds": inp.debt_proceeds.get(m, 0),
            "operating_revenue": revenue,
        }
        outflow = inp.monthly_operating_expenses + debt_service
        cash += sum(inflows.values()) - outflow
        rows.append({"month": m, **inflows, "operating_expenses": inp.monthly_operating_expenses,
                     "debt_service": debt_service, "pending_awards_not_counted": inp.grant_pending.get(m, 0),
                     "ending_cash": cash})
    return rows


def affordability(monthly_net_operating_cash_cents, new_payment_cents, benchmark="1.25"):
    """Debt-service coverage = net operating cash / new payment. Blocks when cash flow is unknown.

    The 1.25 benchmark is a common lender reference point, not a rule of any specific lender.
    """
    from decimal import Decimal
    if monthly_net_operating_cash_cents is None:
        return Blocked(["monthly_net_operating_cash"], "repayment capacity unknown")
    if not new_payment_cents:
        return {"dscr": None, "note": "no new payment"}
    dscr = (Decimal(monthly_net_operating_cash_cents) / Decimal(new_payment_cents)).quantize(Decimal("0.01"))
    return {"dscr": dscr, "meets_benchmark": dscr >= Decimal(benchmark), "benchmark": Decimal(benchmark)}


def double_funding(budget_lines):
    """Flag any budget item funded by more than one source. Lines: {'item', 'source', 'cents'}."""
    seen = {}
    for line in budget_lines:
        seen.setdefault(line["item"].strip().lower(), set()).add(line["source"])
    return sorted(item for item, srcs in seen.items() if len(srcs) > 1)


def reimbursement_gap(spend_cents, opening_cash_cents, delay_months, monthly_net_cash_cents=0):
    """For reimbursement-basis awards: can the business front the spend until repaid?"""
    if opening_cash_cents is None or monthly_net_cash_cents is None:
        miss = [n for n, v in (("opening_cash", opening_cash_cents), ("monthly_net_cash", monthly_net_cash_cents)) if v is None]
        return Blocked(miss, "cannot test reimbursement gap")
    low_point = opening_cash_cents - spend_cents + min(0, monthly_net_cash_cents) * delay_months
    return {"low_point": low_point, "fundable": low_point >= 0}
