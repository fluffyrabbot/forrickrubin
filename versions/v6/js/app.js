const TIER_LABELS = {
  flagship: "Flagship",
  creative: "Creative pipelines",
  burst: "June 2026 burst",
  systems: "Systems & products",
};

const TIER_ORDER = ["flagship", "creative", "burst", "systems"];

function fmt(n) {
  return Number(n).toLocaleString("en-US");
}

function githubUrl(origin, slug) {
  if (origin && origin.includes("github.com")) {
    return origin.replace(/\.git$/, "");
  }
  return `https://github.com/fluffyrabbot/${slug}`;
}

function repoBySlug(data, slug) {
  return data.owned.find((repo) => repo.slug === slug);
}

function renderStats(stats, generated) {
  const el = document.getElementById("stats-grid");
  const cards = [
    ["Owned repos", stats.owned_repos],
    ["Total commits", stats.total_commits],
    ["Last 30 days", stats.commits_30d],
    ["Last 7 days", stats.commits_7d],
    ["Forks excluded", stats.fork_repos],
  ];
  el.innerHTML = cards
    .map(
      ([label, value]) => `
      <div class="stat-card">
        <div class="stat-value">${fmt(value)}</div>
        <div class="stat-label">${label}</div>
      </div>`
    )
    .join("");
  document.getElementById("generated-at").textContent = `Data generated ${generated}`;
}

function renderTrq(trq) {
  const el = document.getElementById("trq-content");
  if (!trq || !el) return;

  const pipeline = trq.pipeline
    .map(
      (step, i) => `
      <div class="trq-step">
        <div class="trq-step-top">
          <span class="trq-step-num">${i + 1}</span>
          <span class="trq-step-name">${step.stage}</span>
          ${step.tool ? `<span class="trq-step-tool">${step.tool}</span>` : ""}
        </div>
        <p class="trq-step-detail">${step.detail}</p>
      </div>`
    )
    .join("");

  const episodes = trq.episodes
    .map(
      (ep) => `
      <a class="trq-ep" href="${ep.url}" target="_blank" rel="noopener">
        <div class="trq-ep-top">
          <span class="trq-ep-topic">${ep.topic}</span>
          <span class="trq-ep-dur">${ep.dur} min</span>
        </div>
        <h4 class="trq-ep-title">${ep.title}</h4>
        <p class="trq-ep-blurb">${ep.blurb}</p>
      </a>`
    )
    .join("");

  el.innerHTML = `
    <p class="trq-lede">
      A studio that takes a real question to a published episode in
      <strong>under ${trq.max_minutes} minutes end to end</strong>: grounded web
      research, a rapidfire script tuned to the channel's voice, and an ElevenLabs
      narration with aligned captions — then deployed live.
      <strong>${trq.episode_count} episodes</strong> shipped so far.
    </p>
    <p class="trq-cta">
      <a class="trq-link" href="${trq.site}" target="_blank" rel="noopener"
        >${trq.site.replace(/^https?:\/\//, "")} →</a
      >
    </p>
    <div class="trq-pipeline">${pipeline}</div>
    <h3 class="trq-subhead">Episode picks</h3>
    <div class="trq-eps">${episodes}</div>`;
}

function renderMesh(mesh) {
  const statsEl = document.getElementById("mesh-stats");
  const planesEl = document.getElementById("mesh-planes");
  if (!mesh || !statsEl || !planesEl) return;

  statsEl.innerHTML = mesh.stats
    .map(
      (stat) => `
      <div class="mesh-stat">
        <div class="mesh-stat-value">${fmt(stat.value)}</div>
        <div class="mesh-stat-label">${stat.label}</div>
      </div>`
    )
    .join("");

  planesEl.innerHTML = mesh.planes
    .map(
      (plane) => `
      <div class="mesh-plane">
        <div class="mesh-plane-head">
          <h3 class="mesh-plane-name">${plane.name}</h3>
          <p class="mesh-plane-blurb">${plane.blurb}</p>
        </div>
        <div class="mesh-vert-grid">
          ${plane.verticals
            .map(
              (vert) => `
            <div class="mesh-vert">
              <div class="mesh-vert-head">
                <span class="mesh-vert-name">${vert.name}</span>
                <span class="mesh-vert-count">${fmt(vert.count)} ${vert.unit}</span>
              </div>
              <p class="mesh-vert-detail">${vert.detail}</p>
            </div>`
            )
            .join("")}
        </div>
      </div>`
    )
    .join("");
}

