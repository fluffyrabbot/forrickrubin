#!/usr/bin/env python3
"""Manage versioned releases.

The site is served as a set of self-contained version snapshots under
/versions/<id>/. The repo root holds a tiny redirector (index.html) that always
routes visitors to the *latest* version — so the homepage tracks the newest
release automatically, while every version (including the latest) keeps a stable
permalink at /versions/<id>/.

Each version directory is the editable source for that version. To cut a release:

  1. python3 scripts/release.py vN "Short label"      # scaffolds versions/vN/
     (copies the current latest as a starting point and points the homepage at it)
  2. Edit versions/vN/index.html, css/, js/ as needed.
  3. python3 scripts/generate.py                       # refreshes versions/vN/data.json
  4. Re-run step 1 (idempotent) if you changed the label.

Running release.py with an existing id just refreshes the manifest label and
re-points the root redirector — handy after editing in place.
"""

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "versions.json"
VERSIONS_DIR = ROOT / "versions"
ROOT_INDEX = ROOT / "index.html"
REDIRECTS = ROOT / "_redirects"


def load_manifest() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text())
    return {"current": None, "versions": []}


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def latest_entry(manifest: dict) -> dict | None:
    for entry in manifest["versions"]:
        if entry["id"] == manifest.get("current"):
            return entry
    return manifest["versions"][-1] if manifest["versions"] else None


def scaffold(version_id: str, source: dict | None) -> None:
    """Create versions/<id>/ by copying the current latest version as a start."""
    target = VERSIONS_DIR / version_id
    if target.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    if source:
        src_dir = ROOT / source["path"].strip("/")
        if src_dir.is_dir():
            for item in src_dir.iterdir():
                dst = target / item.name
                if item.is_dir():
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
    index = target / "index.html"
    if index.is_file():
        html = index.read_text()
        html = re.sub(r'data-version="[^"]*"', f'data-version="{version_id}"', html, count=1)
        index.write_text(html)


def write_root_redirect(latest: dict) -> None:
    """Route the homepage to the latest version.

    Primary mechanism is a Cloudflare Pages `_redirects` 302 (server-side, no
    flash, crawler-friendly). The root index.html is a JS/meta-refresh fallback
    for any host that doesn't honor `_redirects`. A 302 (not 301) keeps "latest"
    free to move to a newer version later.
    """
    path = latest["path"] if latest else "/versions/v1/"

    REDIRECTS.write_text(f"/    {path}    302\n")

    ROOT_INDEX.write_text(
        f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>forrickrubin — agentic portfolio</title>
    <meta
      name="description"
      content="A git-log-driven showcase of agentically built repos — E2EE infrastructure, creative production pipelines, and a June 2026 greenfield burst."
    />
    <link rel="canonical" href="{path}" />
    <script>
      // Route to the latest version. Manifest-driven, so the homepage always
      // tracks the newest release; falls back to the path baked in at release.
      (function () {{
        var fallback = "{path}";
        fetch("/versions.json", {{ cache: "no-store" }})
          .then(function (r) {{ return r.json(); }})
          .then(function (m) {{
            var versions = m.versions || [];
            var cur = versions.filter(function (v) {{ return v.id === m.current; }})[0];
            if (!cur) cur = versions[versions.length - 1];
            location.replace(cur && cur.path ? cur.path : fallback);
          }})
          .catch(function () {{ location.replace(fallback); }});
      }})();
    </script>
    <meta http-equiv="refresh" content="2;url={path}" />
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #0b0a0e;
        color: #968fa0;
        font-family: "IBM Plex Mono", ui-monospace, monospace;
      }}
      a {{ color: #d26a93; }}
    </style>
  </head>
  <body>
    <p>Routing to the latest version… <a href="{path}">open it directly →</a></p>
  </body>
</html>
"""
    )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: release.py <version-id> [label]")

    version_id = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else ""

    manifest = load_manifest()
    existing = {v["id"]: v for v in manifest["versions"]}

    # Scaffold a new version directory from the current latest, if needed.
    if version_id not in existing:
        scaffold(version_id, latest_entry(manifest))

    entry = {
        "id": version_id,
        "path": f"/versions/{version_id}/",
        "released": existing.get(version_id, {}).get("released") or iso_now(),
        "label": label or existing.get(version_id, {}).get("label", ""),
    }

    manifest["versions"] = [v for v in manifest["versions"] if v["id"] != version_id]
    manifest["versions"].append(entry)
    manifest["current"] = version_id
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    write_root_redirect(entry)

    print(f"Released {version_id} ({entry['released']}); homepage routes to {entry['path']}")


if __name__ == "__main__":
    main()
