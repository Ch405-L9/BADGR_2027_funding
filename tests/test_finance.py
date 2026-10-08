import unittest
from decimal import Decimal

from badgr_funding import cashflow, loans

RATE = Decimal("0.0775")


def closed_form(p, annual, n):
    r = annual / 12
    return p * r / (1 - (1 + r) ** -n)


class LoanTests(unittest.TestCase):
    def test_zero_rate_is_straight_division(self):
        self.assertEqual(loans.payment(500_000, Decimal("0"), 24), 20_833)
        rows = loans.schedule(500_000, Decimal("0"), 24)
        self.assertEqual(sum(r["principal"] for r in rows), 500_000)
        self.assertEqual(rows[-1]["balance"], 0)
        self.assertEqual(sum(r["interest"] for r in rows), 0)

    def test_payment_matches_closed_form(self):
        expected = closed_form(Decimal(1_500_000), RATE, 60)
        self.assertLessEqual(abs(loans.payment(1_500_000, RATE, 60) - expected), 1)

    def test_schedule_invariants(self):
        for p, n in ((1_500_000, 60), (5_000_000, 60), (1_234_567, 37)):
            rows = loans.schedule(p, RATE, n)
            self.assertEqual(len(rows), n)
            self.assertEqual(rows[-1]["balance"], 0)
            self.assertEqual(sum(r["principal"] for r in rows), p)
            self.assertTrue(all(r["balance"] >= 0 for r in rows))
            self.assertTrue(all(abs(r["payment"] - rows[0]["payment"]) <= 100 for r in rows))

    def test_interest_decreases(self):
        rows = loans.schedule(1_500_000, RATE, 60)
        self.assertTrue(all(a["interest"] >= b["interest"] for a, b in zip(rows, rows[1:])))

    def test_fees_raise_effective_cost(self):
        no_fee = loans.summary(1_500_000, RATE, 60)
        with_fee = loans.summary(1_500_000, RATE, 60, upfront_fees_cents=10_000 + 45_000)
        self.assertEqual(with_fee["total_cost_of_credit"] - no_fee["total_cost_of_credit"], 55_000)
        self.assertGreater(with_fee["approx_apr"], no_fee["approx_apr"])
        self.assertLess(abs(no_fee["approx_apr"] - RATE), Decimal("0.0005"))

    def test_zero_rate_apr_is_zero(self):
        self.assertEqual(loans.summary(500_000, Decimal("0"), 24)["approx_apr"], Decimal("0"))

    def test_invalid_term(self):
        with self.assertRaises(ValueError):
            loans.payment(1000, RATE, 0)


class CashFlowTests(unittest.TestCase):
    def base(self, **over):
        kw = dict(opening_cash=100_000, monthly_operating_revenue=200_000, monthly_operating_expenses=150_000,
                  existing_debt_payments=0)
        kw.update(over)
        return cashflow.CashFlowInputs(**kw)

    def test_missing_inputs_block(self):
        out = cashflow.project(cashflow.CashFlowInputs())
        self.assertIsInstance(out, cashflow.Blocked)
        self.assertEqual(set(out.missing), {"opening_cash", "monthly_operating_revenue", "monthly_operating_expenses",
                                            "existing_debt_payments"})  # unreported debt is unknown, not zero

    def test_unknown_existing_debt_blocks(self):
        out = cashflow.project(self.base(existing_debt_payments=None))
        self.assertIn("existing_debt_payments", out.missing)

    def test_zero_is_not_missing(self):
        self.assertIsInstance(cashflow.project(self.base(monthly_operating_revenue=0)), list)

    def test_sources_separate_and_pending_not_cash(self):
        rows = cashflow.project(self.base(grant_awarded={2: 1_000_000}, grant_pending={3: 500_000},
                                          owner_contribution={1: 50_000}, debt_proceeds={4: 1_500_000}))
        self.assertEqual(rows[0]["owner_contribution"], 50_000)
        self.assertEqual(rows[1]["grant_awarded"], 1_000_000)
        self.assertEqual(rows[2]["pending_awards_not_counted"], 500_000)
        self.assertEqual(rows[3]["debt_proceeds"], 1_500_000)
        expected = 100_000 + 12 * 50_000 + 1_000_000 + 50_000 + 1_500_000
        self.assertEqual(rows[-1]["ending_cash"], expected)

    def test_downside_lower(self):
        base = cashflow.project(self.base())[-1]["ending_cash"]
        down = cashflow.project(self.base(), revenue_factor=0.5)[-1]["ending_cash"]
        self.assertLess(down, base)

    def test_new_debt_payment_starts_on_month(self):
        rows = cashflow.project(self.base(new_debt_payment=30_000, new_debt_start_month=3))
        self.assertEqual([r["debt_service"] for r in rows[:4]], [0, 0, 30_000, 30_000])

    def test_affordability_blocks_without_cash_flow(self):
        self.assertIsInstance(cashflow.affordability(None, 30_000), cashflow.Blocked)
        res = cashflow.affordability(45_000, 30_000)
        self.assertEqual(res["dscr"], Decimal("1.50"))
        self.assertTrue(res["meets_benchmark"])
        self.assertFalse(cashflow.affordability(30_000, 30_000)["meets_benchmark"])

    def test_double_funding(self):
        lines = [{"item": "Laptop", "source": "verizon", "cents": 1}, {"item": "laptop ", "source": "kiva", "cents": 1},
                 {"item": "Hosting", "source": "kiva", "cents": 1}]
        self.assertEqual(cashflow.double_funding(lines), ["laptop"])

    def test_reimbursement_gap(self):
        self.assertIsInstance(cashflow.reimbursement_gap(500_000, None, 2), cashflow.Blocked)
        self.assertFalse(cashflow.reimbursement_gap(500_000, 300_000, 2)["fundable"])
        self.assertTrue(cashflow.reimbursement_gap(500_000, 900_000, 2, -100_000)["fundable"])


if __name__ == "__main__":
    unittest.main()
