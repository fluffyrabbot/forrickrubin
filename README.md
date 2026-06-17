# Agentic Portfolio Showcase

Static showcase site for the YC AI Summer Residency application. Pulls live stats from sibling repos in `~/apps` via git logs.

## Local preview

```bash
python3 scripts/generate.py   # refresh data.json
python3 -m http.server 8787
# → http://localhost:8787
```

## Deploy to Cloudflare Pages

**Option A — Wrangler CLI**

```bash
npm run generate
npx wrangler pages deploy . --project-name=forrickrubin
```

**Option B — Dashboard**

1. Create a Pages project at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Connect this repo or upload the directory
3. Build command: `python3 scripts/generate.py`
4. Build output directory: `.` (root)

No bundler required — plain HTML/CSS/JS.

## Versioning

The site is a set of self-contained snapshots under `versions/<id>/`. The repo
root is a redirector that routes the homepage to the **latest** version, so `/`
always tracks the newest release while every version keeps a stable permalink at
`/versions/<id>/`. A sticky revision bar (driven by `versions.json`) lets you
hop between versions.

Cut a release:

```bash
python3 scripts/release.py v4 "What changed"   # scaffolds versions/v4 from latest,
                                               # repoints the homepage redirect
# edit versions/v4/{index.html,css,js}
python3 scripts/generate.py                    # refreshes versions/v4/data.json
```

`release.py` writes both `_redirects` (Cloudflare 302) and the `index.html`
JS/meta-refresh fallback, and updates `versions.json`.

## Structure

```
index.html            # homepage redirector → latest version
_redirects            # Cloudflare 302 from / to the latest version
versions.json         # release manifest (id, path, timestamp, label)
versions/<id>/        # self-contained snapshot: index.html, css/, js/, data.json
scripts/generate.py   # writes data.json into the current version dir
scripts/release.py    # cut/repoint a release
```