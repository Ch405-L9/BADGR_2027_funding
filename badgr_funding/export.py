"""Sanitized, shareable packet (exports/public/). Separate from private data by construction.

Only an explicit allowlist of tracked files is copied. Drafts lose citation tags,
'Missing inputs' and 'Review notes' sections. The build fails if the result
contains secret-like patterns, personal tax markers, or private paths.
"""
import re
import shutil
import zipfile
from pathlib import Path

from badgr_funding import dates, redact

PUBLIC_DIR = Path("exports/public")
DRAFTS = [
    "exec_summary.md", "company_overview.md", "capability_statement.md", "service_menu.md", "founder_bio.md",
    "business_plan.md", "marketing_sales_plan.md", "90_day_delivery.md", "use_of_funds_scenarios.md",
    "grant_narrative_short.md", "grant_narrative_standard.md", "grant_narrative_impact.md",
    "rd_concept_retrieval_reliability.md", "rd_concept_routing_validation.md",
]
COPY_AS_IS = ["finance/loan_offer_comparison.csv"]  # shortlist is internal (blockers, cautions)
TAG = re.compile(r"\s*\[[CA]-[A-Z]+-\d{2}\]")
DREF = re.compile(r"\s*\((?:D\d+(?:,\s*)?)+\)")  # internal discrepancy refs like (D6) or (D2, D8)
INTERNAL_SECTIONS = {"missing inputs", "review notes"}
FORBIDDEN = [re.compile(p, re.I) for p in (
    r"private/", r"badgr_legal", r"college_xscripts", r"\.env", r"1099", r"unemployment", r"\bD1[0-9]\b|\bD[1-9]\b",
    r"screening\.json", r"tax_2025_summary", r"owner-screened", r"\b(?:context|drafts|finance|tracking|badgr_funding)/")]


PATH_FIXES = [
    (re.compile(r"\s*Claim IDs (?:in brackets )?refer to context/claims_ledger\.csv\."), ""),
    (re.compile(r"\s*\((?:double-funding )?check in badgr_funding/[a-z_]+\.py\)"), ""),
    (re.compile(r"(?:drafts|finance|tracking|planning|docs)/([A-Za-z0-9_]+)\.(?:md|csv)"),
     lambda m: "the " + m.group(1).replace("_", " ") + " document"),
]


def _humanize_paths(line):
    for rx, repl in PATH_FIXES:
        line = rx.sub(repl, line)
    return line


def sanitize_markdown(text):
    out, skip = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            skip = line[3:].strip().lower() in INTERNAL_SECTIONS
            if skip:
                continue
        if skip:
            continue
        out.append(_humanize_paths(DREF.sub("", TAG.sub("", line))).rstrip())
    return "\n".join(out).rstrip() + "\n"


def problems(text):
    found = [f"{kind}" for _, kind, _ in redact.scan_text(text)]
    found += [rx.pattern for rx in FORBIDDEN if rx.search(text)]
    return found


def build(root=Path("."), out_dir=PUBLIC_DIR, stamp=None):
    root = Path(root)
    stamp = stamp or dates.today().isoformat()
    pkt = root / out_dir / f"badgr_packet_{stamp}"
    if pkt.exists():
        shutil.rmtree(pkt)
    pkt.mkdir(parents=True)
    written, issues = [], {}
    for name in DRAFTS:
        src = root / "drafts" / name
        text = sanitize_markdown(src.read_text(encoding="utf-8"))
        (pkt / name).write_text(text, encoding="utf-8")
        written.append(name)
    for rel in COPY_AS_IS:
        src = root / rel
        if src.exists():
            text = src.read_text(encoding="utf-8")
            if rel.endswith(".md"):
                text = sanitize_markdown(text)
            dest = pkt / Path(rel).name
            dest.write_text(text, encoding="utf-8")
            written.append(dest.name)
    index = ["# BADGR Technologies — advisor review packet (DRAFT)", f"Built {stamp}. All documents are drafts pending owner approval.", "",
             "Intended audience: business advisors (e.g. SBDC, GT APEX) reviewing funding readiness. Not for public posting: it includes 2025 business tax figures.", ""]
    index += [f"- {n}" for n in sorted(written)]
    (pkt / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    written.append("README.md")
    for p in pkt.iterdir():
        found = problems(p.read_text(encoding="utf-8"))
        if found:
            issues[p.name] = found
    if issues:
        shutil.rmtree(pkt)
        raise ValueError(f"packet failed sanitization: {issues}")
    archive = root / out_dir / f"badgr_packet_{stamp}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(written):
            z.write(pkt / n, f"badgr_packet_{stamp}/{n}")
    return pkt, archive, sorted(written)


def completeness(pkt):
    expected = set(DRAFTS) | {Path(r).name for r in COPY_AS_IS} | {"README.md"}
    present = {p.name for p in Path(pkt).iterdir()}
    return sorted(expected - present)
