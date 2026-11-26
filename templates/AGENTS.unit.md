# <Unit> - Agent Context (delta)

> Scope: <what this unit owns and what it does not>.
> Parent: [`../AGENTS.md`](../AGENTS.md). Adjust the relative path for deeper
> units. Root rules still apply.
> This file only states what differs from the parent.

## Commands

```bash
# from <workdir>
<unit install>
<unit dev>
<unit test single>   # focused
<unit test all>      # full
<unit lint>
<unit typecheck>
<unit build>
```

> Prereqs: <services, env, fixtures, OS notes>.

## Delta invariants

- **<Area>**: <checkable rule>. Evidence: `path:line`.
- **<Area>**: <checkable rule>. Evidence: `path:line`.

## Key files

| File | Purpose |
|---|---|
| `<entry>` | <what it owns> |
| `<config>` | <what it controls> |
| `<schema/migration>` | <what it changes> |

## Hazards

- <migration/backfill/auth/PII/long-running job/third-party API>.
- <what must never be changed without approval>.

## Read next

| Topic | Doc |
|---|---|
| <topic> | `<path>` |

## Ownership

Owner: `<name/team>` | Last reviewed: `YYYY-MM-DD` | Review by: `YYYY-MM-DD`
