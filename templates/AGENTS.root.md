# <Repo> - Agent Context

> <One or two sentences: what this repo is, what it deploys, and what it does not own.>
> Router only: details live in `docs/`, history in `plans/`, decisions in `docs/adr/`.

## Start here

| If you ... | Read first |
|---|---|
| want the system overview | [`docs/architecture.md`](docs/architecture.md) |
| change auth/security | [`docs/security.md`](docs/security.md) |
| change data or migrations | [`docs/architecture.md`](docs/architecture.md), `<db doc>` |
| write or run tests | [`docs/testing.md`](docs/testing.md) |
| deploy or operate | [`docs/operations.md`](docs/operations.md) |
| add a new unit | `<unit guide>` |

## Units

| Path | Purpose | Stack | Entry | AGENTS |
|---|---|---|---|---|
| `<path>` | `<purpose>` | `<stack>` | `<entry>` | `<path>/AGENTS.md` |

> Remove this table for a single-unit repo and replace it with a short key-files
> list. Do not invent units.

## Commands

```bash
# from <workdir>
<install>
<dev>
<test single>       # focused test; the fast loop
<test all>          # full check
<lint>
<typecheck>
<build>
```

> Prereqs: <runtime versions, package manager, services, env, OS notes>.
> Mark anything you could not run as `unverified` with the missing prerequisite.

## Hard invariants

- **<Area>**: <checkable rule>. Evidence: `path:line`.
- **<Area>**: <checkable rule>. Evidence: `path:line`.
- **<Area>**: <checkable rule>. Evidence: `path:line`.

## Ask first

- Changing <auth / billing / schema / public API / CI / deploy>.
- Adding a dependency, service, or background job.
- Running a migration or any command against production.

## Never

- Commit `.env`, tokens, keys, customer data, or credentials.
- Run destructive migrations or deploys without the documented gate.
- Edit generated or vendored files by hand.
- Copy an old pattern that this file marks as deprecated.

## Definition of done

- Run <focused test> and <full check>; report the commands and results.
- If a check cannot run, state why and what remains unverified.
- Update the owning doc in the same change as the behavior change.

## Read next

| Topic | Doc |
|---|---|
| Architecture and boundaries | [`docs/architecture.md`](docs/architecture.md) |
| Testing and fixtures | [`docs/testing.md`](docs/testing.md) |
| Operations and deploy | [`docs/operations.md`](docs/operations.md) |
| Decisions | [`docs/adr/`](docs/adr/) |

> Remove rows for documents this repo does not have. Do not link to a file you
> have not created.

## Ownership

Owner: `<name/team>` | Last reviewed: `YYYY-MM-DD` | Review by: `YYYY-MM-DD`
