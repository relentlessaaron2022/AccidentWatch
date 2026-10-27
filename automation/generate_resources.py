#!/usr/bin/env python3
"""
generate_resources.py — Claude-powered SEO article generator for AccidentWatch.

Generates road-safety / accident / legal-resource articles as static HTML pages
styled to match the site, then rebuilds the resources.html hub page that links
to them.

These resource articles drive organic search traffic, which is what makes the
site's attorney advertising inventory (see advertise.html) worth paying for.

USAGE
    export ANTHROPIC_API_KEY=sk-ant-...        # never commit this
    python automation/generate_resources.py "What to do after a car accident"
    python automation/generate_resources.py --from-file automation/topics.txt

The API key is read ONLY from the ANTHROPIC_API_KEY environment variable.
Never hardcode it or commit it.
"""

import argparse
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    sys.exit(
        "The 'anthropic' package is not installed.\n"
        "Install it with:  pip install -r automation/requirements.txt"
    )

# Model is configurable via env var; default to a cost-effective, high-quality model.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = ROOT / "resources"
HUB_PAGE = ROOT / "resources.html"

# --- Site chrome, kept consistent with the rest of AccidentWatch -------------

HEADER = """    <!-- Header -->
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <h1>AccidentWatch</h1>
                </div>
                <nav class="main-nav">
                    <ul>
                        <li><a href="../index.html">Home</a></li>
                        <li><a href="../report.html">Report Accident</a></li>
                        <li><a href="../map.html">Accident Map</a></li>
                        <li><a href="../contest.html">Monthly Contest</a></li>
                        <li><a href="../about.html">About</a></li>
                        <li><a href="../login.html" class="btn btn-outline">Login</a></li>
                        <li><a href="../register.html" class="btn btn-primary">Register</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>
"""

FOOTER = """    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-bottom">
                <p>&copy; {year} AccidentWatch. All rights reserved.</p>
            </div>
        </div>
    </footer>
""".format(year=date.today().year)

# Disclaimer shown on every generated article. AccidentWatch is not a law firm;
# articles are general information, not legal advice. This protects the brand.
DISCLAIMER = (
    '<p class="article-disclaimer"><strong>Disclaimer:</strong> This article is '
    "general information about road safety and the accident-claims process, not "
    "legal advice. Every situation is different. For advice about your specific "
    "circumstances, consult a licensed attorney in your jurisdiction.</p>"
)

ARTICLE_STYLE = """    <style>
        .article-hero { background: linear-gradient(135deg, #1976d2, #0d47a1); color:#fff; padding:55px 0; }
        .article-hero h1 { font-size:2.1rem; max-width:820px; }
        .article-body { max-width:820px; margin:0 auto; padding:45px 0; line-height:1.75; }
        .article-body h2 { color:#0d47a1; margin:32px 0 12px; }
        .article-body h3 { color:#1565c0; margin:24px 0 10px; }
        .article-body p, .article-body li { color:#333; }
        .article-body ul, .article-body ol { margin:0 0 18px 22px; }
        .article-meta { color:#666; font-size:0.9rem; margin-top:10px; }
        .article-disclaimer { background:#f8f9fa; border-left:4px solid #1976d2; padding:15px; font-size:0.9rem; margin:35px 0 0; }
        .article-cta { background:#f0f7ff; border:1px solid #d0e4ff; border-radius:8px; padding:25px; margin:35px 0 0; text-align:center; }
    </style>
"""

CTA = (
    '<div class="article-cta">'
    "<h3>Were you recently in an accident?</h3>"
    '<p>Report it to help others stay safe, or connect with legal professionals in our directory.</p>'
    '<a href="../report.html" class="btn btn-primary">Report an Accident</a></div>'
)

SYSTEM_PROMPT = (
    "You are an expert content writer for AccidentWatch, a community road-safety "
    "and accident-reporting platform. You write accurate, genuinely helpful, "
    "SEO-optimized articles for people dealing with the aftermath of car accidents.\n\n"
    "Rules:\n"
    "- Be factually accurate and practical. Do NOT invent statistics, laws, dollar "
    "amounts, or citations. If a number varies by state/jurisdiction, say so rather "
    "than inventing one.\n"
    "- This is general information, NOT legal advice, and AccidentWatch is not a law "
    "firm. Never imply otherwise.\n"
    "- Write for a general audience at a clear reading level. Use H2/H3 headings, "
    "short paragraphs, and bulleted or numbered lists where helpful.\n"
    "- No fearmongering, no fake urgency, no deceptive claims.\n"
    "Return ONLY valid JSON (no markdown fences) with this exact shape:\n"
    '{"title": "...", "meta_description": "... (<=155 chars)", '
    '"body_html": "<h2>...</h2><p>...</p>..."}\n'
    "body_html must be the article body only (no <html>, <head>, <h1>, header, or "
    "footer) using only h2/h3/p/ul/ol/li/strong/em tags."
)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:70] or "article"


def generate_article(client: Anthropic, topic: str) -> dict:
    """Call Claude to produce a structured article for one topic."""
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Write an article on: {topic}"}],
    )
    raw = "".join(block.text for block in msg.content if block.type == "text").strip()
    # Strip accidental code fences if the model added them.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    data = json.loads(raw)
    for key in ("title", "meta_description", "body_html"):
        if key not in data or not data[key]:
            raise ValueError(f"Model response missing '{key}'")
    return data


