# Profile: Generic / Unknown Stack

Use this when no specific profile matches, or when the repo mixes stacks that do
not have a profile yet (C/C++, Swift, Dart/Flutter, Elixir, Scala, Lua, R, Julia,
Nix, and others).

## Detect the toolchain

Look for the project file and the lockfile:

| Ecosystem | Project file | Lockfile / tool |
|---|---|---|
| C/C++ | `CMakeLists.txt`, `meson.build`, `Makefile`, `conanfile.txt` | `CMakePresets.json`, `conan.lock`, `vcpkg.json` |
| Swift | `Package.swift`, `*.xcodeproj` | `Package.resolved` |
| Dart/Flutter | `pubspec.yaml` | `pubspec.lock` |
| Elixir | `mix.exs` | `mix.lock` |
| Scala | `build.sbt` | `project/` |
| Nix | `flake.nix`, `default.nix` | `flake.lock` |
| Lua | `*.rockspec`, `.luacheckrc` | `luarocks` |

Then read the CI config and the README. CI is the best evidence of the real
build and test commands.

## Discover commands

1. Read `.github/workflows/*`, `.gitlab-ci.yml`, `Makefile`, `justfile`, and
   `README.md`.
2. Run `<tool> --help` or `<tool> --version`.
3. Prefer the focused test command over the full suite.
4. If no command is documented, derive it from the manifest and mark it
   `inferred` until you run it.

## Common invariants

- Dependency lockfile is committed and used in CI.
- Build output, caches, and generated code are not edited by hand.
- Platform-specific files are documented.
- Secrets come from the environment or a secret manager.
- The build is reproducible from a clean checkout.

## Hazards

- Toolchains that require a specific SDK, compiler, or system library.
- Cross-compilation and platform-specific artifacts.
- Generated code from a build step.
- Optional dependencies and feature flags.
- Long build times; document the fast loop.

## Docs to generate

- `docs/testing.md`: exact command, required SDK, focused vs full.
- `docs/architecture.md`: modules, entry points, data flow.
- `docs/operations.md`: build artifact, runtime, deploy target.

## Rule

Do not invent framework advice. Document only what the repo declares and what you
verified.
