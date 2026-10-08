"""Loan math in integer cents with Decimal. Scenario tool only; lender disclosures govern."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("1")


def _round(x):
    return int(Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP))


def payment(principal_cents, annual_rate, months):
    """Level monthly payment (cents). annual_rate as Decimal fraction, e.g. Decimal('0.0775')."""
    if months <= 0:
        raise ValueError("months must be positive")
    p = Decimal(principal_cents)
    r = Decimal(annual_rate) / 12
    if r == 0:
        return _round(p / months)
    return _round(p * r / (1 - (1 + r) ** -months))


def schedule(principal_cents, annual_rate, months):
    """Amortization rows. The final payment absorbs rounding so the balance ends at exactly 0."""
    pay = payment(principal_cents, annual_rate, months)
    r = Decimal(annual_rate) / 12
    balance = principal_cents
    rows = []
    for m in range(1, months + 1):
        interest = _round(Decimal(balance) * r)
        principal = pay - interest
        if m == months or principal > balance:
            principal = balance
        balance -= principal
        rows.append({"month": m, "payment": principal + interest, "interest": interest,
                     "principal": principal, "balance": balance})
    return rows


def summary(principal_cents, annual_rate, months, upfront_fees_cents=0):
    rows = schedule(principal_cents, annual_rate, months)
    interest = sum(r["interest"] for r in rows)
    return {
        "principal": principal_cents,
        "monthly_payment": rows[0]["payment"],
        "months": months,
        "total_interest": interest,
        "upfront_fees": upfront_fees_cents,
        "total_cost_of_credit": interest + upfront_fees_cents,
        "total_repaid": sum(r["payment"] for r in rows),
        "net_proceeds": principal_cents - upfront_fees_cents,
        "approx_apr": approx_apr(principal_cents - upfront_fees_cents, [r["payment"] for r in rows]),
    }


def approx_apr(net_proceeds_cents, payments_cents):
    """Approximate APR: monthly IRR x 12, by bisection. Labelled approximate; not a Reg Z APR."""
    if net_proceeds_cents <= 0 or not payments_cents:
        return None
    if sum(payments_cents) <= net_proceeds_cents:
        return Decimal("0")

    def pv(rate):
        return sum(Decimal(p) / (1 + rate) ** (i + 1) for i, p in enumerate(payments_cents))

    lo, hi = Decimal("0"), Decimal("1")
    for _ in range(80):
        mid = (lo + hi) / 2
        if pv(mid) > net_proceeds_cents:
            lo = mid
        else:
            hi = mid
    return ((lo + hi) / 2 * 12).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
