"""Generate finance/ outputs from templates/financial_inputs.csv and documented scenarios.

Business figures only. Personal income (private/) is never read here.
Missing inputs produce explicit 'blocked' outputs, never zeros.
"""
import csv
from decimal import Decimal
from pathlib import Path

from badgr_funding import cashflow, dates, loans, money

TEMPLATE_PATH = Path("templates/financial_inputs.csv")          # tracked, stays blank
PRIVATE_INPUTS_PATH = Path("private/financial_inputs.csv")      # gitignored; real figures go here
OUT = Path("finance")                                           # tracked: scenario math + status only
PRIVATE_OUT = Path("exports/private")                           # gitignored: anything with real balances
DATE_FIELDS = {"2026_ytd_through"}

# (id, label, principal $, annual rate, months, upfront fees cents fn, assumption id, availability note)
SCENARIOS = [
    ("kiva_5k_24", "Kiva $5,000 / 24 mo / 0%", 5_000, Decimal("0"), 24, lambda p: 0, "A-FIN-02", "Available now if screening passes"),
    ("kiva_10k_36", "Kiva $10,000 / 36 mo / 0%", 10_000, Decimal("0"), 36, lambda p: 0, "A-FIN-03", "Available now if screening passes"),
    ("ace_15k_60", "ACE $15,000 / 60 mo / 7.75% + $100 + 3%", 15_000, Decimal("0.0775"), 60,
     lambda p: 10_000 + int(Decimal(p) * Decimal("0.03")), "A-FIN-04", "Not before 2027-01-20 (2-year rule)"),
]

INPUT_MAP = {  # financial_inputs.csv field -> CashFlowInputs attribute
    "cash_on_hand": "opening_cash",
    "monthly_business_expenses": "monthly_operating_expenses",
    "existing_debt_payments": "existing_debt_payments",
}


def default_inputs_path():
    return PRIVATE_INPUTS_PATH if PRIVATE_INPUTS_PATH.exists() else TEMPLATE_PATH


def read_inputs(path):
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            value = row["value"].strip()
            if not value:
                out[row["field"]] = None
            elif row["field"] in DATE_FIELDS:
                out[row["field"]] = dates.parse_date(value)
            else:
                out[row["field"]] = money.to_cents(value)
    return out


