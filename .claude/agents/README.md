# Agency Agents (Claude Code subagents)

This directory contains specialist AI agent personas installed for use with
Claude Code. Each `*.md` file is a standalone subagent with YAML frontmatter
(`name`, `description`) followed by its persona/instructions.

## Provenance

- **Source:** https://github.com/msitarzewski/agency-agents
- **Source commit:** `ebe9c99acb5c96f9468de368d8bead775387d1a7`
- **License:** MIT (see `LICENSE` in this directory)
- **Installed:** 2026-08-11

## How these were installed

The agent markdown files were copied directly from the source repository's
division folders into `.claude/agents/`. The upstream `scripts/install.sh` was
**not** executed — files were reviewed and copied manually instead.

## Usage

Invoke an agent in Claude Code by asking for it by name, e.g.:

> Use the Frontend Developer agent to review this component.

To remove them, delete the corresponding `*.md` files from this directory.
