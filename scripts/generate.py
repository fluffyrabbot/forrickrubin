#!/usr/bin/env python3
"""Regenerate data.json from git logs in ../apps sibling repos."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT.parent

# Repos whose README first line is missing or unhelpful get a curated tagline.
TAGLINE_OVERRIDES = {
    "fmarch": "From-scratch forum + messaging platform built around forum-mafia — event-sourced Rust.",
    "psychosismv": "Rapidfire LLM-journey music video — a beat-synced Remotion renderer.",
}


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
                "tagline": TAGLINE_OVERRIDES.get(entry.name) or tagline_for(entry),
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
            "mesh": {
                "burst": "557 commits in 30 days",
                "detail": "An E2EE, append-only event store with content-addressed blobs and server-blind encrypted search — the server never touches plaintext. 1,466 crates and 993 RFCs of composable primitives; verticals like rexxy and collablab are extracted from it, not bolted on.",
            },
            "rexxy": {
                "burst": "525 commits in 92 days",
                "detail": "Privacy-preserving P2P connectivity — direct encrypted links that never leak who is talking to whom. Six discovery tiers escalate from a zero-network address cache through mDNS, blind signaling, a Kademlia DHT and NAT hole-punching to a blind relay, each less metadata-revealing than the last.",
            },
            "stricttutor": {
                "burst": "136 commits in 30 days",
                "detail": "Studio-grade ed-tech run as a governed agent factory: a task registry, a parallel-execution playbook, and changed-file quality gates hold AI contributors to release-evidence contracts instead of vibes.",
            },
            "therightquestions": {
                "burst": "35 commits in 4 days",
                "detail": "A YouTube studio that turns a big question into a published episode — grounded web research → rapidfire script → ElevenLabs voiceover. Brave Search and Browserbase Fetch reach un-gated primary sources; cheap models synthesize, stronger agents author assets directly.",
            },
            "rabbotchan": {
                "burst": "186 commits",
                "detail": "Idea-to-published video-essay pipeline as a Cowork plugin, with a hard brand split: anything an LLM meaningfully touches ships as 'rabbot', carrying per-segment C2PA provenance — provenance as a structural commitment, not a label.",
            },
            "manicanim": {
                "burst": "38 commits in 4 days",
                "detail": "A Python-shaped but strictly bounded DSL for 3Blue1Brown-style typography animation, compiling to a serializable internal representation built for reliable human + agent co-editing: preview, diff, validate, repair.",
            },
            "psychosismv": {
                "burst": "Remotion pipeline",
                "detail": "A beat-synced 'rapidfire LLM-journey' music video rendered in Remotion: Python extracts snippets, analyzes audio and beats, builds a salience graph, then drives a layered hybrid layout locked to the beatmap.",
            },
            "agencyagency": {
                "burst": "content-as-data",
                "detail": "A two-corpus curriculum on agency for American teenagers, rendered through Astro/MDX with refusals, norms, drift patterns and citations lifted out of prose into Zod-validated YAML — a build that fails loudly on any broken cross-reference.",
            },
            "fmarch": {
                "burst": "21 commits in 4 days",
                "detail": "A from-scratch forum + messaging platform designed around forum-mafia (Mafia/Werewolf played over threads). Event-sourced Rust — domain, eventstore, projections and wire crates — with a touch-first host console as the showpiece. Built Phase 0→4 in days.",
            },
            "collablab": {
                "burst": "11 commits in 1 day",
                "detail": "A minimalist infinite canvas (tldraw) that lazy-loads collaborative power over true E2EE — the relay only ever sees ciphertext. Loro CRDT plus TreeKEM run in a Worker, with bring-your-own-relay sovereignty as a first-class feature.",
            },
            "travelami": {
                "burst": "18 commits in 3 days",
                "detail": "Builds a printable, laminatable medical/travel card in the local language with region-specific reminders you might not think to say: questionnaire → enrich → translate → human verify → print. A Cairo medical scenario runs end to end.",
            },
            "reluctocracy": {
                "burst": "7 commits in 2 days",
                "detail": "A design theory that treats grift-resistance as a security property — the people least likely to seek power are the most trustworthy to wield it, yet any system rewarding that trait attracts counterfeiters. Theory plus a v0 append-only protocol scaffold.",
            },
            "simcivics": {
                "burst": "greenfield",
                "detail": "A civic-reasoning system built around structured dialectic rather than social-network dynamics — a thesis, a domain model, and a first product slice for proving the dialectic substrate.",
            },
            "caloreceipt": {
                "burst": "local-first",
                "detail": "A local-first grocery nutrition ledger (Astro + Svelte 5) with a client-side session engine — explicit architecture, session and persistence boundaries, and documented privacy/network contracts.",
            },
            "altcs": {
                "burst": "thesis",
                "detail": "A thesis that CS pedagogy teaches content when the real meta-skill is navigation — problem-space identification as 'differential diagnosis for software', and a curriculum rebuilt around locating yourself in the space of problems.",
            },
            "llmepistemics": {
                "burst": "calibration game",
                "detail": "'The Jagged Frontier' — a calibration game: predict whether an LLM will nail or botch each of 20 tasks, surfacing how alien (and jagged) the real capability boundary is.",
            },
            "mnesoma": {
                "burst": "Apache-2.0 lib",
                "detail": "A replayable trace substrate for embodied/wearable sensor data — calibration-aware and version-deterministic, so any session can be replayed under any historical calibration, projection or model version. A 5-level replay engine that never silently degrades.",
            },
            "browserbox": {
                "burst": "100% local",
                "detail": "De-silo your browser history: merge Chromium, Gecko and Safari history into one view and export it — entirely client-side via sql.js (SQLite in WASM), with no uploads, accounts, or third-party fetches.",
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