"""Build the portfolio site (static HTML) from ../cv/cv_data.yaml and site_data.yaml.

    python build.py        # writes index.html and copies the CV PDFs into cv/

Content is rendered into the HTML (readable without JavaScript and by search engines); assets/app.js only adds
interaction: theme toggle, rotating roles, count-up stats, project filters and detail dialogs, scroll reveals,
skill tabs and copy-to-clipboard.
"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CV_DIR = ROOT.parent / "cv"
e = html.escape

FILTERS = [("all", "All"), ("agents", "LLM agents"), ("rag", "RAG & retrieval"), ("data", "Data science"), ("research", "Research")]
ICONS = {
    "github": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.77.11 3.06.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.39-5.27 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13ZM7.12 20.45H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0Z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm0 1 8 7 8-7"/></svg>',
    "download": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 3v12m0 0 5-5m-5 5-5-5M4 21h16"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6 6 6-6 6"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></g></svg>',
    "moon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/></svg>',
    "copy": '<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/></g></svg>',
}
# before -> after metrics for the thesis bars (from the thesis results: paired comparison on 15 comics)
THESIS_BARS = [("Spoken lines printed", 0.49, 1.00), ("Dialogue F1 vs gold", 0.63, 1.00), ("Speaker accuracy", 0.83, 1.00),
               ("Character recall", 0.78, 1.00), ("Face consistency (DINOv2)", 0.54, 0.67)]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cv_project(cv: dict, name: str) -> dict:
    for p in cv["projects"]:
        if p["name"].lower().startswith(name.lower()[:14]):
            return p
    return {}


def bullets(item: dict) -> list[str]:
    return [b["text"] if isinstance(b, dict) else b for b in item.get("bullets", [])]


def project_cards(site: dict, cv: dict) -> tuple[str, str]:
    cards, dialogs = [], []
    for i, p in enumerate(site["projects"]):
        sid = slug(p["name"])
        cvp = cv_project(cv, p["name"])
        badge = ('<span class="badge badge-live">Evaluation in progress</span>' if p["status"] == "running"
                 else '<span class="badge badge-done">Live product</span>' if p["status"] == "live"
                 else '<span class="badge badge-done">Measured</span>')
        private = '<span class="badge badge-private">Private code</span>' if not p.get("repo") else ""
        chips = "".join(f"<li>{e(h)}</li>" for h in p["highlights"])
        tags = "".join(f"<span class='tag'>{e(t)}</span>" for t in p["tags"])
        cards.append(f"""
      <article class="card reveal" data-cat="{' '.join(p['category'])}" style="--i:{i}">
        <div class="card-top">{badge}{private}</div>
        <h3>{e(p['name'])}</h3>
        <p class="card-blurb">{e(p['blurb'])}</p>
        <ul class="highlights">{chips}</ul>
        <div class="tags">{tags}</div>
        <div class="card-actions">
          <button class="btn btn-ghost" data-open="dlg-{sid}" aria-haspopup="dialog">Details {ICONS['arrow']}</button>
          {f'<a class="btn btn-ghost" href="{e(p["repo"])}" target="_blank" rel="noopener">{ICONS["github"]} Code</a>' if p.get("repo")
           else f'<a class="btn btn-ghost" href="{e(p["link"])}" target="_blank" rel="noopener">{e(p.get("link_label", "Open"))} {ICONS["arrow"]}</a>' if p.get("link")
           else f'<span class="muted small">{e(p.get("note", ""))}</span>'}
        </div>
      </article>""")
        detail = "".join(f"<li>{e(b)}</li>" for b in bullets(cvp))
        dialogs.append(f"""
    <dialog id="dlg-{sid}" class="dialog" aria-labelledby="dlg-{sid}-title">
      <form method="dialog"><button class="dialog-close" aria-label="Close">×</button></form>
      <p class="eyebrow">{e(cvp.get('stack', ''))}</p>
      <h3 id="dlg-{sid}-title">{e(p['name'])}</h3>
      <p>{e(p['blurb'])}</p>
      <h4>What I built and measured</h4>
      <ul class="detail-list">{detail}</ul>
      <div class="tags">{tags}</div>
      {f'<a class="btn btn-primary" href="{e(p["repo"])}" target="_blank" rel="noopener">{ICONS["github"]} View the repository</a>' if p.get("repo") else ''}
      {''.join(f'<a class="btn btn-ghost" href="{e(u)}" target="_blank" rel="noopener">{e(n)} {ICONS["arrow"]}</a> ' for n, u in p.get("links", []))}
      {f'<p class="muted">{e(p.get("note", ""))}</p>' if p.get("note") else ''}
      {'<p class="muted small">The code and the evaluation harness are finished; the full evaluation is running and the results will appear here.</p>' if p["status"] == "running" else ''}
    </dialog>""")
    return "".join(cards), "".join(dialogs)


def research_html(cv: dict) -> str:
    thesis, paper = cv["research"][0], cv["research"][1]
    bars = "".join(f"""
          <div class="bar-row">
            <div class="bar-label">{e(n)}</div>
            <div class="bar-track" role="img" aria-label="{e(n)}: baseline {a:.2f}, thesis method {b:.2f}">
              <span class="bar bar-before" style="--w:{a * 100:.0f}%"></span>
              <span class="bar bar-after" style="--w:{b * 100:.0f}%"></span>
            </div>
            <div class="bar-val"><span class="muted">{a:.2f}</span> → <b>{b:.2f}</b></div>
          </div>""" for n, a, b in THESIS_BARS)
    return f"""
      <div class="research-grid">
        <article class="panel reveal">
          <p class="eyebrow">MS thesis · in progress</p>
          <h3>UrduComicLab: complete Urdu stories → right-to-left comics</h3>
          <p>{e(bullets(thesis)[0])}</p>
          <div class="bars" data-bars>
            <div class="legend"><span class="key key-before"></span>Baseline <span class="key key-after"></span>Thesis method</div>
            {bars}
          </div>
          <p class="muted small">15 paired comics (3 stories × 5 seeds), paired bootstrap confidence intervals; about 35 pinned open-weight models benchmarked.</p>
        </article>
        <article class="panel reveal">
          <p class="eyebrow">Paper · pending publication</p>
          <h3>CNN vs Vision Transformer on imbalanced FER2013</h3>
          <ul class="detail-list">{''.join(f'<li>{e(b)}</li>' for b in bullets(paper))}</ul>
          <div class="duel">
            <div><span class="duel-num" data-count="64.9" data-decimals="1">0</span><span class="duel-unit">%</span><p>ViT accuracy on the rarest class (Disgust)</p></div>
            <div><span class="duel-num">0</span><span class="duel-unit">%</span><p>CNN on the same class</p></div>
          </div>
        </article>
      </div>"""


def for_site(item: dict, v: str = "ai") -> bool:
    return v in item.get("for", [v]) and v not in item.get("not_for", [])


def experience_html(cv: dict) -> str:
    out = []
    for x in cv["experience"]:
        bl = "".join(f"<li>{e(b['text'] if isinstance(b, dict) else b)}</li>"
                     for b in x.get("bullets", []) if not isinstance(b, dict) or for_site(b))
        out.append(f"""
        <li class="tl-item reveal">
          <div class="tl-dot"></div>
          <div class="tl-card">
            <div class="tl-head"><h3>{e(x.get('role_ai') or x['role'])} · {e(x['org'])}</h3><span class="tl-date">{e(x['dates'])}</span></div>
            <p class="muted small">{e(x['place'])}</p>
            <ul class="detail-list">{bl}</ul>
          </div>
        </li>""")
    ed = cv["education"][0]
    out.append(f"""
        <li class="tl-item reveal">
          <div class="tl-dot tl-dot-edu"></div>
          <div class="tl-card">
            <div class="tl-head"><h3>{e(ed['degree'])} · {e(ed['org'])}</h3><span class="tl-date">{e(ed['dates'])}</span></div>
            <p>{e(ed['detail'])}</p>
            <p class="muted small">Certifications: {e(' · '.join(cv['certifications']))}</p>
          </div>
        </li>""")
    return "".join(out)


def clients_html(cv: dict) -> str:
    cards = []
    for i, x in enumerate(cv.get("client_projects", [])):
        tags = "".join(f"<span class='tag'>{e(t.strip())}</span>" for t in x["stack"].split("·"))
        cards.append(f"""
      <article class="card card-mini reveal" style="--i:{i % 6}">
        <div class="card-top"><span class="badge badge-private">Client · code private</span></div>
        <h3>{e(x['name'])}</h3>
        <p class="card-blurb">{e(x['text'])}</p>
        <div class="tags">{tags}</div>
      </article>""")
    return "".join(cards)


def skills_html(cv: dict) -> str:
    groups = []
    seen = set()
    for v in ("ai", "ds", "research"):
        for name, items in cv["variants"][v]["skills"]:
            if name in seen:
                continue
            seen.add(name)
            groups.append((name, [s.strip() for s in re.split(r",(?![^()]*\))", items) if s.strip()]))
    tabs = "".join(f'<button role="tab" class="tab" aria-selected="{str(i == 0).lower()}" aria-controls="sk-{i}" id="tab-{i}">{e(n)}</button>'
                   for i, (n, _) in enumerate(groups))
    panels = "".join(f'<div role="tabpanel" class="tab-panel" id="sk-{i}" aria-labelledby="tab-{i}" {"" if i == 0 else "hidden"}>'
                     + "".join(f"<span class='skill' style='--i:{j}'>{e(s)}</span>" for j, s in enumerate(items)) + "</div>"
                     for i, (_, items) in enumerate(groups))
    return f'<div class="tabs" role="tablist" aria-label="Skill groups">{tabs}</div>{panels}'


def page(site: dict, cv: dict) -> str:
    c = cv["contact"]
    cards, dialogs = project_cards(site, cv)
    stats = "".join(f"""<div class="stat reveal"><span class="stat-num" data-count="{s['value']}" data-decimals="{s.get('decimals', 0)}">0</span><span class="stat-suffix">{e(s['suffix'])}</span><p>{e(s['label'])}</p></div>"""
                    for s in site["stats"])
    filters = "".join(f'<button class="chip{" active" if k == "all" else ""}" data-filter="{k}" aria-pressed="{str(k == "all").lower()}">{e(lbl)}</button>' for k, lbl in FILTERS)
    cvs = [(v["file"], v["headline"].split(" · ")[0]) for v in cv["variants"].values() if v.get("site", True)]
    cv_links = "".join(f'<a href="cv/{e(f)}.pdf" download>{ICONS["download"]} {e(t)} CV</a>' for f, t in cvs)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(site['title'])}</title>
  <meta name="description" content="{e(site['tagline'])} 30+ projects in LLM agents, RAG, AI apps, data science and machine-learning research.">
  <meta property="og:title" content="{e(site['title'])}">
  <meta property="og:description" content="{e(site['tagline'])}">
  <meta property="og:type" content="website">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/style.css">
  <script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
</head>
<body>
  <div class="progress" aria-hidden="true"></div>
  <header class="nav">
    <a class="brand" href="#top">MIU<span>.</span></a>
    <nav aria-label="Main">
      <button class="menu-btn" aria-expanded="false" aria-controls="menu" aria-label="Menu"><span></span><span></span></button>
      <ul id="menu">
        <li><a href="#projects">Projects</a></li><li><a href="#clients">Client work</a></li><li><a href="#research">Research</a></li>
        <li><a href="#experience">Experience</a></li><li><a href="#skills">Skills</a></li><li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
    <button class="theme-btn" aria-label="Toggle dark mode"><span class="i-sun">{ICONS['sun']}</span><span class="i-moon">{ICONS['moon']}</span></button>
  </header>

  <main id="top">
    <section class="hero">
      <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="grid-bg"></div>
      <div class="hero-inner">
        <p class="eyebrow mono">Islamabad, Pakistan · open to onsite, hybrid & remote</p>
        <h1>{e(cv['name'])}</h1>
        <p class="role"><span class="role-text" data-roles='["AI/ML Engineer","Data Scientist","ML Researcher","LLM Agent Builder","AI App Developer"]'>AI/ML Engineer</span><span class="caret"></span></p>
        <p class="tagline">{e(site['tagline'])}</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="#projects">See the projects {ICONS['arrow']}</a>
          <div class="dropdown">
            <button class="btn btn-ghost" aria-expanded="false" aria-haspopup="true">{ICONS['download']} Download CV</button>
            <div class="dropdown-menu">{cv_links}</div>
          </div>
        </div>
        <div class="socials">
          <a href="https://{e(c['github'])}" target="_blank" rel="noopener" aria-label="GitHub">{ICONS['github']}</a>
          <a href="https://{e(c['linkedin'])}" target="_blank" rel="noopener" aria-label="LinkedIn">{ICONS['linkedin']}</a>
          <a href="mailto:{e(c['email'])}" aria-label="E-mail">{ICONS['mail']}</a>
        </div>
      </div>
    </section>

    <section class="stats" aria-label="Highlights">{stats}</section>

    <section id="about" class="section narrow reveal">
      <p class="eyebrow">About</p>
      <h2>Engineering that is measured, not just demoed</h2>
      <p class="lead">{e(site['intro'])}</p>
    </section>

    <section id="projects" class="section">
      <div class="section-head reveal">
        <p class="eyebrow">Selected work</p>
        <h2>Projects</h2>
        <p class="muted">A live product, my public portfolio projects (each with tests, launchers for Windows and macOS, and an evaluation on held-out data) and private work.</p>
      </div>
      <div class="filters" role="group" aria-label="Filter projects">{filters}</div>
      <div class="cards">{cards}</div>
    </section>

    <section id="clients" class="section">
      <div class="section-head reveal">
        <p class="eyebrow">Client work</p>
        <h2>More projects</h2>
        <p class="muted">A selection of projects built for clients. The code belongs to them, so it is not public; I am happy to walk through any of them.</p>
      </div>
      <div class="cards">{clients_html(cv)}</div>
    </section>

    <section id="research" class="section">
      <div class="section-head reveal"><p class="eyebrow">Research</p><h2>Thesis and publications</h2></div>
      {research_html(cv)}
    </section>

    <section id="experience" class="section">
      <div class="section-head reveal"><p class="eyebrow">Career</p><h2>Experience & education</h2></div>
      <ol class="timeline">{experience_html(cv)}</ol>
    </section>

    <section id="skills" class="section">
      <div class="section-head reveal"><p class="eyebrow">Toolbox</p><h2>Skills</h2></div>
      <div class="skills reveal">{skills_html(cv)}</div>
    </section>

    <section id="contact" class="section contact reveal">
      <p class="eyebrow">Contact</p>
      <h2>Let's talk</h2>
      <p class="lead">Hiring for an AI/ML engineering, data science or research role? I would be glad to walk you through any of these projects.</p>
      <div class="contact-row">
        <button class="btn btn-primary copy" data-copy="{e(c['email'])}">{ICONS['copy']} <span>{e(c['email'])}</span></button>
        <a class="btn btn-ghost" href="https://{e(c['linkedin'])}" target="_blank" rel="noopener">{ICONS['linkedin']} LinkedIn</a>
        <a class="btn btn-ghost" href="https://{e(c['github'])}" target="_blank" rel="noopener">{ICONS['github']} GitHub</a>
      </div>
      <div class="cv-row">{cv_links}</div>
    </section>
  </main>

  {dialogs}
  <footer class="footer"><p>© 2026 {e(cv['name'])} · Built by hand, no framework · <a href="#top">Back to top ↑</a></p></footer>
  <div class="toast" role="status" aria-live="polite"></div>
  <script src="assets/app.js" defer></script>
</body>
</html>
"""


def main() -> None:
    cv = yaml.safe_load((CV_DIR / "cv_data.yaml").read_text(encoding="utf-8"))
    site = yaml.safe_load((ROOT / "site_data.yaml").read_text(encoding="utf-8"))
    (ROOT / "index.html").write_text(page(site, cv), encoding="utf-8")
    out = ROOT / "cv"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.pdf"):
        old.unlink()
    for v in cv["variants"].values():
        if not v.get("site", True):
            continue
        src = CV_DIR / "output" / f"{v['file']}.pdf"
        if src.exists():
            shutil.copy2(src, out / src.name)
    print("wrote index.html and", len(list(out.glob("*.pdf"))), "CV PDFs")


if __name__ == "__main__":
    main()
