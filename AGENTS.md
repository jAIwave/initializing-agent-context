# initializing-agent-context - Agent Context

> Public, dependency-free skill that bootstraps or audits agent documentation
> (`AGENTS.md`, `CLAUDE.md`, docs, checkers) for any repository.

## Start here

| If you ... | Read first |
|---|---|
| use the skill on another repository | [`SKILL.md`](SKILL.md), [`references/state-audit.md`](references/state-audit.md) |
| change the scanner | [`scripts/scan_repo.py`](scripts/scan_repo.py), [`tests/test_scan_repo.py`](tests/test_scan_repo.py) |
| change the documentation checker | [`scripts/check_agent_docs.py`](scripts/check_agent_docs.py), [`tests/test_check_agent_docs.py`](tests/test_check_agent_docs.py) |
| change command classification | [`scripts/smoke_commands.py`](scripts/smoke_commands.py), [`tests/test_smoke_commands.py`](tests/test_smoke_commands.py) |
| edit templates, profiles, or states | [`templates/`](templates/), [`references/`](references/) |
| publish or release | [`PUBLISHING.md`](PUBLISHING.md), [`CHANGELOG.md`](CHANGELOG.md) |

## Commands

```bash
python -m unittest discover -s tests -v
python scripts/check_agent_docs.py --root . --strict
python scripts/scan_repo.py --root .
python scripts/smoke_commands.py --root .
```

The smoke tool extracts documented commands only; review the classification
before executing a category.

## Hard invariants

- **Zero dependencies, read-only scripts**: Python 3.10+ standard library only;
  scripts never write to the inspected repository.
- **Never execute unreviewed categories**: `setup`, `test`, `server`,
  `dangerous`, and unclassified commands stay manual.
- **ASCII-safe output**: scripts reconfigure stdio to UTF-8 with replacement so
  non-ASCII repository content cannot crash a run.
- **Version sync**: `SKILL.md` metadata, `CHANGELOG.md`, and release tags agree.
- **Every behavior change has a test**: fixtures under `tests/fixtures/` lock
  checker and classifier rules.

## Ask first

- Changing CLI flags, default severities, or the checker's exit-code contract.
- Changing what the smoke tool may execute.
- Deleting a reference, state, or profile document.
- Adding a dependency or a network call.

## Never

- Commit secrets, `.env` files, or inspected repositories' private data.
- Run the smoke tool with an unreviewed category against an untrusted repository.
- Claim a fixture is green without running the suite.
- Publish a release whose tag and `SKILL.md` version disagree.

## Definition of done

- `python -m unittest discover -s tests -v` is green.
- `python scripts/check_agent_docs.py --root . --strict` is green.
- New behavior is covered by a fixture or unit test.
- `CHANGELOG.md` and `SKILL.md` version match the intended release.

## Read next

- [`SKILL.md`](SKILL.md) - workflow, states, and gates.
- [`references/state-audit.md`](references/state-audit.md) - repair order and checker triage.
- [`templates/agent-docs.example`](templates/agent-docs.example) - checker configuration surface.

## Ownership

Owner: Johannes Ramser | Last reviewed: 2026-11-26 | Review by: 2027-11-26
