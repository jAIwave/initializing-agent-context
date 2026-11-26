---
name: initializing-agent-context
description: Initializes or repairs agent-facing repository context for any codebase, including empty repos, undocumented code, monorepos, mixed stacks and docs-only repositories. Use when a repo has no AGENTS.md or CLAUDE.md, docs are missing or stale, an agent gets lost or runs wrong commands, or an existing agent setup should be audited and made verifiable.
compatibility: Python 3.10+ on Windows, macOS or Linux. Read-only scripts; no third-party packages.
license: MIT
metadata:
  version: "1.1.0"
---

# Initializing Agent Context

Build the smallest repository context that lets a coding agent find the entry
point, run the right command, respect the hard boundaries, and verify its work.
This is a setup skill, not a documentation generator: it produces a router, a
few durable docs, and a feedback loop, then stops.

## When to use

- A repository has no `AGENTS.md`, `CLAUDE.md`, or equivalent agent entry file.
- The codebase has no durable docs, or docs exist but are stale, duplicated, or
  disconnected from the code.
- An agent repeatedly opens irrelevant files, runs the wrong test command, or
  misses a project-specific invariant.
- An existing agent setup should be audited: size, required sections, links,
  ownership dates, duplicate facts, stale commands.
- A monorepo has several deployable units with different stacks and commands.
- A docs-only repository needs a workflow router and content boundaries.

## When not to use

- A one-off explanation or code question. Read the repo directly.
- A request to rewrite an entire documentation set. This skill is incremental.
- A repository where you have no permission to write. Use it in audit mode and
  return a plan instead.
- A repo where a different agent convention already works and is maintained.
  Audit and improve it; do not replace it with a competing file.

## Non-negotiables

1. **Read-only discovery first.** Never write during inventory. Never read
   `.env` contents, secrets, credentials, or customer data. Listing env file
   names is fine; opening them is not.
2. **Evidence over invention.** Every command, path, invariant, and owner claim
   is either verified in this session, inferred from a named file, or marked
   `unknown`. Do not invent architecture rationale.
3. **Minimal viable context.** Every line must answer a question the agent would
   otherwise get wrong. If removing a line changes nothing, remove it.
4. **Root is a router.** The root `AGENTS.md` holds the map, universal commands,
   hard boundaries, and links. Detail belongs in `docs/`.
5. **Nested files are deltas.** One `AGENTS.md` per deployable unit with its own
   commands or invariants, not per folder. A unit file never repeats the root.
6. **Commands must run.** A documented command is a claim. Run it or mark it
   `unverified` with its prerequisites.
7. **One fact, one home.** Duplicates are replaced by links. Generated facts
   (routes, env names, schema, test inventory) are generated or single-sourced.
8. **Guardrails over prose.** What must always or never happen belongs in a
   checker, CI, hooks, or permissions, not only in a paragraph.
9. **Respect the existing setup.** If `CLAUDE.md`, Cursor rules, or docs already
   exist, adopt them. Use `AGENTS.md` as the shared source and point other files
   at it instead of copying rules.
10. **Idempotent.** Re-running the skill audits and proposes diffs. It never
    regenerates a maintained file from scratch.

## Modes

Detect the mode first; do not ask the user to choose unless the repository is
ambiguous.

| Mode | Detect | Goal |
|---|---|---|
| `bootstrap` | No code, no manifests (S0) | Decisions + walking skeleton + minimal router |
| `archaeology` | Code, no durable docs (S1) | Read the code, build a fact sheet, write 3 core docs |
| `adopt` | Code + docs, no agent entry (S2) | Derive the router from docs, verify against code |
| `audit` | `AGENTS.md`/`CLAUDE.md` exists (S3) | Fix gaps, duplication, size, stale commands |
| `repair` | Existing setup is drifted or broken | Targeted fixes only; no rewrite |

For a monorepo, run the mode per unit and keep the root at `bootstrap` or
`adopt` level. For a docs-only repo, use `archaeology` with the docs-only
profile.

## Examples

**Empty repository.** `scan_repo.py` returns S0. Read
`references/state-empty.md`. Ask the five questions, record open decisions, then
create a walking skeleton and at most four files. Do not write architecture
prose.

