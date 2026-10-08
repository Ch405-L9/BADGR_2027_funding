"""Upsert with deduplication by sponsor|program|cycle. Never deletes; changes go to history."""
from badgr_funding import db, dates


def find_match(conn, sponsor, program, cycle):
    """Return (match_id, flag). flag='cycle_conflict' when one cycle is null and the other set."""
    key = db.dedupe_key(sponsor, program, cycle)
    row = conn.execute("SELECT id FROM opportunities WHERE dedupe_key = ?", (key,)).fetchone()
    if row:
        return row["id"], None
    prefix = key.rsplit("|", 1)[0] + "|"
    for r in conn.execute("SELECT id, cycle FROM opportunities WHERE dedupe_key LIKE ?", (prefix + "%",)):
        if (r["cycle"] is None) != (cycle is None):
            return None, ("cycle_conflict", r["id"])
    return None, None


def upsert(conn, opp_id, fields, reason):
    """Insert or merge. Returns ('inserted'|'updated'|'unchanged'|'flagged', id)."""
    match, flag = find_match(conn, fields.get("sponsor"), fields.get("program"), fields.get("cycle"))
    if match is None and db.get(conn, opp_id) is not None:
        match = opp_id  # same id, cycle or name edited: treat as update
    if match:
        changed = db.update(conn, match, fields, reason)
        return ("updated" if changed else "unchanged"), match
    db.insert(conn, opp_id, {**fields, "_reason": reason})
    if flag:
        kind, other = flag
        with conn:
            conn.execute("INSERT INTO review_flags (opportunity_id, other_id, flag, created_at) VALUES (?, ?, ?, ?)",
                         (opp_id, other, kind, dates.now_iso()))
        return "flagged", opp_id
    return "inserted", opp_id