function renderFeatured(data) {
  const tabs = document.getElementById("tier-tabs");
  const grid = document.getElementById("featured-grid");
  let activeTier = "flagship";

  function draw() {
    const slugs = data.featured[activeTier] || [];
    grid.innerHTML = slugs
      .map((slug) => {
        const repo = repoBySlug(data, slug);
        if (!repo) return "";
        const highlight = data.highlights[slug];
        const url = githubUrl(repo.origin, repo.slug);
        return `
        <article class="repo-card" data-tier="${activeTier}">
          <div class="repo-head">
            <h3 class="repo-name"><a href="${url}" target="_blank" rel="noopener">${repo.slug}</a></h3>
            ${highlight ? `<span class="repo-badge">${highlight.burst}</span>` : ""}
          </div>
          <p class="repo-tagline">${repo.tagline || "—"}</p>
          <div class="repo-metrics">
            <span><strong>${fmt(repo.commits)}</strong> commits</span>
            <span><strong>${repo.velocity}</strong>/day</span>
            <span><strong>${repo.c30}</strong> in 30d</span>
            <span>${repo.last}</span>
          </div>
          ${highlight ? `<p class="repo-highlight">${highlight.detail}</p>` : ""}
        </article>`;
      })
      .join("");
  }

  tabs.innerHTML = TIER_ORDER.map(
    (tier) =>
      `<button class="tier-tab${tier === activeTier ? " active" : ""}" data-tier="${tier}" type="button">${TIER_LABELS[tier]}</button>`
  ).join("");

  tabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tier]");
    if (!button) return;
    activeTier = button.dataset.tier;
    tabs.querySelectorAll(".tier-tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tier === activeTier);
    });
    draw();
  });

  draw();
}

function renderBurstTimeline(data) {
  const el = document.getElementById("burst-timeline");
  const items = [
    ["Jun 14–17", "therightquestions", "35 commits — full YouTube studio, 4+ episodes shipped"],
    ["Jun 12–15", "fmarch", "21 commits — forum-mafia platform Phase 0 through network boundary"],
    ["Jun 14–16", "travelami", "18 commits — deployable medical travel card, Netlify-ready"],
    ["Jun 16", "collablab", "11 commits — E2EE canvas architecture + Loro CRDT round-trip"],
    ["Jun 13–14", "reluctocracy", "7 commits — governance theory to protocol spec + TS scaffold"],
    ["Ongoing", "mesh", `${fmt(data.stats.commits_30d)} commits portfolio-wide in 30 days`],
  ];
  el.innerHTML = items
    .map(
      ([date, slug, text]) => `
      <div class="burst-item">
        <div class="burst-date">${date}</div>
        <div class="burst-body">
          <strong>${slug}</strong>
          <p>${text}</p>
        </div>
      </div>`
    )
    .join("");
}

function renderTable(data) {
  const tbody = document.getElementById("repo-table-body");
  const search = document.getElementById("repo-search");
  const activeOnly = document.getElementById("active-only");

  function draw() {
    const query = search.value.trim().toLowerCase();
    const onlyActive = activeOnly.checked;
    const rows = data.owned.filter((repo) => {
      if (onlyActive && repo.c30 === 0) return false;
      if (!query) return true;
      return (
        repo.slug.toLowerCase().includes(query) ||
        (repo.tagline || "").toLowerCase().includes(query)
      );
    });

    tbody.innerHTML = rows
      .map((repo) => {
        const url = githubUrl(repo.origin, repo.slug);
        const inactive = repo.c30 === 0 ? "inactive" : "";
        return `
        <tr class="${inactive}">
          <td><a href="${url}" target="_blank" rel="noopener">${repo.slug}</a></td>
          <td class="num">${fmt(repo.commits)}</td>
          <td class="num">${repo.c30}</td>
          <td class="num">${repo.velocity}</td>
          <td>${repo.last}</td>
          <td>${repo.tagline ? repo.tagline.slice(0, 60) + (repo.tagline.length > 60 ? "…" : "") : "—"}</td>
        </tr>`;
      })
      .join("");
  }

  search.addEventListener("input", draw);
  activeOnly.addEventListener("change", draw);
  draw();
}

async function main() {
  const response = await fetch("./data.json");
  const data = await response.json();
  renderStats(data.stats, data.generated);
  renderMesh(data.mesh);
  renderTrq(data.trq);
  renderFeatured(data);
  renderBurstTimeline(data);
  renderTable(data);
}

main().catch((error) => {
  console.error(error);
  document.body.insertAdjacentHTML(
    "beforeend",
    `<p style="color:#e8a849;padding:2rem">Failed to load portfolio data. Run <code>python3 scripts/generate.py</code> and serve over HTTP.</p>`
  );
});