# State: Monorepo and Mixed Stacks

The root is a map; each deployable unit carries its own delta. Do not create one
`AGENTS.md` per folder.

## 1. Detect units

A unit is something that can be built, tested, deployed, or owned on its own:

- a service with its own entry point,
- an app with its own manifest and build,
- a package with its own public API,
- a worker or scheduled job,
- a deployable infra stack.

Detection signals:

- `package.json` with scripts or `workspaces`,
- `pyproject.toml` / `requirements.txt`,
- `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `*.csproj`,
- `Dockerfile`, `compose.yaml`, `*.service`, `Chart.yaml`,
- `vite.config.*`, `next.config.*`, `manage.py`, `app.py`, `main.go`.

Use `scripts/scan_repo.py`; it lists unit candidates and their commands.

## 2. Root file

Keep the root under ~120 lines:

- Purpose of the monorepo.
- Unit map:

  | Path | Purpose | Stack | Entry | AGENTS |
  |---|---|---|---|---|
  | `apps/api` | Public API | Python/FastAPI | `app.py` | `apps/api/AGENTS.md` |
  | `apps/web` | Customer UI | React/Vite | `src/main.tsx` | `apps/web/AGENTS.md` |
  | `packages/ui` | Shared components | React | `src/index.ts` | `packages/ui/AGENTS.md` |

- Universal commands (install, orchestrated test, full check).
- Universal rules: secrets, lockfiles, commit style, cross-unit contracts.
- Task routing for cross-cutting work.
- A link to the operational runbook (usually `README.md`); do not paste deploy
  commands if the README owns them.
- Read next and ownership.

Do not repeat unit commands in the root. Link them.

## 3. Unit file

Only the delta:

- Scope and parent link.
- Commands not already in the root.
- Invariants specific to this unit.
- Key files and entry points.
- Hazards: migrations, auth, money, generated code, long-running jobs.
- Read next and ownership.

If a unit file only repeats the root, delete it.

## 4. Command layers

| Layer | Command style |
|---|---|
| Root | Orchestrator: `make test`, `turbo run test`, `nx run-many`, `pnpm -r test`, `docker compose ...` |
| Unit | Native: `pytest`, `vitest`, `go test ./...`, `cargo test`, `dotnet test` |

Document both, and say which one is the fast loop. The root command is for the
full gate; the unit command is for iteration.

## 5. Tech profiles

Use `references/profiles/` only to know what to look for. Each profile gives:

- manifests and package manager,
- entry points,
- test/lint/type commands,
- common invariants and hazards.

Do not copy a profile into the repo. Write only the facts that are true here.

## 6. Cross-unit contracts

A contract that spans units belongs in one canonical place:

- API schema / OpenAPI file,
- shared types package,
- event schema,
- auth/CSRF contract,
- database ownership.

The root links to it. Each unit links to the same source. Never copy the contract
into every unit file.

## 7. Example split

```text
AGENTS.md                       map, universal rules, orchestrator commands
apps/api/AGENTS.md              FastAPI delta: migrations, auth, test command
apps/web/AGENTS.md              React delta: build, E2E, env prefix, no secrets
packages/ui/AGENTS.md           shared package delta: public API, no app imports
infra/AGENTS.md                 deploy delta: plan only, never apply without approval
docs/README.md                  docs index
docs/architecture.md            system map and boundaries
docs/testing.md                 how to test each layer
```

## 8. Common mistakes

- One root file that documents every package.
- A nested file for every `src/` folder.
- Copying the same command into five unit files.
- Assuming units share virtualenv names, install paths, or env directories;
  verify each unit's scripts and service files.
- Hiding the fast test command behind a slow root command.
- Letting packages import each other through relative paths outside their public
  API.
- Documenting generated clients as if they were source.

## Done criteria

- Every deployable unit has a card in the root map.
- Only units with real deltas have their own file.
- The fast loop is discoverable per unit.
- Cross-unit contracts have one home.
- The root stays under its size budget.