**Code without docs.** The scanner returns S1 and lists units and a suggested
test command. Read `references/state-undocumented.md`. Run the focused test,
build the fact sheet, then write `AGENTS.md`, `docs/architecture.md`,
`docs/testing.md`.

**Existing setup.** The scanner returns S3 and lists every agent file. Run
`check_agent_docs.py --strict --duplicates`, read `references/state-audit.md`,
and fix links, commands, duplication, size, and boundaries in that order.

**Monorepo.** The scanner returns several units. Read
`references/state-monorepo.md`. Keep the root as a map; add unit files only for
units with their own commands or invariants.

**Docs-only repo.** The scanner marks the profile as docs-only. Read
`references/profiles/docs-only.md`. The router is a workflow and content
boundary, not a code map.

## Workflow

### Phase 0 - Scope and safety

1. Resolve the repository root. If run inside a submodule, treat that submodule
   as the repo; the umbrella root is only a map.
2. Record the write scope and whether the user asked for a plan or an
   implementation.
3. Note excluded paths: generated output, vendored code, worktrees, secrets,
   build artifacts, `node_modules`, virtualenvs.
4. If write access is not granted, stop after Phase 2 and return the file plan.

Output: a short scope contract (root, excluded paths, write permission).

### Phase 1 - Inventory

Run the scanner; do not duplicate its work by hand.

```bash
SKILL=.kilo/skills/initializing-agent-context
python "$SKILL/scripts/scan_repo.py" --root .
```

PowerShell:

```powershell
$SKILL = ".kilo/skills/initializing-agent-context"
python "$SKILL/scripts/scan_repo.py" --root .
```

> `SKILL` is the directory that contains this `SKILL.md`. For a globally
> installed skill, point it at that location instead. The scripts only read the
> target repository; they never write to it.

Use `--json` when you need to process the result. For a monorepo, run the
scanner once at the root, then again per unit if a unit is large or ambiguous.

Read, in this order:

1. `README.md`, existing `AGENTS.md`/`CLAUDE.md`, `CONTRIBUTING.md`.
2. Manifests and lockfiles: stack, package manager, scripts, engines.
3. Entry points: app/server/main/index, routes, CLI, workers, cron.
4. Tests and test config: the fastest focused verification command.
5. Lint/typecheck/format config.
6. CI and deploy files.
7. DB/schema/migrations.
8. Env file names (never contents).
9. Git history for hot files and repeated fixes.
10. `docs/` or `doc/`, `plans/`, `docs/adr/` if present.

Cross-check the README quickstart against the manifests and entry points. Stale
hosts, ports, package managers, and start commands are common; the code and
config are authoritative.

Record a fact sheet:

| Claim | Evidence | Confidence |
|---|---|---|
| Test command is `python -m pytest tests/ -q` | `server/AGENTS.md:51`, `tests/conftest.py` | verified |
| Deploy uses systemd + nginx | `deploy/*.service`, `nginx/` | inferred |
| Why Redis exists | no ADR, no comment | unknown |

`verified` means you ran it or read the exact source. `inferred` means the code
strongly implies it. `unknown` means do not write it as fact.

Stop condition: if the repo is too large to inventory in one pass, narrow to the
unit the user asked about and state the narrowed scope.

### Phase 2 - Decide the topology

Choose the smallest set of files that satisfies the workflow:

- **Always:** root `AGENTS.md` (create or repair).
- **If docs exist:** link them from `Read next`; do not rewrite them.
- **If no docs:** create `docs/README.md` plus at most two of
  `docs/architecture.md`, `docs/testing.md`, `docs/operations.md`.
- **If a unit has its own commands or invariants:** one unit `AGENTS.md`.
- **If a procedure is long:** a skill or command, not the router.
- **If history is relevant:** `plans/` or ADRs, not `AGENTS.md`.

First-pass write budget:

| Repo shape | New or heavily edited files |
|---|---|
| Empty repo | 4 maximum |
| Single-unit repo | 4 maximum |
| Monorepo | 2 + one per unit, hard cap 8 |

If the plan exceeds the budget, cut docs, not the verification loop.

Output: a file plan.

```text
CREATE  AGENTS.md                 root router
CREATE  docs/README.md            docs index
CREATE  docs/testing.md           commands and fixtures
UPDATE  README.md                 link to AGENTS.md and docs/
LEAVE   docs/architecture.md      existing, verified
```