def render_article_page(data: dict, topic: str) -> str:
    title = html.escape(data["title"])
    meta = html.escape(data["meta_description"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - AccidentWatch</title>
    <meta name="description" content="{meta}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta}">
    <meta property="og:type" content="article">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
{ARTICLE_STYLE}</head>
<body>
{HEADER}
    <section class="article-hero">
        <div class="container">
            <h1>{title}</h1>
            <p class="article-meta">Road Safety &amp; Accident Resources &middot; Updated {date.today():%B %Y}</p>
        </div>
    </section>

    <article class="container">
        <div class="article-body">
{data["body_html"]}
{CTA}
{DISCLAIMER}
        </div>
    </article>

{FOOTER}</body>
</html>
"""


def rebuild_hub():
    """Regenerate resources.html listing every article in resources/."""
    articles = []
    for path in sorted(RESOURCES_DIR.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        tmatch = re.search(r"<title>(.*?) - AccidentWatch</title>", text, re.S)
        dmatch = re.search(r'<meta name="description" content="(.*?)">', text, re.S)
        articles.append({
            "href": f"resources/{path.name}",
            "title": html.unescape(tmatch.group(1).strip()) if tmatch else path.stem,
            "desc": html.unescape(dmatch.group(1).strip()) if dmatch else "",
        })

    if articles:
        cards = "\n".join(
            f"""                <a class="resource-card" href="{html.escape(a['href'])}">
                    <h3>{html.escape(a['title'])}</h3>
                    <p>{html.escape(a['desc'])}</p>
                </a>""" for a in articles
        )
    else:
        cards = '                <p class="resource-empty">Resource articles are being added. Check back soon.</p>'

    hub = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Road Safety &amp; Accident Resources - AccidentWatch</title>
    <meta name="description" content="Practical guides on road safety, what to do after a car accident, insurance claims, and the legal process. Free resources from AccidentWatch.">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        .resources-hero {{ background:linear-gradient(135deg,#1976d2,#0d47a1); color:#fff; padding:60px 0; text-align:center; }}
        .resources-hero h1 {{ font-size:2.3rem; margin-bottom:12px; }}
        .resources-hero p {{ max-width:680px; margin:0 auto; opacity:.95; }}
        .resource-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:22px; padding:50px 0; }}
        .resource-card {{ display:block; background:#fff; border:1px solid #eee; border-radius:8px; padding:24px; text-decoration:none; color:inherit; box-shadow:0 2px 6px rgba(0,0,0,.05); transition:transform .15s,box-shadow .15s; }}
        .resource-card:hover {{ transform:translateY(-3px); box-shadow:0 6px 16px rgba(0,0,0,.1); }}
        .resource-card h3 {{ color:#0d47a1; margin-bottom:8px; }}
        .resource-card p {{ color:#555; font-size:.92rem; line-height:1.55; }}
        .resource-empty {{ grid-column:1/-1; text-align:center; color:#777; padding:40px 0; }}
    </style>
</head>
<body>
{HEADER}
    <section class="resources-hero">
        <div class="container">
            <h1>Road Safety &amp; Accident Resources</h1>
            <p>Practical, plain-language guides to help you stay safe and navigate what comes after a car accident.</p>
        </div>
    </section>

    <section class="container">
        <div class="resource-grid">
{cards}
        </div>
    </section>

{FOOTER}</body>
</html>
"""
    HUB_PAGE.write_text(hub, encoding="utf-8")
    return len(articles)


def main():
    parser = argparse.ArgumentParser(description="Generate SEO resource articles with Claude.")
    parser.add_argument("topic", nargs="?", help="A single article topic.")
    parser.add_argument("--from-file", help="Path to a file with one topic per line.")
    parser.add_argument("--rebuild-only", action="store_true",
                        help="Only rebuild resources.html from existing articles (no API calls).")
    args = parser.parse_args()

    RESOURCES_DIR.mkdir(exist_ok=True)

    if args.rebuild_only:
        n = rebuild_hub()
        print(f"Rebuilt resources.html with {n} article(s). No API calls made.")
        return

    topics = []
    if args.from_file:
        topics += [t.strip() for t in Path(args.from_file).read_text().splitlines() if t.strip() and not t.startswith("#")]
    if args.topic:
        topics.append(args.topic)
    if not topics:
        parser.error("Provide a topic, --from-file, or --rebuild-only.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set. Export it before running (never commit it).")

    client = Anthropic(api_key=api_key)

    for topic in topics:
        print(f"Generating: {topic!r} ...")
        try:
            data = generate_article(client, topic)
        except Exception as e:  # noqa: BLE001 - surface any failure per-topic, keep going
            print(f"  ! Failed: {e}", file=sys.stderr)
            continue
        out = RESOURCES_DIR / f"{slugify(topic)}.html"
        out.write_text(render_article_page(data, topic), encoding="utf-8")
        print(f"  -> {out.relative_to(ROOT)}  ({data['title']})")

    n = rebuild_hub()
    print(f"Done. resources.html now lists {n} article(s).")


if __name__ == "__main__":
    main()
