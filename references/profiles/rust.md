# Profile: Rust

## Detect

- `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `.cargo/config.toml`
- Entry: `src/main.rs`, `src/lib.rs`, `[[bin]]`, `src/bin/*.rs`
- Tests: inline `#[cfg(test)]`, `tests/`, benchmarks
- Lint/format: `rustfmt.toml`, `clippy.toml`

## Commands to verify

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test --no-run
cargo test
cargo build --release
```

Feature-specific checks:

```bash
cargo test --all-features
cargo check --no-default-features
```

## Common invariants

- No `unsafe` without a safety comment and a reason.
- Errors use the project's error type; no `unwrap` on request paths.
- Feature flags are additive and documented.
- Generated code (build.rs, protobuf) is not hand-edited.
- Public API changes update the crate docs or changelog.

## Hazards

- Workspace members with different feature sets.
- `target/` is huge; keep it out of search.
- `build.rs` can require system libraries.
- Integration tests need services or fixtures.
- Cross-compilation and linker settings.

## Docs to generate

- `docs/testing.md`: workspace vs crate test, features, fixtures.
- `docs/architecture.md`: crates, ownership, error model.
- `docs/operations.md`: release build, target, artifact.