### Phase 3 - Author

Use `templates/AGENTS.root.md` and `templates/AGENTS.unit.md` as shapes, not as
text to copy blindly. Fill every placeholder with evidence from Phase 1.

Root file rules:

- One paragraph of purpose and scope.
- A `Start here` table: task -> read first -> verify with.
- A unit map for monorepos, or a key-files list for single units.
- Commands with working directory, prerequisites, single-test and full-check
  variants.
- 5-10 hard invariants, each with an evidence link.
- `Ask first` and `Never` boundaries.
- Definition of done: which commands prove the change.
- `Read next` links to docs.
- `Ownership`: owner, last reviewed, review by.

Unit file rules:

- Scope and parent link.
- Only delta commands, delta invariants, key files, read-next, ownership.
- No repetition of root commands or rules.

Docs rules:

- `README.md` is for humans: purpose, install, run, where the code lives.
- `docs/` is the current truth: architecture, testing, operations, security.
- `plans/` is dated history. `docs/adr/` holds durable decisions.
- Never put test counts, ports, or endpoint lists in several places.

If a command cannot be run because the environment is missing, write it as
`unverified` with the prerequisite. Never present a guessed command as verified.

### Phase 4 - Add guardrails

Install a checker that makes drift visible (run from the repo root with `$SKILL`
set as in Phase 1):

```bash
python "$SKILL/scripts/check_agent_docs.py" --root . --strict
python "$SKILL/scripts/smoke_commands.py" --root .
```

The checker covers links, anchors, repo boundaries, required sections, size,
ownership dates, volatile numbers, parent/child index coverage, and optional
duplicate facts. It skips site-absolute links (`/docs/...`) and reports
mojibake. It reads `.agent-docs.json` from the repo root; use it to add nested
doc dirs to `include` and published/generated paths to `exclude` (path globs),
and to map intentional non-English headings via `section_aliases`. Start from
`templates/agent-docs.example`.
The smoke tool extracts documented commands; review the classification, then
run only a category you inspected. Setup, test, and server commands stay manual
unless their category is explicitly requested.

Wire the checker into one of:

- CI (preferred),
- a pre-commit hook,
- the existing test suite,
- a documented `docs:check` script.

If the repo has no tests, the first guardrail is a walking-skeleton test, not a
docs checker.

### Phase 5 - Verify

Run in this order:

1. `check_agent_docs.py --strict` and fix errors.
2. Run every documented command that is safe. Record pass/fail.
3. Run the focused test command and the full check if time permits.
4. Cold-start test: in a fresh session or subagent, ask "Where do I change X and
   which test proves it?" without naming paths. The setup passes if the agent
   finds the router, the unit doc, and the focused test without correction.
5. Check the always-on size: root <= 120 lines soft, <= 180 warning, <= 260 hard.
6. Check that no secret, token, customer data, or volatile count was written.

If a gate fails, fix the file or report the failure. Do not mark the setup done
because the Markdown looks good.

### Phase 6 - Hand over

Return a short report:

```text
Created:   AGENTS.md, docs/README.md, docs/testing.md
Updated:   README.md (links)
Verified:  pytest --collect-only; focused test; docs check
Inferred:  deploy topology (deploy/*.service, nginx/)
Unknown:   why the legacy worker exists; no ADR
Next:      docs/architecture.md after the next feature; CI wiring
Review:    2027-05-25
```

State the boundaries you did not cross: no secrets read, no destructive command
run, no existing doc rewritten.

## The three hard cases

### Empty repository

Do not invent an architecture. Do this instead:

1. Ask only what code cannot answer: purpose, stack constraints, deploy target,
   owner, non-negotiables. If the user does not answer, record a decision
   backlog instead of guessing.
2. Create a walking skeleton as soon as the stack is known: one entry point, one
   test, one command that runs it.
3. Create at most four files: `README.md`, `AGENTS.md`, optional
   `docs/adr/0001-stack.md`, and `.gitignore`/`.editorconfig` if missing.
4. Mark everything as `provisional`. Review after the first real feature.
5. Put stack choices under `Ask first` until they are decided.

The highest-value output in an empty repo is a feedback loop, not prose.

