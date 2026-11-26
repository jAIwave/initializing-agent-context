# <Repo> - Documentation

> Current truth for architecture, testing, operations, and security.
> [`AGENTS.md`](../AGENTS.md) is the agent router; [`plans/`](../plans/) is
> dated history; [`adr/`](adr/) holds durable decisions.

## Document types

| Type | Location | Purpose |
|---|---|---|
| Agent router | [`AGENTS.md`](../AGENTS.md), unit `AGENTS.md` | Map, commands, boundaries, links |
| Current truth | `docs/` | Architecture, testing, operations, security |
| History | `plans/` | Dated plans; can be stale |
| Decisions | `docs/adr/` | One decision per file |
| Human entry | [`README.md`](../README.md) | Purpose and quickstart |

## Index

| Document | Content |
|---|---|
| [`architecture.md`](architecture.md) | Units, data flow, boundaries, hazards |
| [`testing.md`](testing.md) | Commands, fixtures, layers, CI |
| [`operations.md`](operations.md) | Deploy, migrations, health, rollback |
| [`security.md`](security.md) | Auth, CSRF, RBAC, secrets, PII |
| [`adr/`](adr/) | Durable decisions |

> Remove rows for documents this repo does not have.

## Maintenance rules

1. One fact, one home. A summary links to the canonical doc.
2. No volatile test counts, port tables, or endpoint lists in `AGENTS.md`.
3. History stays in `plans/`; current truth stays in `docs/`.
4. A behavior change updates the owning doc in the same change.
5. Relative links stay inside the repo; cross-repo links use stable URLs.
6. Run the docs check before considering the change done:

```bash
python scripts/check_agent_docs.py --root . --strict
```

## Ownership

Owner: `<name/team>` | Last reviewed: `YYYY-MM-DD` | Review by: `YYYY-MM-DD`
