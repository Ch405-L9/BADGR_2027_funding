"""CSV import/export of the tracker, the starter seed file, and curated research findings."""
import csv
import io
import json
from pathlib import Path

from badgr_funding import applicant as applicant_mod
from badgr_funding import csv_safe, db, dates, dedupe, money, scoring, status

INT_COLUMNS = {"amount_min_cents", "amount_max_cents", "min_months_in_business",
               "term_months", "effort_hours", "override_score"}
EXPORT_COLUMNS = ["id", *db.EDITABLE]
COMPUTED_COLUMNS = ["score_total", "score_parts", "eligibility_rollup", "ready_to_submit", "blockers"]

SEED_NOTE_PREFIX = "Imported from research/seed_opportunities.csv"
SEED_TYPE_MAP = {"grant": "grant", "loan": "loan", "loan_support": "loan_support",
                 "workspace_support": "workspace", "advisory": "advisory", "R&D": "rd"}


def _read_rows(path):
    text = Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return list(csv.DictReader(io.StringIO(text)))


def _coerce(col, raw):
    raw = csv_safe.unescape(raw) if col not in INT_COLUMNS else raw
    if raw == "":
        return None
    if col in INT_COLUMNS:
        return int(raw)
    return raw


def export_tracker(conn, path, appl=None, ref=None):
    appl = appl or applicant_mod.load()
    rows = []
    for opp in db.all_opportunities(conn):
        crit = db.criteria(conn, opp["id"])
        sc = scoring.score(opp, crit, appl, ref)
        blk = status.blockers(opp, crit, appl, ref)
        row = {c: (opp[c] if c in INT_COLUMNS else csv_safe.escape(opp[c])) for c in EXPORT_COLUMNS}
        row.update(score_total=sc["total"],
                   score_parts=csv_safe.escape(";".join(f"{k}={v[0]}" for k, v in sc["parts"].items())),
                   eligibility_rollup=sc["eligibility"],
                   ready_to_submit=("n/a-service" if opp["funding_type"] in scoring.IN_KIND_TYPES
                                    else ("yes" if not blk else "no")),
                   blockers=csv_safe.escape(" | ".join(blk)))
        rows.append(row)
    rows.sort(key=lambda r: r["id"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=EXPORT_COLUMNS + COMPUTED_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return len(rows)


def import_tracker(conn, path, reason="CSV import"):
    results = []
    for raw in _read_rows(path):
        fields = {c: _coerce(c, raw.get(c, "")) for c in db.EDITABLE if c in raw}
        results.append(dedupe.upsert(conn, raw["id"], fields, reason))
    return results


def import_seed(conn, path):
    """Import the starter seed CSV. All rows stay UNVERIFIED_CURRENT / eligibility unknown."""
    results = []
    for r in _read_rows(path):
        fields = {
            "sponsor": r["program"], "program": r["program"],
            "funding_type": SEED_TYPE_MAP[r["funding_type"]],
            "official_url": r["official_url"] or None,
            "source_status": "UNVERIFIED_CURRENT", "eligibility": "unknown",
            "next_action": r["next_action"] or None,
            "notes": SEED_NOTE_PREFIX + " (2026-10-07 seed; not freshly checked)",
        }
        results.append(dedupe.upsert(conn, r["id"], fields, "seed import"))
    return results


def load_findings(conn, path):
    """Load curated research findings JSON: opportunities with criteria and sources."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    results = []
    for item in data["opportunities"]:
        fields = {k: v for k, v in item.items() if k in db.EDITABLE}
        current = db.get(conn, item["id"])
        fresh = item.get("source_status", "UNVERIFIED_CURRENT") != "UNVERIFIED_CURRENT"
        if fresh and "notes" not in item and current and (current["notes"] or "").startswith(SEED_NOTE_PREFIX):
            fields["notes"] = f"Seed row re-checked against official source {(item.get('source_checked_at') or '')[:10]}"
        for key in ("amount_min", "amount_max"):
            if key in item:
                fields[f"{key}_cents"] = money.to_cents(item[key])
        outcome, opp_id = dedupe.upsert(conn, item["id"], fields, item.get("reason", "research findings"))
        for c in item.get("criteria", []):
            db.set_criterion(conn, opp_id, c["criterion"], c.get("status", "unknown"), c.get("material", True),
                             c.get("evidence"), c.get("private_key"), c.get("pass_when"))
        for s in item.get("sources", []):
            db.add_source(conn, opp_id, s["url"], s["kind"], s["method"], s.get("excerpt"),
                          s.get("checked_at"), s.get("tz", dates.LOCAL_TZ_NAME))
        rolled = status.rolled_eligibility(db.criteria(conn, opp_id))
        db.update(conn, opp_id, {"eligibility": rolled}, "eligibility roll-up from criteria")
        results.append((outcome, opp_id))
    return results


def export_logs(conn, history_path, sources_path):
    """Write durable, tracked copies of change history and source checks (DB is gitignored)."""
    for path, query in ((history_path, "SELECT opportunity_id, field, old_value, new_value, changed_at, reason FROM history ORDER BY id"),
                        (sources_path, "SELECT opportunity_id, url, kind, method, checked_at, checked_tz, excerpt FROM sources ORDER BY opportunity_id, checked_at, url")):
        rows = conn.execute(query).fetchall()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(rows[0].keys() if rows else [])
            for r in rows:
                vals = list(r)
                if "field" in r.keys() and str(r["field"]).endswith("_cents"):
                    for i in (2, 3):  # old_value, new_value as dollars, not bare digit runs
                        vals[i] = None if vals[i] is None else money.fmt(int(vals[i]))
                w.writerow([csv_safe.escape(v) for v in vals])
    return True
