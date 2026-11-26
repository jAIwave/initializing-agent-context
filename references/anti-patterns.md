# Anti-Patterns

Each item names the failure and the fix. Use this list when auditing.

## 1. The monolithic manual

A 400-line `AGENTS.md` that explains the whole system.

**Fix:** keep the root as a router; move detail to `docs/`; link, do not copy.
Budget: 120 lines soft, 180 warning, 260 hard.

## 2. The second README

The agent file repeats install steps, project description, and contribution
guide.

**Fix:** `README.md` is for humans; `AGENTS.md` adds only what the code and
README do not reveal: commands, gotchas, boundaries, verification.

## 3. Generic advice

"Write clean code", "be careful with security", "follow best practices".

**Fix:** replace with a checkable rule: "Never log request bodies", "All money is
integer cents", "Run `pytest tests/auth -q` after auth changes".

## 4. A file per folder

Nested files for `src/`, `utils/`, `components/`.

**Fix:** one file per deployable unit with its own commands or invariants. Root
holds universal rules; unit files are deltas.

## 5. Stale commands

A command that no longer exists, with the wrong working directory, or missing a
required service.

**Fix:** run it. If it cannot run, mark `unverified` with prerequisites. Wire a
smoke check into CI.

## 6. Duplicated facts

The same port, email rule, or test count in root, unit, and docs.

**Fix:** one canonical home; links everywhere else. Generate reference facts.

## 7. Volatile numbers in the router

"312 tests", "Stand 2026-11-25", "Port 8004" in `AGENTS.md`.

**Fix:** replace with a command (`pytest --collect-only -q`) and a link to
`docs/ports.md`.

## 8. Documentation before code

A 200-line architecture doc for an empty repo.

**Fix:** build a walking skeleton and one test first. Document decisions as ADRs
only when they are made.

## 9. Invented rationale

"We use Redis for horizontal scaling" with no ADR, comment, or owner statement.

**Fix:** mark `unknown`; ask the owner; write the answer only when confirmed.

## 10. The file tour

A list of every file and what it contains.

**Fix:** document entry points, boundaries, data flow, and gotchas. The agent can
read files.

## 11. Secrets in the repo

A token, connection string, customer sample, or `.env` content in a doc.

**Fix:** remove it, rotate it if it was real, and add a `Never` rule. Do not
repeat the value in the handover.

## 12. Prose instead of enforcement

"Never commit to main", "Always run the formatter" only in Markdown.

**Fix:** branch protection, hooks, CI, formatter config, permissions. Keep the
line in `AGENTS.md` as a pointer, not the only control.

## 13. One big skill

A skill that explains everything and fires for every task.

**Fix:** scope it to a recognizable moment; write the description as a trigger;
move depth to references; test that it fires and changes the output.

## 14. Docs for generated code

Hand-written docs for generated clients, schema dumps, or build output.

**Fix:** document the generator and the contract; link to generated artifacts.

## 15. Worktree universes

Several stale `AGENTS.md` copies in worktrees, each with different rules.

**Fix:** treat worktrees as disposable; refresh from the root or exclude them
from the agent context; never edit a worktree copy as the source of truth.

## 16. The giant first pass

Twenty new docs in one change, none verified.

**Fix:** first pass maximum 4 files (or 2 + units, hard cap 8). Expand on demand.
