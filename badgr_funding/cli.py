"""Command-line interface. Local only: no network, no submissions, no messages."""
import argparse
import sys

from badgr_funding import applicant as applicant_mod
from badgr_funding import csvio, db, dates, money, scoring, status

TYPE_GROUPS = [
    ("Grants & prizes", {"grant", "prize"}),
    ("Loans & credit support", {"loan", "loan_support"}),
    ("Advisory & no-cost services", {"advisory"}),
    ("Workspace", {"workspace"}),
    ("Equipment", {"equipment"}),
    ("Transport", {"transport"}),
    ("Property", {"property"}),
    ("R&D (SBIR/STTR-type)", {"rd"}),
    ("Contracting readiness", {"contracting"}),
    ("Odds-improvement levers", {"lever"}),
]


def _conn(args):
    conn = db.connect(args.db)
    db.migrate(conn)
    return conn


def cmd_init(args):
    conn = db.connect(args.db)
    applied = db.migrate(conn)
    print(f"database {args.db}: applied {applied or 'nothing (up to date)'}")


def cmd_import_seed(args):
    for outcome, oid in csvio.import_seed(_conn(args), args.path):
        print(f"{outcome:9} {oid}")


def cmd_load_findings(args):
    for outcome, oid in csvio.load_findings(_conn(args), args.path):
        print(f"{outcome:9} {oid}")


def cmd_import(args):
    for outcome, oid in csvio.import_tracker(_conn(args), args.path, args.reason):
        print(f"{outcome:9} {oid}")


def cmd_export(args):
    conn = _conn(args)
    n = csvio.export_tracker(conn, args.path)
    csvio.export_logs(conn, "tracking/history.csv", "tracking/source_checks.csv")
    print(f"exported {n} rows to {args.path}; history and source checks to tracking/")


def cmd_add(args):
    conn = _conn(args)
    fields = dict(kv.split("=", 1) for kv in args.set or [])
    fields.update(sponsor=args.sponsor, program=args.program, funding_type=args.type, cycle=args.cycle)
    db.insert(conn, args.id, {**_typed(fields), "_reason": args.reason})
    print(f"added {args.id}")


def cmd_update(args):
    conn = _conn(args)
    fields = _typed(dict(kv.split("=", 1) for kv in args.set))
    if ("override_score" in fields) and fields["override_score"] is not None and not fields.get("override_reason"):
        current = db.get(conn, args.id) or {}
        if not current.get("override_reason"):
            sys.exit("override_score requires override_reason")
    changed = db.update(conn, args.id, fields, args.reason)
    print(f"updated {args.id}: {sorted(changed) or 'no changes'}")


def cmd_check_source(args):
    conn = _conn(args)
    db.add_source(conn, args.id, args.url, args.kind, args.method, args.excerpt)
    db.update(conn, args.id, {"source_status": args.status, "source_checked_at": dates.now_iso(),
                              "source_checked_tz": dates.LOCAL_TZ_NAME}, f"source check: {args.method}")
    print(f"recorded source check for {args.id}: {args.status}")


def cmd_list(args):
    conn = _conn(args)
    for o in db.all_opportunities(conn):
        if args.type and o["funding_type"] != args.type:
            continue
        if args.tier and o["prerequisite_tier"] != args.tier:
            continue
        if args.status and o["source_status"] != args.status:
            continue
        print(f"{o['id']:28} {o['funding_type']:12} {o['prerequisite_tier']:22} {o['source_status']:18} "
              f"{o['eligibility']:8} {o['program']}")


