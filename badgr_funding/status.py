"""Eligibility roll-up and ready-to-submit gate. Both fail closed on unknowns."""
from badgr_funding import dates

OPEN_STATUSES = {"VERIFIED_OPEN", "ROLLING_CONFIRMED"}
MAX_SOURCE_AGE_DAYS = 30


ARCHIVE_STATUSES = {"VERIFIED_CLOSED", "DISCONTINUED", "CHANGED", "UNREACHABLE"}


def resolve_private(criteria_rows, screening):
    """Return criteria with private keys resolved from the owner's private screening answers.

    Used only for the private view. Tracked exports keep these rows 'unknown'.
    """
    out = []
    for c in criteria_rows:
        c = dict(c)
        key = c.get("private_key")
        if key and screening.get(key) is not None:
            passed = str(bool(screening[key])).lower() == c["pass_when"]
            c["status"] = "yes" if passed else "no"
            c["evidence"] = "owner-screened (private)"
        out.append(c)
    return out


def archive_reason(opp, criteria_rows):
    """Why a row is not actionable now (closed, changed, owner-declined), or None."""
    if opp["source_status"] in ARCHIVE_STATUSES:
        return f"source {opp['source_status']}"
    if opp["next_action"] and opp["next_action"].lower().startswith("parked"):
        return "parked by owner"
    return None


def rolled_eligibility(criteria_rows):
    """'no' if any material criterion is no; 'yes' only if all material criteria are yes."""
    material = [c for c in criteria_rows if c["material"]]
    if not material:
        return "unknown"
    if any(c["status"] == "no" for c in material):
        return "no"
    if all(c["status"] == "yes" for c in material):
        return "yes"
    return "unknown"


def blockers(opp, criteria_rows, applicant, ref=None):
    """Return the reasons this opportunity is NOT ready to submit. Empty list = ready."""
    ref = ref or dates.today()
    out = []
    if opp["source_status"] not in OPEN_STATUSES:
        out.append(f"source status {opp['source_status']} (needs VERIFIED_OPEN or ROLLING_CONFIRMED)")
    if dates.is_stale(opp["source_checked_at"], MAX_SOURCE_AGE_DAYS, ref):
        out.append(f"source not checked within {MAX_SOURCE_AGE_DAYS} days")
    elig = rolled_eligibility(criteria_rows)
    if elig != "yes":
        unknown = [c["criterion"] for c in criteria_rows if c["material"] and c["status"] != "yes"]
        out.append("eligibility " + elig + (f": {', '.join(unknown)}" if unknown else ": no criteria recorded"))
    tier = opp["prerequisite_tier"]
    if tier == "UNKNOWN":
        out.append("prerequisites unknown")
    if tier in ("SAM_ACTIVE", "GRANTS_GOV_ROLE") and not applicant.sam_active:
        out.append("SAM registration not Active")
    if tier == "GRANTS_GOV_ROLE":
        out.append("Grants.gov roles not verified")
    if tier == "CERTIFICATION_REQUIRED" and not applicant.third_party_certs:
        out.append("required certification not held")
    gate = dates.history_gate_date(applicant.formation_date, opp["min_months_in_business"])
    if gate and ref < gate:
        out.append(f"business history below {opp['min_months_in_business']} months until {gate.isoformat()}")
    if opp["deadline_date"]:
        left = dates.days_until(opp["deadline_date"], ref)
        if left is not None and left < 0:
            out.append("deadline passed")
    elif opp["rolling"] != "yes" and opp["funding_type"] not in ("advisory", "lever", "workspace"):
        out.append("deadline unknown (not confirmed rolling)")
    if opp["funding_type"] in ("loan", "loan_support", "property") and not opp["repayment_gate"]:
        out.append("repayment analysis not done")
    return out


def is_ready(opp, criteria_rows, applicant, ref=None):
    return not blockers(opp, criteria_rows, applicant, ref)
