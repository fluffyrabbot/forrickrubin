#!/usr/bin/env python3
"""Regenerate data.json from git logs in ../apps sibling repos."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT.parent


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def tagline_for(path: Path) -> str:
    for name in ("README.md", "readme.md", "docs/README.md", "THESIS.md"):
        candidate = path / name
        if not candidate.is_file():
            continue
        with candidate.open() as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith(("[!", ">")):
                    continue
                if stripped.startswith("# "):
                    return stripped[2:][:200]
                return stripped[:200]
    return ""


def main() -> None:
    repos = []
    for entry in sorted(APPS.iterdir()):
        if entry.name == "forrickrubin" or not (entry / ".git").is_dir():
            continue

        total = int(git(entry, "rev-list", "--count", "HEAD") or 0)
        if total == 0:
            continue

        shortlog = git(entry, "shortlog", "-sn", "--all")
        top = shortlog.split("\n")[0].strip() if shortlog else ""
        yours = sum(
            int(line.split()[0])
            for line in shortlog.split("\n")
            if "fluffyrabbot" in line or "fluffy rabbit" in line
        )
        yours_pct = round(yours / total * 100, 1) if total else 0.0
        top_author = top.split(None, 1)[-1] if top else ""
        is_fork = top_author not in ("fluffyrabbot", "fluffy rabbit") and yours_pct < 50

        first = git(entry, "log", "--reverse", "--format=%ai").split("\n")[0][:10]
        last = git(entry, "log", "-1", "--format=%ai")[:10]
        c7 = len([line for line in git(entry, "log", "--since=7 days ago", "--oneline").split("\n") if line])
        c30 = len([line for line in git(entry, "log", "--since=30 days ago", "--oneline").split("\n") if line])

        days = 1
        if first and last:
            try:
                start = datetime.strptime(first, "%Y-%m-%d")
                end = datetime.strptime(last, "%Y-%m-%d")
                days = max(1, (end - start).days + 1)
            except ValueError:
                pass

        origin = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=entry,
            capture_output=True,
            text=True,
        ).stdout.strip()

        repos.append(
            {
                "slug": entry.name,
                "commits": total,
                "yours_pct": yours_pct,
                "is_fork": is_fork,
                "first": first,
                "last": last,
                "days": days,
                "velocity": round(total / days, 1),
                "c7": c7,
                "c30": c30,
                "origin": origin or None,
                "tagline": tagline_for(entry),
                "top_author": top_author,
            }
        )

    owned = [repo for repo in repos if not repo["is_fork"]]
    forks = [repo for repo in repos if repo["is_fork"]]
    owned.sort(key=lambda repo: (-repo["c30"], -repo["commits"]))

    payload = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "owned_repos": len(owned),
            "total_repos": len(repos),
            "fork_repos": len(forks),
            "total_commits": sum(repo["commits"] for repo in owned),
            "commits_30d": sum(repo["c30"] for repo in owned),
            "commits_7d": sum(repo["c7"] for repo in owned),
        },
        "featured": {
            "flagship": ["mesh", "rexxy", "stricttutor"],
            "creative": [
                "therightquestions",
                "rabbotchan",
                "manicanim",
                "psychosismv",
                "agencyagency",
            ],
            "burst": ["fmarch", "collablab", "travelami", "reluctocracy", "simcivics"],
            "systems": ["caloreceipt", "altcs", "llmepistemics", "mnesoma", "browserbox"],
        },
        "highlights": {
            "therightquestions": {
                "burst": "35 commits in 4 days",
                "detail": "YouTube studio: research → script → voice → publish. Multiple episodes shipped June 2026.",
            },
            "fmarch": {
                "burst": "21 commits in 4 days",
                "detail": "Forum-mafia platform Phase 0→4: event-sourced Rust, Postgres projections, CBOR/WebSocket.",
            },
            "collablab": {
                "burst": "11 commits in 1 day",
                "detail": "E2EE infinite canvas: tldraw + Loro CRDT + TreeKEM + postern cover traffic.",
            },
            "travelami": {
                "burst": "18 commits in 3 days",
                "detail": "Deployable medical travel card app — questionnaire to print, Netlify-ready.",
            },
            "mesh": {
                "burst": "557 commits in 30 days",
                "detail": "1,466 crates, 993 RFCs. E2EE event store & protocol synthesis monorepo.",
            },
            "rexxy": {
                "burst": "525 commits in 92 days",
                "detail": "22-crate P2P stack: blind signaling, Kademlia, NAT traversal, TreeKEM.",
            },
            "stricttutor": {
                "burst": "136 commits in 30 days",
                "detail": "Studio-grade ed-tech with parallel agent execution playbooks and release gates.",
            },
            "rabbotchan": {
                "burst": "186 commits",
                "detail": "LLM video pipeline with per-segment C2PA provenance.",
            },
            "manicanim": {
                "burst": "38 commits in 4 days",
                "detail": "Typography animation DSL built for human+agent co-editing.",
            },
        },
        "owned": owned,
        "forks": forks,
    }

    output = ROOT / "data.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {output} ({len(owned)} owned repos)")


if __name__ == "__main__":
    main()