def cmd_rank(args):
    conn = _conn(args)
    appl = applicant_mod.load(args.profile)
    screening = applicant_mod.load_screening() if args.private else {}
    rows, archived = [], []
    for o in db.all_opportunities(conn):
        crit = status.resolve_private(db.criteria(conn, o["id"]), screening)
        reason = status.archive_reason(o, crit)
        if reason:
            archived.append((o, reason))
            continue
        rows.append((o, scoring.score(o, crit, appl), status.blockers(o, crit, appl)))
    if args.private:
        print("# PRIVATE VIEW — includes owner screening answers. Do not save in tracked files.\n")
    print(f"# Priority ranking — {dates.today().isoformat()} (prioritization only; not odds of award)\n")
    for title, types in TYPE_GROUPS:
        group = [r for r in rows if r[0]["funding_type"] in types]
        if not group:
            continue
        print(f"## {title}")
        for o, sc, blk in sorted(group, key=lambda r: (-r[1]["ranked"], -r[1]["total"], r[0]["id"])):
            tag = "INELIGIBLE NOW" if not sc["ranked"] else f"{sc['total']:3d}{'*' if sc['override'] else ' '}"
            amount = ("in-kind service" if o["funding_type"] in scoring.IN_KIND_TYPES and o["amount_max_cents"] is None
                      else money.range_text(o["amount_min_cents"], o["amount_max_cents"]))
            print(f"- [{tag}] {o['program']} ({o['sponsor']}) — {amount}; "
                  f"tier {o['prerequisite_tier']}; source {o['source_status']}; eligibility {sc['eligibility']}")
            if args.verbose:
                print("    parts: " + ", ".join(f"{k} {v[0]} ({v[1]})" for k, v in sc["parts"].items()))
                print(f"    deadline: {dates.deadline_display(o['deadline_date'], o['deadline_time'], o['deadline_tz'], o['rolling'])}")
                print(f"    not ready: {'; '.join(blk) if blk else 'none'}")
                if o["next_action"]:
                    print(f"    next: {o['next_action']}")
        print()
    if archived:
        print("## Archived / not actionable (kept for history; not deleted)")
        for o, reason in sorted(archived, key=lambda r: r[0]["id"]):
            print(f"- {o['program']} ({o['sponsor']}) — {reason}. {o['next_action'] or ''}".rstrip())
        print()


def cmd_finance(args):
    from badgr_funding import finance_report
    for path in finance_report.generate():
        print(f"wrote {path}")


def cmd_plan(args):
    from badgr_funding import planner
    data = planner.load_tasks()
    start = dates.parse_date(args.start) if args.start else dates.today()
    statuses, holidays = planner.load_status(), planner.load_holidays()
    sam = applicant_mod.load().sam_active
    daily = planner.schedule(data, start, 30, statuses, holidays, sam)
    weeks, leftover = planner.weekly(data, start, 13, statuses, holidays, sam)
    from pathlib import Path
    Path("planning/plan_30_day.md").write_text(planner.render_daily(data, daily), encoding="utf-8")
    Path("planning/plan_90_weekly.md").write_text(planner.render_weekly(data, weeks, leftover), encoding="utf-8")
    print(f"wrote planning/plan_30_day.md and planning/plan_90_weekly.md (start {start})")


def cmd_agenda(args):
    from badgr_funding import planner
    ref = dates.parse_date(args.date) if args.date else dates.today()
    sec = planner.agenda(_conn(args), planner.load_tasks(), ref, args.days)
    print(f"# Agenda — {ref.isoformat()} (America/New_York). Local report only; nothing is sent or submitted.\n")
    for title, items in sec.items():
        print(f"## {title}")
        print("\n".join(f"- {i}" for i in items) if items else "- none")
        print()


def cmd_task(args):
    from badgr_funding import planner
    ids = {t["id"] for t in planner.load_tasks()["tasks"]}
    if args.id not in ids:
        sys.exit(f"unknown task id {args.id}")
    planner.set_status(args.id, args.action, args.evidence)
    print(f"task {args.id}: {args.action}")


def cmd_backup(args):
    from badgr_funding import backup
    archive, manifest = backup.create()
    print(f"backup written: {archive} ({len(manifest['files'])} files; private, gitignored)")


def cmd_restore_test(args):
    import tempfile
    from pathlib import Path
    from badgr_funding import backup
    archives = sorted(Path("backups/private").glob("badgr_backup_*.zip"))
    if not archives:
        sys.exit("no backups found; run `backup` first")
    with tempfile.TemporaryDirectory() as tmp:
        report = backup.restore_test(archives[-1], tmp)
    print(f"restore test of {archives[-1].name}: {report}")
    if not report["ok"]:
        sys.exit(1)


def cmd_export_packet(args):
    from badgr_funding import export
    pkt, archive, files = export.build()
    missing = export.completeness(pkt)
    print(f"packet: {pkt} ({len(files)} files); archive: {archive}; missing: {missing or 'none'}")


def cmd_reports(args):
    from pathlib import Path
    from badgr_funding import reports
    Path("docs/SOURCE_REGISTER.md").write_text(reports.source_register(), encoding="utf-8")
    Path("docs/MISSING_INPUTS.md").write_text(reports.missing_inputs(), encoding="utf-8")
    print("wrote docs/SOURCE_REGISTER.md and docs/MISSING_INPUTS.md")


def cmd_calendar(args):
    from badgr_funding import ics
    path, n = ics.write(start=dates.parse_date(args.start) if args.start else None)
    print(f"wrote {path} ({n} events)")


