# Privacy controls — DRAFT
Updated 2026-10-08 (America/New_York).

## Data classes
| Class | Where it may live | In git? |
|---|---|---|
| Sanitized context (profile, claims, drafts) | `context/`, `drafts/`, `docs/` | Yes (local repo, no remote) |
| Private working data (SQLite DB, private exports, backups) | `data/`, `exports/private/`, `backups/private/`, `private/`, `inputs/private/` | No (gitignored) |
| Credential-bearing original source | Must not be in project; currently `.env_sam-gov.json` in root | No (gitignored by `.env*`) |
| Never stored | Passwords, full TIN/EIN/SSN, bank account/routing numbers, card numbers, full home address, personal phone/email | — |

## Controls in place
0. Real financial inputs live in `private/financial_inputs.csv`; any output with real balances goes to `exports/private/`. Tracked `finance/` holds only scenario math and BLOCKED/COMPUTED_PRIVATELY status (tested). Owner screening answers live in `private/screening.json` and are applied only by `rank --private` in the terminal.
1. `.gitignore` covers `.env*`, `secret_*`, `*secret*`, `data/`, `*.sqlite*`, `*.db`, private export/backup folders. `git check-ignore` confirmed `.env_sam-gov.json` is ignored on 2026-10-08.
2. **`.gitignore` is not access control.** It does not stop Claude Code tools or other programs from reading a file. The owner should add a Claude Code `/permissions` deny rule for reading `.env*`, or move that file outside the project. Confirm the exact rule syntax with the official docs: https://code.claude.com/docs/en/permissions
3. `badgr_funding/redact.py` never opens files matching `.env*`, `*secret*`, `*.sqlite*`, `*.db`, or anything under `data/`, `backups/`, `.git/`. A unit test (`test_env_and_secret_files_are_never_opened`) verifies this.
4. Drafts store city/county/state/ZIP only. The schema rejects extra location fields such as a street address.
5. The git repository is local only: no remote, no push.
6. Network use (approved 2026-10-08) is read-only fetches of public pages. No logins, form submissions or paid scrapers.

## Redaction scanner
Run: `python3 -m badgr_funding.redact .` (exit code 1 if anything is found; values are masked in output).

It detects EIN-like, SSN-like, 9–17 digit account/routing-like numbers, card-like numbers, password / API-key / token assignments, private-key headers, GitHub/AWS/`sk-` tokens, email addresses and US phone numbers.

CSV cells in `*_cents` columns (integer money) are skipped to avoid false account-number matches; every other cell is scanned.

Public office contacts (SBDC Gwinnett, ATDC, APEX, VITA, Gwinnett Entrepreneur Center), taken from official pages, are allowlisted in `redact.py`. No personal contacts are allowlisted.

**Limitations:**
- Regex heuristics only.
- Misses secrets in PDFs, images, encoded or compressed data, and unusual formats.
- Can flag harmless long numbers.
- Does not scan skipped files by design.
- A clean result is not proof that no sensitive data exists.
- Human review is still required before any export or sharing.

## Sharing and backups (Phase 5)
- `cli export-packet` builds `exports/public/badgr_packet_<date>/` (+ zip) from an allowlist of drafts. It strips claim tags, internal notes, discrepancy references and repository paths, then refuses to build if secret-like patterns, tax markers or private paths remain.
- `cli backup` writes `backups/private/` (gitignored), including private/. Keep it off shared drives; it contains your most sensitive files.
- `cli restore-test` verifies the latest backup in a temp folder without touching live files.
- Permissions recommendation: docs/PERMISSIONS_RECOMMENDATION.md.

## Owner actions outstanding
- Add a `/permissions` deny rule for `.env*`, or move `.env_sam-gov.json` outside the project.
- Rotate any credentials that were in the original source (README).
- Never paste passwords or full bank/TIN values into chat. Final application data goes through official secure channels only.
