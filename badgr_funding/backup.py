"""Private backup and verified restore. Archives go to backups/private/ (gitignored).

A backup contains a consistent SQLite copy (sqlite3 backup API), the private/
folder and planning/task_status.csv, plus a SHA-256 manifest. Restore extracts to
a separate directory and verifies every hash and the database integrity; it
never overwrites the live files.
"""
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from badgr_funding import dates

BACKUP_DIR = Path("backups/private")
INCLUDE_DIRS = ("private",)
INCLUDE_FILES = ("planning/task_status.csv",)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def create(root=Path("."), db_path=Path("data/funding.sqlite"), out_dir=BACKUP_DIR, stamp=None):
    root, out_dir = Path(root), Path(root) / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or dates.now().strftime("%Y%m%dT%H%M%S")
    archive = out_dir / f"badgr_backup_{stamp}.zip"
    manifest = {"created": dates.now_iso(), "files": {}}
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        db_file = root / db_path
        if db_file.exists():
            snap = Path(tmp) / "funding.sqlite"
            src, dst = sqlite3.connect(str(db_file)), sqlite3.connect(str(snap))
            with dst:
                src.backup(dst)
            src.close(); dst.close()
            z.write(snap, "data/funding.sqlite")
            manifest["files"]["data/funding.sqlite"] = _sha(snap)
        for d in INCLUDE_DIRS:
            for p in sorted((root / d).rglob("*")):
                if p.is_file():
                    rel = p.relative_to(root).as_posix()
                    z.write(p, rel)
                    manifest["files"][rel] = _sha(p)
        for f in INCLUDE_FILES:
            p = root / f
            if p.exists():
                z.write(p, f)
                manifest["files"][f] = _sha(p)
        z.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
    return archive, manifest


def restore_test(archive, target):
    """Extract to target and verify hashes + SQLite integrity. Returns a report dict."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"unsafe path in archive: {name}")
        z.extractall(target)
    manifest = json.loads((target / "MANIFEST.json").read_text())
    bad = [rel for rel, digest in manifest["files"].items() if _sha(target / rel) != digest]
    report = {"files": len(manifest["files"]), "hash_mismatches": bad, "db_integrity": None, "db_rows": None}
    db = target / "data/funding.sqlite"
    if db.exists():
        conn = sqlite3.connect(str(db))
        report["db_integrity"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
        report["db_rows"] = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                             for t in ("opportunities", "criteria", "sources", "history")}
        conn.close()
    report["ok"] = not bad and report["db_integrity"] in (None, "ok")
    return report