def cmd_history(args):
    for h in db.history(_conn(args), args.id):
        print(f"{h['changed_at']} {h['field']}: {h['old_value']!r} -> {h['new_value']!r} ({h['reason']})")


def cmd_show(args):
    conn = _conn(args)
    o = db.get(conn, args.id)
    if not o:
        sys.exit(f"unknown id {args.id}")
    for k, v in o.items():
        if v is not None:
            print(f"{k}: {v}")
    print("criteria:")
    for c in db.criteria(conn, args.id):
        print(f"  [{c['status']}] {'*' if c['material'] else ' '} {c['criterion']} — {c['evidence'] or ''}")
    print("sources:")
    for s in db.sources(conn, args.id):
        print(f"  {s['checked_at']} {s['kind']} {s['url']} ({s['method']})")


def _typed(fields):
    out = {}
    for k, v in fields.items():
        if v in ("", None):
            out[k] = None
        elif k in csvio.INT_COLUMNS:
            out[k] = int(v)
        else:
            out[k] = v
    return out


def build_parser():
    p = argparse.ArgumentParser(prog="python3 -m badgr_funding.cli", description=__doc__)
    p.add_argument("--db", default=str(db.DEFAULT_DB))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    s = sub.add_parser("import-seed"); s.add_argument("path", nargs="?", default="research/seed_opportunities.csv"); s.set_defaults(func=cmd_import_seed)
    s = sub.add_parser("load-findings"); s.add_argument("path"); s.set_defaults(func=cmd_load_findings)
    s = sub.add_parser("import"); s.add_argument("path"); s.add_argument("--reason", default="CSV import"); s.set_defaults(func=cmd_import)
    s = sub.add_parser("export"); s.add_argument("path", nargs="?", default="tracking/opportunity_tracker.csv"); s.set_defaults(func=cmd_export)
    s = sub.add_parser("add"); s.add_argument("id"); s.add_argument("--sponsor", required=True); s.add_argument("--program", required=True)
    s.add_argument("--type", required=True); s.add_argument("--cycle"); s.add_argument("--set", nargs="*"); s.add_argument("--reason", default="manual add"); s.set_defaults(func=cmd_add)
    s = sub.add_parser("update"); s.add_argument("id"); s.add_argument("--set", nargs="+", required=True); s.add_argument("--reason", required=True); s.set_defaults(func=cmd_update)
    s = sub.add_parser("check-source"); s.add_argument("id"); s.add_argument("--url", required=True); s.add_argument("--status", required=True)
    s.add_argument("--kind", default="official", choices=["official", "lead"]); s.add_argument("--method", default="manual check"); s.add_argument("--excerpt"); s.set_defaults(func=cmd_check_source)
    s = sub.add_parser("list"); s.add_argument("--type"); s.add_argument("--tier"); s.add_argument("--status"); s.set_defaults(func=cmd_list)
    s = sub.add_parser("rank"); s.add_argument("--profile", default=str(applicant_mod.PROFILE_PATH)); s.add_argument("-v", "--verbose", action="store_true")
    s.add_argument("--private", action="store_true", help="resolve private screening answers (terminal only)"); s.set_defaults(func=cmd_rank)
    s = sub.add_parser("history"); s.add_argument("id"); s.set_defaults(func=cmd_history)
    sub.add_parser("finance", help="loan scenarios, schedules, cash flow, repayment analysis").set_defaults(func=cmd_finance)
    s = sub.add_parser("plan", help="write 30-day daily and 90-day weekly plans"); s.add_argument("--start"); s.set_defaults(func=cmd_plan)
    s = sub.add_parser("agenda", help="today's agenda (local report only)"); s.add_argument("--date"); s.add_argument("--days", type=int, default=14); s.set_defaults(func=cmd_agenda)
    sub.add_parser("backup", help="private backup to backups/private/").set_defaults(func=cmd_backup)
    sub.add_parser("restore-test", help="verify the latest backup in a temp dir").set_defaults(func=cmd_restore_test)
    sub.add_parser("export-packet", help="sanitized shareable packet in exports/public/").set_defaults(func=cmd_export_packet)
    sub.add_parser("reports", help="source register and missing-input report").set_defaults(func=cmd_reports)
    s = sub.add_parser("calendar", help="write planning/badgr_funding_calendar.ics"); s.add_argument("--start"); s.set_defaults(func=cmd_calendar)
    s = sub.add_parser("task", help="mark a planning task done/skipped/todo"); s.add_argument("action", choices=["done", "skipped", "todo"])
    s.add_argument("id"); s.add_argument("--evidence", default=""); s.set_defaults(func=cmd_task)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(func=cmd_show)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
