# Discovery Checklist

Read-only inventory for any repository. Run from the repository root. Prefer
`scripts/scan_repo.py` first; use this checklist to fill the gaps and verify.

## 1. Shape and safety

```bash
pwd
git status --short
git branch --show-current
git log -5 --oneline
git worktree list
```

- Confirm the repo root. Inside a submodule, treat the submodule as the repo.
- Note untracked files, worktrees, submodules, and generated directories.
- Do not open `.env`, credentials, keys, database dumps, or customer data.
- List env file names only: `ls -a | grep '^\\.env'` (bash) or
  `Get-ChildItem -Force -Filter '.env*'` (PowerShell).

## 2. Size and languages

```bash
git ls-files | wc -l
git ls-files | sed 's/.*\\.//' | sort | uniq -c | sort -rn | head -20
```

PowerShell equivalent:

```powershell
(git ls-files).Count
git ls-files | ForEach-Object { [IO.Path]::GetExtension($_) } |
  Group-Object | Sort-Object Count -Descending | Select-Object -First 20
```

Skip `node_modules`, virtualenvs, `dist`, `build`, `target`, `vendor`, worktrees.
If the repo contains a vendored or third-party toolkit that is not part of the
product (for example `tools/`), pass `--skip tools` to the scanner and add it to
the checker's `exclude_dirs`; otherwise its skills and docs add noise.

## 3. Manifests and package managers

| Stack | Look for |
|---|---|
| Node | `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `.nvmrc`, `engines` |
| Python | `pyproject.toml`, `requirements*.txt`, `setup.py`, `Pipfile`, `poetry.lock`, `uv.lock`, `.python-version` |
| Go | `go.mod`, `go.work`, `go.sum` |
| Rust | `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` |
| JVM | `pom.xml`, `build.gradle(.kts)`, `settings.gradle`, `gradlew`, `mvnw` |
| .NET | `*.sln`, `*.csproj`, `global.json`, `Directory.Build.props` |
| PHP | `composer.json`, `composer.lock` |
| Ruby | `Gemfile`, `Gemfile.lock`, `.ruby-version` |
| Infra | `Dockerfile`, `compose.yaml`, `*.tf`, `Chart.yaml`, `k8s/`, `ansible/` |

Read the declared scripts, not only the files:

```bash
# Node
node -e "const p=require('./package.json'); console.log(p.packageManager||'', p.engines||{}, p.scripts||{})"

# Python
python - <<'PY'
import tomllib
with open('pyproject.toml','rb') as f:
    d=tomllib.load(f)
print(d.get('project',{}).get('scripts',{}))
print(d.get('tool',{}).get('poetry',{}).get('scripts',{}))
PY
```

## 4. Entry points

Search names and patterns, then read the smallest set:

```bash
rg -n --glob '!node_modules' --glob '!venv' --glob '!.venv' \
  '(^|/)(main|app|server|index|manage|wsgi|asgi)\\.(py|js|ts|tsx|mjs|go|rs|java|cs)$'
rg -n 'if __name__ == .__main__.' --glob '*.py'
rg -n 'app\\.(get|post|put|patch|delete)\\(' --glob '*.py' | head -40
rg -n 'router\\.(get|post|put|patch|delete)\\(' --glob '*.{js,ts,tsx}' | head -40
```

Also inspect `pyproject.toml` `[project.scripts]`, `package.json` `bin`, Go
`cmd/*/main.go`, Rust `[[bin]]`, JVM main classes, and `.NET` `Program.cs`.

## 5. Verification loop

Find the focused command before the full suite:

```bash
rg -n 'pytest|vitest|jest|playwright|cypress|phpunit|rspec|go test|cargo test|dotnet test' \
  README.md AGENTS.md docs package.json pyproject.toml Makefile justfile 2>/dev/null
```

Check config files:

- Python: `pytest.ini`, `tox.ini`, `conftest.py`, `[tool.pytest.ini_options]`.
- Node: `vitest.config.*`, `jest.config.*`, `playwright.config.*`, `cypress.config.*`.
- Go: `go test ./...`, build tags, integration tags.
- Rust: `cargo test`, feature flags.
- JVM: `mvn test`, `gradle test`, wrapper presence.
- .NET: `dotnet test`, `--filter`.
- PHP: `phpunit.xml`, `composer test`.
- Ruby: `.rspec`, `bundle exec rspec`.

Run only what is safe: `--help`, `--version`, `--collect-only`, `--list`,
`--dry-run`. Do not run migrations, deploys, or servers during discovery.

## 6. Lint, typecheck, format

```bash
ls -a | rg 'eslint|prettier|tsconfig|ruff|mypy|pyright|golangci|clippy|rustfmt|editorconfig|biome'
```

Document only what exists. If there is no static check, say so; do not invent
one. A missing typecheck is a finding, not a command to write.

## 7. CI and deploy

- `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`,
  `azure-pipelines.yml`, `.circleci/config.yml`.
- `Dockerfile`, `compose.yaml`, `deploy/`, `systemd/*.service`, `nginx/`,
  `k8s/`, `helm/`, `terraform/`, `ansible/`.
- What does CI actually run? If CI exists, it is the best source for the
  "definition of done".

## 8. Data and migrations

- `migrations/`, `alembic/`, `prisma/schema.prisma`, `db/`, `schema.sql`,
  `flyway/`, `liquibase/`, ORM models.
- Find the migration command and whether it is additive.
- Identify the production database from docs/config names, not by opening
  secrets.

## 9. Docs and decisions

- `README.md`, `CONTRIBUTING.md`, `docs/`, `docs/adr/`, `plans/`, `CHANGELOG.md`.
- Existing `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/*.mdc`,
  `.github/copilot-instructions.md`, `GEMINI.md`.
- Note what is current truth vs history. A dated plan is not current truth.

## 10. Git history

```bash
git log --oneline -20
git log --name-only --pretty=format: -50 | sort | uniq -c | sort -rn | head -20
git log -S 'TODO' --oneline --all | head -20
```

- Hot files reveal where changes concentrate.
- Recurring fix commits reveal gotchas worth documenting.
- Large deletions or renames reveal stale docs.

## Evidence table

Fill this before writing anything:

| Claim | Evidence | Confidence |
|---|---|---|
| Install command | `package.json:12` | verified |
| Focused test | `pytest --collect-only` ran | verified |
| Deploy target | `deploy/*.service` | inferred |
| Why the queue exists | no ADR, no comment | unknown |
| Owner | `CODEOWNERS` | verified |

`verified` = you ran it or read the exact source. `inferred` = the code strongly
implies it. `unknown` = do not write it as fact.

## Stop conditions

- More than ~20k files: narrow to one unit and state the scope.
- No runnable environment: document prerequisites and mark commands `unverified`.
- No tests: make the first recommendation a walking-skeleton test, not a doc.
- Conflicting docs: current code + tests win; record the conflict as an ADR or an
  open question.
