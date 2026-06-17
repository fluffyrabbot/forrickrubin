#!/usr/bin/env python3
"""Regenerate data.json from git logs in ../apps sibling repos."""

import json
import os
import re
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

# The verticals that live *inside* mesh. Crate counts are computed live from
# mesh/crates by matching directory-name prefixes, so the numbers never drift
# from the codebase. Each plane is an editorial grouping; the breadth is the point.
MESH_PLANES = [
    {
        "name": "Products — the v-OS platform",
        "blurb": "Consumer apps that sit on the substrate. E2EE sync, server-blind search, 80% of revenue to user-chosen charities.",
        "verticals": [
            {
                "name": "memorise",
                "prefixes": ["memorise", "mesh-memorise", "mesh-extension-memorise", "tauri-plugin-memorise"],
                "detail": "Universal encrypted memory — drag anything, search everything. E2EE sync with server-blind tokens, spaced repetition, and Zettelkasten knowledge graphs across desktop, extension, and CLI.",
            },
            {
                "name": "v-OS",
                "prefixes": ["v-os", "v-text", "v-cli", "v-protocol"],
                "detail": "A universal versioning platform: undo for text, files, and archives; the editable web (v://, fork/improve/merge), crowd annotations, and translations — all flowing back into memory.",
            },
        ],
    },
    {
        "name": "Cultural monuments — educational games",
        "blurb": "Monument-grade games that demonstrate event sourcing, teach systems thinking, and preserve computing history.",
        "verticals": [
            {
                "name": "Monument-grade games",
                "games": True,
                "detail": "memorial-gardens (Turing, Lovelace, Hopper), museum, genetics, harmonic, factory-factory, archipelago, duplicator, idle-clicker, collider — event sourcing taught through play, built to monument quality.",
            },
        ],
    },
    {
        "name": "Infrastructure — the developer platform",
        "blurb": "The surprising breadth: one server workspace spans crypto, search, supply chain, compliance, mocap, and more — each a real crate family.",
        "verticals": [
            {
                "name": "Event store & crypto core",
                "prefixes": ["mesh-crypto", "mesh-domain", "mesh-repo", "mesh-blob", "mesh-events-http", "mesh-memcore", "mesh-client"],
                "detail": "Append-only E2EE event store: Argon2id / HKDF / XChaCha20 crypto, content-addressed blobs, monotonic sequencing, and a type-safe domain where illegal states fail to compile.",
            },
            {
                "name": "Blind search",
                "prefixes": ["mesh-search"],
                "detail": "Server-assisted encrypted search via HMAC-blinded, epoch-rotated tokens — the server helps you search without ever reading your queries.",
            },
            {
                "name": "Topology compiler (forge)",
                "prefixes": ["forge", "mesh-network"],
                "detail": "A protocol DSL: TOML specs compile to typed Rust edge binaries and heterogeneous Docker + mTLS topologies with zero-knowledge routing.",
            },
            {
                "name": "Intent orchestration (archon)",
                "prefixes": ["archon"],
                "detail": "High-level intent expanded into durable, observable workflows — spec-driven deployment to bare metal or Kubernetes with guardrails and backups.",
            },
            {
                "name": "Factory & supply chain",
                "prefixes": ["mesh-factory", "mesh-build-factory", "mesh-verify"],
                "detail": "Ed25519 certification chains (Factory³ → Factory² → Factory¹ → product) with capability manifests, offline attestation, and transparency logs.",
            },
            {
                "name": "Compliance automation (notaio)",
                "prefixes": ["notaio", "lysergic"],
                "detail": "PCI, HIPAA, SOC2, and GDPR templates compiled into signed evidence bundles.",
            },
            {
                "name": "Collaborative editing",
                "prefixes": ["mesh-collab", "mesh-memory-rewind"],
                "detail": "CRDT collaboration with O(1) undo/redo and git-like branching timeline scrubbing on a rope-based, WASM-ready core.",
            },
            {
                "name": "Mastery engine",
                "prefixes": ["mesh-mastery"],
                "detail": "A deterministic spaced-repetition mastery engine — no_std, replayable, projection-driven.",
            },
            {
                "name": "Knowledge graph & LLM memex",
                "prefixes": ["mesh-graph", "llm-memex"],
                "detail": "An embedding knowledge graph with coherence measurement, plus autonomous LLM exploration trails through pluggable web, citation, and concept explorers.",
            },
            {
                "name": "Motion capture",
                "prefixes": ["mesh-mocap"],
                "detail": "An open motion-capture pipeline: the OMF format, inverse kinematics, UDP tracking, and delta compression.",
            },
            {
                "name": "Interactive fiction",
                "prefixes": ["mesh-samizdat"],
                "detail": "An interactive-fiction runtime with E2EE cloud sync.",
            },
            {
                "name": "Anti-abuse",
                "prefixes": ["mesh-pow"],
                "detail": "OPRF-blinded proof-of-work for rate limiting without tracking users.",
            },
        ],
    },
]


def mesh_crate_count(crates_dir: Path, prefixes: list[str]) -> int:
    if not crates_dir.is_dir():
        return 0
    return sum(
        1
        for entry in crates_dir.iterdir()
        if entry.is_dir() and any(entry.name.startswith(p) for p in prefixes)
    )


def build_mesh(repos: list[dict]) -> dict | None:
    mesh_path = APPS / "mesh"
    crates_dir = mesh_path / "crates"
    if not crates_dir.is_dir():
        return None

    crate_total = sum(1 for p in crates_dir.rglob("Cargo.toml") if "/target/" not in str(p))

    docs = mesh_path / "docs"
    rfc_numbers = set()
    if docs.is_dir():
        for path in docs.rglob("[0-9]*.md"):
            match = re.match(r"\d{3,4}", path.name)
            if match:
                rfc_numbers.add(match.group(0))
    rfc_total = len(rfc_numbers)

    games = mesh_path / "crates" / "games"
    games_count = sum(1 for d in games.iterdir() if d.is_dir()) if games.is_dir() else 0

    mesh_repo = next((r for r in repos if r["slug"] == "mesh"), None)

    planes = []
    for plane in MESH_PLANES:
        verticals = []
        for vert in plane["verticals"]:
            if vert.get("games"):
                count, unit = games_count, "games"
            else:
                count = mesh_crate_count(crates_dir, vert["prefixes"])
                unit = "crate" if count == 1 else "crates"
            verticals.append(
                {"name": vert["name"], "detail": vert["detail"], "count": count, "unit": unit}
            )
        planes.append({"name": plane["name"], "blurb": plane["blurb"], "verticals": verticals})

    return {
        "stats": [
            {"label": "Rust crates", "value": crate_total},
            {"label": "RFCs", "value": rfc_total},
            {"label": "commits", "value": mesh_repo["commits"] if mesh_repo else 0},
            {"label": "in last 30 days", "value": mesh_repo["c30"] if mesh_repo else 0},
        ],
        "planes": planes,
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
        "mesh": build_mesh(repos),
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

    # Write into the current version directory (the editable source for the
    # latest release). The homepage redirector and /versions/<id>/ serve it.
    manifest_path = ROOT / "versions.json"
    output = ROOT / "data.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        current = manifest.get("current")
        version_dir = ROOT / "versions" / current if current else None
        if version_dir and version_dir.is_dir():
            output = version_dir / "data.json"

    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {output} ({len(owned)} owned repos)")


if __name__ == "__main__":
    main()