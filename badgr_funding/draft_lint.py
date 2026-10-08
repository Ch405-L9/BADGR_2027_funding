"""Lint DRAFT documents: header, missing-inputs section, claim citations and banned claims.

Rules:
- First line contains "DRAFT"; preamble contains a YYYY-MM-DD check date.
- A "## Missing inputs" section exists.
- Every content line outside the preamble, "Missing inputs" and "Review notes"
  must cite at least one [C-...] claim ID, and every cited ID must exist in the
  ledger. Exempt lines: headings, blanks, table header and separator rows.
- Content lines must not contain banned affirmative claims (BANNED).
- Scoped claims (SCOPED_CLAIMS) must keep their scope words on the citing line.
- Excluded claims (EXCLUDED_CLAIMS) may not be cited in any draft, and
  BUYER_FACING_EXCLUDED claims may not appear in the listed documents.
"""
import csv
import re
import sys
from pathlib import Path

CITE = re.compile(r"\[([CA]-[A-Z]+-\d{2})\]")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}")
EXEMPT_SECTIONS = {"missing inputs", "review notes"}

BANNED = {
    "percent_accuracy_claim": re.compile(
        r"(\b100\s*%|\bone hundred percent\b)\s*(accura|correct|precis|reliab|success|uptime|effective|guarantee)"
        r"|(accura\w*|correct\w*|precis\w*|reliab\w*|success\w*|uptime)\W+(of\W+)?100\s*%", re.I),
    "8a_certified_claim": re.compile(r"\b8\(a\)[- ](certified|participant|firm)\b", re.I),
    "mbe_certified_claim": re.compile(r"\bcertified (MBE|minority business enterprise)\b", re.I),
    "hubzone_certified_claim": re.compile(r"\bHUBZone[- ]certified\b", re.I),
    "award_guarantee": re.compile(r"\bguarantee(d|s)?\b.*\b(award|fund|grant|loan)", re.I),
    "customer_claim": re.compile(r"\b(our|existing|current) (customers|clients) (include|are)\b", re.I),
    "revenue_claim": re.compile(r"\b(annual|monthly) revenue of\b", re.I),
}

# claim id -> list of (description, regex) that must all match the citing line
SCOPED_CLAIMS = {
    "C-PROJ-02": [
        ("'controlled'", re.compile(r"\bcontrolled\b", re.I)),
        ("test date", re.compile(r"2026-08-12|August 12, 2026")),
    ],
}
# Claims not supported by evidence; not reusable in drafts until the owner supplies proof.
EXCLUDED_CLAIMS = {"C-PROJ-05"}
# Buyer-facing summaries must not lead with metrics nobody can check yet.
BUYER_FACING_EXCLUDED = {"capability_statement.md": {"C-PROJ-02"}}


ASSUMPTIONS_PATH = Path("finance/assumptions.csv")


def disputed_ids(ledger_path):
    with open(ledger_path, newline="", encoding="utf-8") as fh:
        return {row["claim_id"] for row in csv.DictReader(fh) if row["verification_status"] in ("DISPUTED", "SUPERSEDED")}


def load_ledger_ids(ledger_path, assumptions_path=None):
    """Claim IDs from the ledger plus assumption IDs (A-...) from finance/assumptions.csv."""
    with open(ledger_path, newline="", encoding="utf-8") as fh:
        ids = {row["claim_id"] for row in csv.DictReader(fh)}
    apath = Path(assumptions_path) if assumptions_path else Path(ledger_path).parent.parent / ASSUMPTIONS_PATH
    if apath.exists():
        with open(apath, newline="", encoding="utf-8") as fh:
            ids |= {row["assumption_id"] for row in csv.DictReader(fh)}
    return ids


def lint_text(text, ledger_ids, doc_name="", excluded=frozenset()):
    errors = []
    lines = text.splitlines()
    if not lines or "DRAFT" not in lines[0]:
        errors.append("line 1: missing DRAFT marker")
    first_section = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    if not any(DATE.search(l) for l in lines[:first_section]):
        errors.append("preamble: missing YYYY-MM-DD check date")
    if not any(l.strip().lower() == "## missing inputs" for l in lines):
        errors.append("missing '## Missing inputs' section")

    section = None
    for i, line in enumerate(lines):
        n = i + 1
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower() if stripped.startswith("## ") else section
            continue
        if i < first_section or not stripped or section in EXEMPT_SECTIONS:
            continue
        if TABLE_SEP.match(stripped):
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1].strip()):
            continue  # table header row
        for kind, rx in BANNED.items():
            if rx.search(stripped):
                errors.append(f"line {n}: banned claim ({kind})")
        cited = CITE.findall(stripped)
        if not cited:
            errors.append(f"line {n}: no claim citation")
        for cid in cited:
            if cid not in ledger_ids:
                errors.append(f"line {n}: unknown claim id {cid}")
            if cid in EXCLUDED_CLAIMS or cid in excluded:
                errors.append(f"line {n}: excluded claim {cid} cited")
            if cid in BUYER_FACING_EXCLUDED.get(doc_name, ()):
                errors.append(f"line {n}: {cid} not allowed in {doc_name}")
            for desc, rx in SCOPED_CLAIMS.get(cid, ()):
                if not rx.search(stripped):
                    errors.append(f"line {n}: {cid} missing scope ({desc})")
    return errors


def lint_dir(drafts_dir, ledger_path):
    ledger_ids = load_ledger_ids(ledger_path)
    excluded = disputed_ids(ledger_path)
    results = {}
    for path in sorted([*Path(drafts_dir).glob("*.md"), *Path(drafts_dir).glob("outreach/*.md")]):
        name = path.name if path.parent == Path(drafts_dir) else f"{path.parent.name}/{path.name}"
        results[name] = lint_text(path.read_text(encoding="utf-8"), ledger_ids, name, excluded)
    return results


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    drafts_dir = argv[0] if argv else "drafts"
    ledger = argv[1] if len(argv) > 1 else "context/claims_ledger.csv"
    results = lint_dir(drafts_dir, ledger)
    failed = 0
    for name, errs in results.items():
        print(f"{name}: {'OK' if not errs else f'{len(errs)} error(s)'}")
        for e in errs:
            print(f"  {e}")
        failed += bool(errs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
