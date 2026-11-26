# Contributing

Thanks for improving the skill. Keep changes small, tested, and reversible.

## Prerequisites

- Python 3.10 or newer.
- No third-party packages. The scripts must stay dependency-free and read-only.

## Local checks

```bash
python -m unittest discover -s tests -v
python scripts/check_agent_docs.py --root . --strict
python scripts/scan_repo.py --root .
python scripts/smoke_commands.py --root .
```

Review the smoke classification before executing any category. The fixture
suite covers the classifier; do not run `--run` categories against repositories
you do not trust.

## Rules

- One behavior, one test. Add or update a fixture under `tests/fixtures/` for
  checker and classifier changes.
- Keep script output ASCII-safe; non-ASCII repository content must not crash a
  run.
- Never add a network call or a dependency.
- Never make a script write to the inspected repository.
- Update `SKILL.md` and `CHANGELOG.md` for user-visible changes.
- Keep `SKILL.md` metadata version, `CHANGELOG.md`, and release tags in sync.
- Use clear commit messages; keep unrelated refactors out of a change.

## Pull requests

- [ ] Tests and strict checker pass locally.
- [ ] New behavior has a fixture or unit test.
- [ ] Documentation describes the new flag, config key, or state.
- [ ] No secrets, private paths, or customer data in code, tests, or fixtures.
- [ ] `CHANGELOG.md` has an entry for user-visible changes.
