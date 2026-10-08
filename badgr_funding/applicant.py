"""Applicant facts derived from context/business_profile.json for screening and ranking.

Only business facts are loaded. Personal income detail lives in private/ and is
never read here. Unknown attributes (e.g. gender, veteran status) stay None so
restricted programs screen as 'unknown', never inferred.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from badgr_funding import dates

PROFILE_PATH = Path("context/business_profile.json")
SCREENING_PATH = Path("private/screening.json")


@dataclass
class Applicant:
    state: str
    county: str
    city: str
    naics: list
    entity_type: str
    formation_date: object
    sam_active: bool
    uei: str
    receipts_2025_cents: object
    net_2025_cents: object
    ownership_pct: object
    ownership_verified: bool
    self_cert_sdb: bool
    minority_owned_reported: bool
    third_party_certs: list = field(default_factory=list)
    gender: object = None
    veteran: object = None
    cautions: list = field(default_factory=list)

    def months_in_business(self, ref=None):
        return dates.months_between(self.formation_date, ref or dates.today())


def load(path=PROFILE_PATH):
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    biz, reg, own, fin, des = p["business"], p["registration"], p["owner"], p["financials"], p["designations"]
    sched = fin.get("2025_schedule_c") or {}
    reported = des.get("reported", [])
    return Applicant(
        state=biz["operating_location"]["state"],
        county=biz["operating_location"]["county"],
        city=biz["operating_location"]["city"],
        naics=[biz["primary_naics"], *biz.get("additional_naics", [])],
        entity_type=biz["entity_type"],
        formation_date=dates.parse_date(biz["formation_date"]),
        sam_active=reg.get("status", "").lower() == "active",
        uei=reg["uei"],
        receipts_2025_cents=None if fin.get("2025_revenue_verified") is None else int(fin["2025_revenue_verified"] * 100),
        net_2025_cents=None if sched.get("net_profit_or_loss") is None else int(sched["net_profit_or_loss"] * 100),
        ownership_pct=own.get("ownership_percentage"),
        ownership_verified=False,  # C-OWN-04 PARTIAL until a signed copy is confirmed
        self_cert_sdb=any("Small Disadvantaged" in r for r in reported),
        minority_owned_reported=any("Minority" in r or "Black" in r for r in reported),
        third_party_certs=[],
        cautions=["D16: tax follow-up pending before lender/federal review (details in private/tax_2025_summary.md)"],
    )


def load_screening(path=SCREENING_PATH):
    """Owner's private screening answers; {} if absent. Never copied into tracked files."""
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
