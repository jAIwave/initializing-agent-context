# State: Code Without Docs (S1)

The repository has code but no durable documentation. Read the code; do not
imagine the rationale. The output is a small set of verified facts, not a book.

## Archaeology order

1. **Manifests and lockfiles** -> stack, package manager, scripts, engines.
2. **Entry points** -> what actually runs.
3. **Routes, CLI commands, events, jobs** -> public surface.
4. **Tests** -> intended behavior, fixtures, test data, skipped tests.
5. **Configuration and env names** -> runtime assumptions (never contents).
6. **DB, schema, migrations** -> data model and destructive hazards.
7. **CI and deploy** -> what "done" means and how it ships.
8. **Git history** -> hot files, repeated fixes, reverted patterns.
9. **Existing docs/plans** -> current truth vs history; date every plan.
10. **README defaults** -> cross-check hosts, ports, versions, and start
    commands against manifests, config classes, and entry points. Stale
    quickstarts are common; code and config win.

Use `references/discovery-checklist.md` for commands. Use
`scripts/scan_repo.py` for the first pass.

## Build a fact sheet

For each deployable unit:

| Field | Example |
|---|---|
| Path | `server/` |
| Purpose | FastAPI services for auth and booking |
| Stack | Python 3.12, FastAPI, PostgreSQL |
| Package manager | `uv` (uv.lock) |
| Entry points | `auth/app.py`, `services/lager/app.py` |
| Dev command | `python -m website.app` (verified) |
| Focused test | `pytest tests/lager/test_sync.py -q` (verified) |
| Full check | `pytest tests/ -q` (verified) |
| Lint/typecheck | none configured (finding) |
| Data | PostgreSQL; migrations in `db/pg/migrations/` |
| Deploy | systemd + nginx (inferred from `deploy/`) |
| Hazards | auth, migrations, email |
| Owner | unknown (no CODEOWNERS) |
| Confidence | verified / inferred / unknown per row |

Add evidence: `path:line` or the command you ran.

## Generated vs curated

Generate or single-source reference facts:

- routes and CLI commands,
- env variable names,
- DB schema or table list,
- test inventory,
- package scripts.

Hand-write only:

- why the structure exists,
- boundaries and ownership,
- invariants that the code cannot express,
- gotchas and known hazards,
- "do not copy this old pattern" notes.

If a fact can be regenerated, link to the generator or the canonical file. Do not
copy it into three docs.

## The three core docs

Start with these; add more only when a task needs them.

### `AGENTS.md`

- Purpose and scope.
- Start here: task -> read first -> verify.
- Unit map or key files.
- Commands: workdir, prerequisites, focused test, full check.
- 5-10 invariants with evidence.
- Ask first / Never.
- Definition of done.
- Read next.
- Ownership.

### `docs/architecture.md`

- What the system does.
- Deployable units and their responsibilities.
- Data flow and storage.
- External dependencies.
- Boundaries: what may call what.
- Known hazards.
- Open questions, explicitly marked.

### `docs/testing.md`

- Test layers (unit, integration, E2E).
- Exact commands and working directories.
- Required services, env, fixtures, test data.
- How to run one test file, one test, one E2E path.
- Known flaky tests and why.
- What CI runs.

Optional, only if applicable: `docs/operations.md` (deploy/runbook),
`docs/security.md` (auth/PII/secrets), `docs/api.md` (contract).

## Interview only for the "why"

Ask the owner only where the code cannot answer:

- Why this database/queue/provider?
- Which behavior is intentionally weird?
- What must never be changed without approval?
- Which old pattern must not be copied?

Record answers as `inferred` until confirmed, then as `verified` with the source.

## Verification

- Run the focused test command and the full check.
- Run `--help` for CLI tools.
- Check the docs checker.
- If the environment is missing, write prerequisites and mark commands
  `unverified`.
- Do not claim a deploy process works because a file exists.

## Example: small API

```text
AGENTS.md
  Commands: uv sync; uv run pytest tests/test_api.py -q; uv run pytest -q
  Invariants: all handlers validate at the boundary; money is integer cents;
              migrations are additive and never edited after apply.
  Ask first: schema changes, auth middleware, dependency additions.
  Never: commit .env, run migrations against production.

docs/architecture.md
  One service, one Postgres schema, one background worker.
  Request -> validation -> service -> repository -> Postgres.
  Worker consumes the same queue; no direct DB access from the web tier.

docs/testing.md
  Unit tests use an in-memory DB; integration tests require Postgres on 5433.
  Focused: uv run pytest tests/test_orders.py -q
  Full: uv run pytest -q
  E2E: requires the local stack; see scripts/dev.sh.
```

## Done criteria

- A new agent can find the entry point and the focused test from `AGENTS.md`.
- Every command was run or is marked `unverified`.
- Invariants have evidence.
- Unknowns are listed, not hidden.
- No doc duplicates a fact that lives in code or another doc.

## Anti-patterns

- A file-by-file tour of the repository.
- Guessing why a dependency exists.
- Documenting generated code.
- Turning a plan into current truth without verifying it.
- Writing ten docs before running one test.
