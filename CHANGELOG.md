# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.1] - 2026-11-26

### Changed

- CI actions updated via Dependabot: `actions/checkout` to v7 and
  `actions/setup-python` to v7 (#1, #2).

## [1.1.0] - 2026-11-26

### Added

- Mojibake detection in checked Markdown.
- Path-based `exclude` globs in `.agent-docs.json`.
- Package-manager install patterns (`choco`, `winget`, `scoop`, `brew`, `apt`,
  `dnf`, `pacman`, `apk`) classified as `setup`.
- Database bootstrap tools (`createdb`, `dropdb`, `pg_ctl`, `initdb`)
  classified as `dangerous`.
- Tests, fixtures, CI, release workflow, and public repository files.

### Changed

- `include` patterns are authoritative: nested `docs/`/`doc/` directories are
  checked only when listed.
- GitHub-compatible anchor slugs: punctuation is removed, every whitespace
  character becomes a hyphen, runs are not collapsed.
- Smoke classification is boundary-aware for long flags; short `-h`/`-V` no
  longer mark a command as safe.
- System service detection uses a token boundary, avoiding false positives from
  paths such as `src/redis_service`.

### Fixed

- Site-absolute links (`/docs/...`) are skipped instead of treated as missing
  repository files.
- `choco install ... --version=5.3.3` and `postgres ... -h HOST` are no longer
  classified as safe.
- `--json` output of the smoke tool is pure JSON.

## [1.0.0] - 2026-11-25

### Added

- Initial release: repository scanner, agent documentation checker, command
  extraction and classification, state/mode workflow, references, profiles, and
  templates.
