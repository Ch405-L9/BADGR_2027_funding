"""Source register and missing-input report, generated from tracked files only."""
import csv
import re
from pathlib import Path

from badgr_funding import dates


def source_register(root=Path(".")):
    root = Path(root)
    lines = ["# Source register — DRAFT", f"Generated {dates.today().isoformat()} by `python3 -m badgr_funding.cli reports`. Official = sponsor/agency page; lead = third-party, not relied on for eligibility.", ""]
    lines += ["## Funding program sources (tracking/source_checks.csv)", "| Opportunity | Kind | URL | Checked | Method |", "|---|---|---|---|---|"]
    with open(root / "tracking/source_checks.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lines.append(f"| {r['opportunity_id']} | {r['kind']} | {r['url']} | {r['checked_at'][:16]} | {r['method']} |")
    lines += ["", "## Profile link checks (context/url_checks.csv)", "| URL | Result | Checked |", "|---|---|---|"]
    with open(root / "context/url_checks.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lines.append(f"| {r['url']} | {r['result']} | {r['checked_at'] or 'not checked'} |")
    lines += ["", "## Missing inputs", "- Re-check any source older than 30 days before applying (`cli agenda`)."]
    return "\n".join(lines) + "\n"


def missing_inputs(root=Path(".")):
    root = Path(root)
    items = {}
    for path in sorted([*(root / "drafts").glob("*.md"), *(root / "drafts/outreach").glob("*.md")]):
        section = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                section = line[3:].strip().lower()
                continue
            if section == "missing inputs" and line.strip().startswith("- "):
                items.setdefault(re.sub(r"\s+", " ", line.strip()[2:]), []).append(path.relative_to(root).as_posix())
    open_d = []
    for line in (root / "context/discrepancies.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (D\d+) \| (.+?) \|", line)
        if m and "RESOLVED" not in m.group(2):
            open_d.append(f"{m.group(1)}: {m.group(2)[:140]}")
    lines = ["# Missing-input report — DRAFT", f"Generated {dates.today().isoformat()} by `python3 -m badgr_funding.cli reports`.", "",
             "## Open discrepancies (context/discrepancies.md)", *[f"- {d}" for d in open_d], "",
             "## Inputs requested by drafts (deduplicated)"]
    for item, srcs in sorted(items.items()):
        lines.append(f"- {item} — in {', '.join(sorted(set(srcs)))}")
    lines += ["", "## Missing inputs", "- This report itself lists them; resolve and regenerate."]
    return "\n".join(lines) + "\n"
