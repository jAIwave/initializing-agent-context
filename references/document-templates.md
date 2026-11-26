# Document Templates and Writing Rules

The templates in `templates/` are shapes. Replace every placeholder with a
verified fact. Delete any section that does not change agent behavior.

## Root `AGENTS.md`

Purpose: a router injected into every session. Target 80-120 lines.

### Required shape

````markdown
# <Repo> - Agent Context

> <One or two sentences: what this repo is, what it deploys, what it does not.>
> Router only: detail in `docs/`, history in `plans/`, decisions in `docs/adr/`.

## Start here

| If you ... | Read first |
|---|---|
| ... | ... |

## Units

| Path | Purpose | Stack | Entry | AGENTS |
|---|---|---|---|---|

## Commands

```bash
# from <workdir>
<install>
<dev>
<test single>
<test all>
<lint>
<typecheck>
<build>
```

> Prereqs: <runtime, package manager, env, OS notes>

## Hard invariants

- **<Area>**: <checkable rule>. Evidence: `path:line`.

## Ask first

- ...

## Never

- ...

## Definition of done

- Run <command>; report the command and result.
- ...

## Read next

| Topic | Doc |
|---|---|

## Ownership

Owner: <name/team> | Last reviewed: YYYY-MM-DD | Review by: YYYY-MM-DD
````

### Rules

- `Start here` is task-oriented, not topic-oriented: "If you change auth" beats
  "Security".
- Commands are copy-pasteable, with working directory and prerequisites.
- Include the focused test, not only the full suite.
- Invariants are checkable. "Never log request bodies" is checkable; "be
  careful" is not.
- `Ask first` / `Never` are the highest-value boundaries. Put the expensive
  mistakes there.
- `Definition of done` names the evidence, not the feeling.
- Link to docs; do not paste them.

## Unit `AGENTS.md`

Purpose: the delta for one deployable unit. Target 40-100 lines.

````markdown
# <Unit> - Agent Context (delta)

> Scope: <what this unit owns>. Parent: `../AGENTS.md`.
> This file only states what differs from the parent.

## Commands

```bash
# unit-specific commands, workdir, prereqs
```

## Delta invariants

- ...

## Key files

| File | Purpose |
|---|---|

## Read next

| Topic | Doc |
|---|---|

## Ownership

Owner: ... | Last reviewed: ... | Review by: ...
````

Rules:

- Do not repeat root commands or rules.
- Link the parent at the top.
- Keep only what changes inside this unit.
- If the file would be identical to the parent, delete it.

## `docs/README.md`

Purpose: docs index and maintenance rules.

- Document types: current truth vs history vs decisions.
- Index: architecture, testing, operations, security, ADRs.
- Rules: one fact one home; no volatile counts; links stay in the repo.
- Check command.

## `docs/architecture.md`

Purpose: why the system is shaped this way, and where behavior should change.

- System purpose and users.
- Deployable units and responsibilities.
- Data flow and storage.
- External dependencies.
- Boundaries: allowed and forbidden calls.
- Known hazards.
- Open questions, explicitly marked.

Keep it stable. It should not become a file tour.

## `docs/testing.md`

Purpose: how to prove a change.

- Test layers and what each covers.
- Exact commands: one test, one file, full suite, E2E.
- Required services, env, fixtures, test data.
- Known flaky tests and why.
- What CI runs.
- What cannot be tested locally.

## `docs/operations.md`

Purpose: run and deploy.

- Environments and URLs.
- Deploy command and prerequisites.
- Migrations and backup rules.
- Health checks and rollback.
- Secrets source (name, never value).
- On-call/owner.

## `docs/security.md`

Purpose: the security contract.

- Auth model (cookie, token, session).
- CSRF/CORS/origin rules.
- RBAC and service access.
- Secrets handling.
- PII and logging rules.
- Threat assumptions and open risks.

Use only if the repo has auth, payments, PII, or privileged operations.

## ADR (`docs/adr/NNNN-title.md`)

```markdown
# NNNN - <Decision>

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Owner: ...
- Supersedes: ...

## Context

## Decision

## Consequences

## Alternatives
```

An ADR records a decision, not a tutorial. One decision per file.

## Language and style

- Use the repository's language. If docs are German, write German; keep code,
  commands, and filenames in English.
- Use short sentences and tables for routing.
- Use code fences with a language tag.
- Use `path:line` for evidence.
- Prefer one authentic command or snippet over three paragraphs.
- Do not add emojis, slogans, or motivational text.

## Length budgets

| File | Target | Warning | Hard |
|---|---:|---:|---:|
| Root `AGENTS.md` | 80-120 | 180 | 260 |
| Unit `AGENTS.md` | 40-100 | 220 | 260 |
| `docs/architecture.md` | open | - | - |
| ADR | 1 page | - | - |

If a file grows past the warning, move detail to a topic doc and leave a link.

## Good vs bad

Bad:

```markdown
## Architecture
The backend is built with FastAPI. It has many services. The code is organized
in folders. Please be careful when changing things.
```

Good:

```markdown
## Architecture
- `auth/` owns JWT, cookies, CSRF, and role changes.
- `services/lager/` owns stock, sync, and CSV export.
- All services share `db/` and `shared/`; no service imports another service's
  internals.
- Evidence: `server/docs/architecture.md`, `server/db/AGENTS.md`.
```

Bad:

```markdown
Run the tests.
```

Good:

````markdown
```bash
cd server
python -m pytest tests/lager/test_sync.py -q   # focused
python -m pytest tests/ -q                      # full
```
````
