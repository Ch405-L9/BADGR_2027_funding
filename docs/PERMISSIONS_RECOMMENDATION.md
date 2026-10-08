# Claude Code permissions — recommendation (not applied)
Checked against the official docs on 2026-10-08: https://code.claude.com/docs/en/permissions

You apply this yourself (`/permissions`, or edit `.claude/settings.local.json` in this project). Written instructions are not permissions, and I did not change your settings.

## Suggested deny rules (project-anchored with a leading `/`)
```json
{
  "permissions": {
    "deny": [
      "Read(/.env*)",
      "Read(/.env_2025_tax/**)",
      "Read(/private/**)",
      "Read(/badgr_legal/**)",
      "Read(/college_xscripts/**)",
      "Read(/exports/private/**)",
      "Read(/backups/private/**)"
    ]
  }
}
```
What the docs say about these rules:
- **Deny wins.** Rules are evaluated deny, then ask, then allow, and an allow rule can't carve an exception out of a deny.
- **A `Read` deny also blocks Edit and Write** on the same path. It also blocks Bash file commands Claude Code recognizes (`cat`, `head`, `tail`, `sed`, `tee`) and redirections.
- **Leading `/`** anchors at the settings source (this project). `//` would be an absolute filesystem path.
- **Use `.claude/settings.local.json`** (personal, not committed) rather than `.claude/settings.json` (shared).

## Limits
- **Python scripts aren't blocked.** Deny rules don't stop a script from reading these folders, so the project's own tools (`cli agenda`, `cli finance`, `cli backup`) keep working.
- **Stronger isolation needs sandboxing.** For filesystem enforcement that doesn't depend on command text, see https://code.claude.com/docs/en/sandboxing.
- **Future sessions:** with these rules in place, Claude can't open new private documents you drop in (receipts, statements). Move them into the project root for a one-off review, or temporarily relax a rule.
- **Never use bypass-permissions mode** (CLAUDE.md).

## Missing inputs
- Your decision to apply, and which folders to include.
