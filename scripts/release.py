#!/usr/bin/env python3
"""Freeze the current site into /versions/<id>/ and record it in versions.json.

Workflow:
  1. Edit the live site at the repo root (index.html, css/, js/, data.json) so it
     reflects the new version. Make sure <body data-version="vN"> matches the id.
  2. python3 scripts/release.py vN "Short label describing what changed"

The script copies the root snapshot into /versions/vN/ (a frozen, self-contained
copy) and appends the entry to versions.json. The revision bar on every page reads
the live /versions.json, so older snapshots automatically gain links to newer ones.
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "versions.json"
VERSIONS_DIR = ROOT / "versions"

# Files/dirs that make up a frozen, self-contained snapshot.
SNAPSHOT_ITEMS = ["index.html", "css", "js", "data.json"]


def load_manifest() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text())
    return {"current": None, "versions": []}


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def snapshot(version_id: str) -> None:
    target = VERSIONS_DIR / version_id
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for item in SNAPSHOT_ITEMS:
        src = ROOT / item
        if not src.exists():
            continue
        dst = target / item
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: release.py <version-id> [label]")

    version_id = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else ""

    manifest = load_manifest()
    existing = {v["id"]: v for v in manifest["versions"]}

    entry = {
        "id": version_id,
        "path": f"/versions/{version_id}/",
        "released": existing.get(version_id, {}).get("released") or iso_now(),
        "label": label or existing.get(version_id, {}).get("label", ""),
    }

    snapshot(version_id)

    manifest["versions"] = [v for v in manifest["versions"] if v["id"] != version_id]
    manifest["versions"].append(entry)
    manifest["current"] = version_id
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"Froze {version_id} -> versions/{version_id}/  ({entry['released']})")


if __name__ == "__main__":
    main()
