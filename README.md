# initializing-agent-context

A portable skill for coding agents that bootstraps or audits repository context:
a small `AGENTS.md` router, a few durable docs, verified commands, and
deterministic checks.

Works with Kilo, Claude Code, and any agent that reads `AGENTS.md`.

[![CI](https://github.com/johannes3502/initializing-agent-context/actions/workflows/ci.yml/badge.svg)](https://github.com/johannes3502/initializing-agent-context/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Why

Agents lose time when a repository has no entry point, stale commands, or three
competing sources of truth. This skill makes the context small, current, and
checkable: it produces a router instead of a manual, verifies commands instead
of guessing them, and installs a checker so drift becomes visible.

## What it does

| Tool | Purpose |
|---|---|
| `scripts/scan_repo.py` | Read-only inventory: state, units, stacks, manifests, commands, tests, CI, hazards |
| `scripts/check_agent_docs.py` | Links, anchors, required sections, size budgets, ownership, volatile numbers, duplicates, index coverage |
| `scripts/smoke_commands.py` | Extract documented commands, classify them, optionally run only reviewed categories |

The skill is a workflow, not a generator: it picks one of four states (empty,
code without docs, docs without agent context, existing setup), creates only the
files that state needs, then stops.

## Install

The directory name must match `name` in `SKILL.md`.

### Kilo, globally

```bash
git clone https://github.com/johannes3502/initializing-agent-context.git \
  ~/.kilo/skills/initializing-agent-context
```

Windows PowerShell:

```powershell
git clone https://github.com/johannes3502/initializing-agent-context.git `
  "$env:USERPROFILE\.kilo\skills\initializing-agent-context"
```

### Kilo, per project

```bash
git clone https://github.com/johannes3502/initializing-agent-context.git \
  .kilo/skills/initializing-agent-context
```

### Claude Code

```bash
git clone https://github.com/johannes3502/initializing-agent-context.git \
  ~/.claude/skills/initializing-agent-context
```

## Quick start

```bash
SKILL=~/.kilo/skills/initializing-agent-context
python "$SKILL/scripts/scan_repo.py" --root .
python "$SKILL/scripts/check_agent_docs.py" --root . --strict
python "$SKILL/scripts/smoke_commands.py" --root .
```

On Windows use `$env:USERPROFILE\.kilo\skills\initializing-agent-context` and
`python` instead of `python3`.

Ask the agent to read `SKILL.md` and apply it to the repository. The skill
chooses the state and mode, writes the router and docs, and reports verified and
unverified commands.

## Modes

| State | Situation | Mode |
|---|---|---|
| S0 | Empty repository | `bootstrap` |
| S1 | Code, no docs | `archaeology` |
| S2 | Docs, no agent entry point | `adopt` |
| S3 | Existing agent setup | `audit`, then targeted `repair` |

## Safety

- All scripts are read-only; they never modify the inspected repository.
- No network access, no third-party Python packages, Python 3.10+.
- The smoke tool never executes `setup`, `test`, `server`, `dangerous`, or
  unclassified commands by default.
- Review the classification before running a category, especially in untrusted
  repositories.
- Secrets, `.env` files, and customer data are never read or written.

## Repository layout

```text
SKILL.md                 workflow, states, gates
scripts/                 scanner, doc checker, command smoke tool
references/              discovery, states, templates, anti-patterns, profiles
templates/               AGENTS.md, docs index, ADR, checker config
tests/                   unit tests and fixtures
.github/                 CI, release workflow, issue templates
```

## Compatibility

Python 3.10 or newer on Windows, macOS, or Linux. The Markdown and skill
conventions are agent-agnostic; Kilo and Claude Code discovery paths are
documented above.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).
Release steps: [PUBLISHING.md](PUBLISHING.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