def cashflow_inputs(raw):
    kw = {attr: raw.get(field) for field, attr in INPUT_MAP.items()}
    # YTD revenue is averaged over the months it actually covers (through the end of the
    # month in 2026_ytd_through), never over "months elapsed today".
    ytd, through = raw.get("2026_ytd_revenue"), raw.get("2026_ytd_through")
    kw["monthly_operating_revenue"] = (ytd // through.month) if (ytd is not None and through) else None
    owner = raw.get("owner_contribution")
    kw["owner_contribution"] = {1: owner} if owner else {}
    return cashflow.CashFlowInputs(**kw)


def _write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def generate(out_dir=OUT, inputs_path=None, private_dir=PRIVATE_OUT, ref=None):
    """Write scenario math and status to out_dir (tracked); write real balances only to private_dir."""
    out_dir, private_dir = Path(out_dir), Path(private_dir)
    today = (ref or dates.today()).isoformat()
    raw = read_inputs(inputs_path or default_inputs_path())
    written = []

    # Loan scenarios and schedules
    comparison = []
    for sid, label, dollars, rate, months, fee_fn, aid, avail in SCENARIOS:
        p = dollars * 100
        s = loans.summary(p, rate, months, fee_fn(p))
        rows = loans.schedule(p, rate, months)
        path = out_dir / f"debt_schedule_{sid}.csv"
        _write_csv(path, ["month", "payment", "interest", "principal", "balance"],
                   [[r["month"], money.fmt(r["payment"]), money.fmt(r["interest"]), money.fmt(r["principal"]), money.fmt(r["balance"])] for r in rows])
        written.append(path)
        comparison.append([sid, label, money.fmt(s["principal"]), f"{rate * 100:.2f}%", months, money.fmt(s["monthly_payment"]),
                           money.fmt(s["total_interest"]), money.fmt(s["upfront_fees"]), money.fmt(s["total_cost_of_credit"]),
                           money.fmt(s["net_proceeds"]), f"~{s['approx_apr'] * 100:.2f}%", avail, aid])
    path = out_dir / "loan_offer_comparison.csv"
    _write_csv(path, ["scenario", "label", "principal", "stated_rate", "months", "monthly_payment", "total_interest",
                      "upfront_fees", "total_cost_of_credit", "net_proceeds", "approx_apr", "availability", "assumption"], comparison)
    written.append(path)

    # Cash flow (base / downside). Real balances never go to the tracked directory.
    inp = cashflow_inputs(raw)
    if raw.get("2026_ytd_revenue") is not None and raw.get("2026_ytd_through") is None:
        inp.monthly_operating_revenue = None
    for name, factor in (("base", 1.0), ("downside", 0.5)):
        res = cashflow.project(inp, 12, factor)
        path = out_dir / f"cashflow_12mo_{name}.csv"
        if isinstance(res, cashflow.Blocked):
            _write_csv(path, ["status", "missing_inputs", "generated"], [["BLOCKED", ";".join(res.missing), today]])
        else:
            private_path = private_dir / f"cashflow_12mo_{name}.csv"
            keys = list(res[0])
            _write_csv(private_path, keys, [[money.fmt(r[k]) if k != "month" else r[k] for k in keys] for r in res])
            written.append(private_path)
            _write_csv(path, ["status", "location", "generated"], [["COMPUTED_PRIVATELY", str(private_path), today]])
        written.append(path)

    # Repayment analysis
    lines = [f"# DRAFT — Repayment analysis", f"Generated {today} by `python3 -m badgr_funding.cli finance`. Scenario tool only; lender disclosures govern.", ""]
    base = cashflow.project(inp, 12, 1.0)
    if isinstance(base, cashflow.Blocked):
        lines += ["## Status: BLOCKED",
                  f"Affordability cannot be assessed. Missing: {', '.join(base.missing)}.",
                  f"No ratios or 'affordable' conclusions are produced until these are entered in `{PRIVATE_INPUTS_PATH}` (gitignored) with evidence.", ""]
    else:
        lines += ["## Status: computed privately",
                  f"Affordability with real figures is in `{private_dir / 'repayment_analysis_private.md'}` (gitignored).", ""]
        monthly_net = inp.monthly_operating_revenue - inp.monthly_operating_expenses - inp.existing_debt_payments
        plines = ["# PRIVATE — Repayment affordability (real figures; never commit or export)", f"Generated {today}.", "",
                  f"Monthly net operating cash (base): {money.fmt(monthly_net)}", ""]
        for sc in SCENARIOS:
            pay = loans.payment(sc[2] * 100, sc[3], sc[4])
            res = cashflow.affordability(monthly_net, pay)
            plines.append(f"- {sc[1]}: payment {money.fmt(pay)}; coverage {res['dscr']} (reference 1.25, A-FIN-06)")
        ppath = private_dir / "repayment_analysis_private.md"
        ppath.parent.mkdir(parents=True, exist_ok=True)
        ppath.write_text("\n".join(plines) + "\n", encoding="utf-8")
        written.append(ppath)
    lines += ["## Scenario payments (computed)", "| Scenario | Monthly payment | Total cost of credit | Approx. APR | Availability |", "|---|---|---|---|---|"]
    lines += [f"| {c[1]} | {c[5]} | {c[8]} | {c[10]} | {c[11]} |" for c in comparison]
    lines += ["", "## What each payment would need",
              "Using a debt-service coverage of 1.25 (common reference point, A-FIN-06), the business would need monthly net operating cash of at least:"]
    for c, sc in zip(comparison, SCENARIOS):
        pay = loans.payment(sc[2] * 100, sc[3], sc[4])
        lines.append(f"- {c[1]}: {money.fmt(int(pay * 125 // 100))} per month")
    lines += ["", "2025 Schedule C showed a net loss (C-FIN-02), so repayment depends on 2026 operating results.", "",
              "## Missing inputs", f"- Real figures in `{PRIVATE_INPUTS_PATH}`: cash_on_hand, monthly_business_expenses, existing_debt_payments, 2026_ytd_revenue, 2026_ytd_through."]
    path = out_dir / "repayment_analysis.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(path)

    # 3-year projection template (assumption-driven; blank values)
    path = out_dir / "projection_3yr_template.csv"
    _write_csv(path, ["line", "year_1", "year_2", "year_3", "assumption_or_evidence"], [
        ["operating_revenue", "", "", "", "owner to set from pipeline; 2025 actual $5,550 (C-FIN-02)"],
        ["cost_of_services", "", "", "", "owner input"],
        ["software_and_hosting", "", "", "", "owner input"],
        ["equipment_capex", "", "", "", "quotes in finance/equipment_quote_register.csv (A-EQ-01)"],
        ["workspace", "", "", "", "quotes needed (A-WS-01)"],
        ["vehicle_and_travel", "", "", "", "trip log needed (A-TR-01)"],
        ["debt_service", "", "", "", "from chosen loan scenario (finance/loan_offer_comparison.csv)"],
        ["owner_contribution", "", "", "", "owner input"],
        ["grants_awarded", "", "", "", "awarded only; pending awards excluded"],
    ])
    written.append(path)
    return written