### Codebase without docs

Run archaeology, not imagination:

1. Manifests -> stack, package manager, scripts.
2. Entry points -> public surface.
3. Routes/CLI/events -> behavior.
4. Tests -> intended behavior and fixtures.
5. Config/env names -> runtime assumptions.
6. DB/schema/migrations -> data model and hazards.
7. CI/deploy -> how it actually runs.
8. Git history -> hot files and recurring fixes.

Then:

- Generate reference facts where possible: routes, env names, schema, test
  inventory.
- Hand-write only the architecture rationale, boundaries, and gotchas.
- Start with `AGENTS.md`, `docs/architecture.md`, `docs/testing.md`.
- Use `verified` / `inferred` / `unknown` inline or in an appendix.
- Interview the owner only for the "why" that the code cannot reveal.

Do not document every file. Entry points, boundaries, and data flow are enough.

### Mixed stack or monorepo

1. Detect units by manifests and deployables, not by folder depth.
2. Root: unit map, universal rules, orchestrator commands, cross-unit contracts.
3. Unit: delta commands, delta invariants, key files, own hazards.
4. Use the tech profiles in `references/profiles/` only for discovery. They are
   not tutorials and should not be copied into the repo.
5. Put cross-unit contracts in one canonical doc; root links to it.
6. Keep packages flat and domain-named where the repo allows it. Do not nest a
   unit inside another unit's `src/`.

### Docs-only repository

Use the docs-only profile:

- `AGENTS.md` is a workflow router (where tasks live, what to read, how to
  verify), not a code map.
- Invariants are content rules: no PII in git, no unreviewed claims, no silent
  price changes, archive instead of delete.
- Verification is a link/anchor check plus a manual review checklist.
- One task list, stable IDs, and a clear "done" definition.

## Output contract

The skill is done when:

- a root `AGENTS.md` exists and is a router, not an encyclopedia,
- every unit with its own commands has a delta file,
- commands are verified or explicitly marked,
- the docs checker passes (or its failures are reported),
- the cold-start test passes,
- the handover report lists created/updated/verified/inferred/unknown,
- the maintenance contract (owner, review date, growth rule) is in place.

The skill is not done when only Markdown was written.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/scan_repo.py` | Read-only fact sheet: state, units, stacks, commands, tests, docs, CI, hazards |
| `scripts/check_agent_docs.py` | Links, anchors, required sections, size, ownership, duplicates, index coverage |
| `scripts/smoke_commands.py` | Extract and optionally run documented commands; never runs dangerous ones |

All scripts accept `--root`, `--json` where useful, and never write to the repo.
They require Python 3.10+; use `python3` if `python` is not on PATH.

## Quality gates

- Root `AGENTS.md`: <= 120 lines target, 180 warning, 260 hard.
- Unit `AGENTS.md`: <= 100 lines target, 220 warning, 260 hard.
- Every command: run this session or marked `unverified`.
- Every invariant: evidence (`path:line`, test, config) or marked as assumption.
- Every relative link resolves; no relative link escapes the repo.
- No secrets, PII, test counts, or volatile port tables in the router.
- Nested files only with a delta justification.
- Checker wired into CI, pre-commit, or the test suite.
- Cold-start test passes.

## References

Read only the reference you need:

- `references/discovery-checklist.md` - exact discovery commands and evidence table.
- `references/state-empty.md` - bootstrap for an empty repo.
- `references/state-undocumented.md` - archaeology for a repo without docs.
- `references/state-monorepo.md` - units, root/delta split, orchestrators.
- `references/state-audit.md` - audit rubric and repair order.
- `references/document-templates.md` - section-by-section guidance and examples.
- `references/anti-patterns.md` - what to avoid and the fix.
- `references/profiles/` - Python, Node, Go, Rust, JVM, .NET, PHP, Ruby, infra,
  docs-only, and a generic fallback.

## Maintenance

- Add a nested file only when a unit gains its own commands or invariants.
- Update the owning doc in the same change as the behavior change.
- Re-run the checker in CI; review ownership dates at least yearly.
- Prune quarterly: archive stale plans, replace duplicates with links, delete
  lines that no longer change agent behavior.
- When an agent repeats a mistake, add one boundary line or one test; do not
  grow the router with prose.
