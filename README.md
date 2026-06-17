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

## Structure

```
index.html       # showcase page
css/style.css    # editorial dark theme
js/app.js        # renders data.json
data.json        # generated portfolio stats
scripts/generate.py
```