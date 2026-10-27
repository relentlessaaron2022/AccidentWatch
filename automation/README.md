# AccidentWatch Automation

Claude-powered automations that generate revenue-supporting content for the site.

## What's here

| Script | What it does |
|--------|--------------|
| `generate_resources.py` | Uses the Claude API to write road-safety / accident / legal-process articles as static HTML pages in `../resources/`, then rebuilds `../resources.html` (the resource hub the homepage links to). |

**Why this makes money:** the resource articles drive organic search traffic.
Traffic is what makes the site's attorney advertising inventory (`advertise.html`)
worth paying for. More relevant visitors → more valuable ad placements.

## Setup

```bash
# 1. Install dependencies (use a virtualenv if you like)
pip install -r automation/requirements.txt

# 2. Provide your Anthropic API key via environment variable.
#    NEVER hardcode it or commit it.
export ANTHROPIC_API_KEY=sk-ant-...

# optional: pick a model (defaults to claude-sonnet-5-5)
export ANTHROPIC_MODEL=claude-sonnet-5-5
```

## Usage

```bash
# Generate one article
python automation/generate_resources.py "What to do after a car accident"

# Generate a batch from the starter topic list
python automation/generate_resources.py --from-file automation/topics.txt

# Rebuild resources.html from existing articles (no API calls, no cost)
python automation/generate_resources.py --rebuild-only
```

Generated articles land in `../resources/<slug>.html` and are automatically
listed on `../resources.html`. Commit the results to publish them.

## Cost

Each article is a single API call (a few thousand output tokens). On
`claude-sonnet-5-5` that is a fraction of a cent to a few cents per article —
the full starter list of 8 topics costs well under a dollar.

## Guardrails built into the script

- The API key is read **only** from `ANTHROPIC_API_KEY` — never stored in code.
- The system prompt forbids inventing statistics, laws, or dollar amounts.
- Every article carries a disclaimer: general information, **not legal advice**;
  AccidentWatch is not a law firm.
- No fearmongering, fake urgency, or deceptive claims.

## Automating on a schedule (optional next step)

This can run on a schedule via GitHub Actions (store the key as a repository
secret named `ANTHROPIC_API_KEY`, never in the workflow file) to publish fresh
articles automatically. Ask and it can be wired up.
