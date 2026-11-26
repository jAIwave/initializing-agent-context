# Profile: .NET

## Detect

- `*.sln`, `*.csproj`, `*.fsproj`, `global.json`, `Directory.Build.props`
- Entry: `Program.cs`, `Startup.cs`, `Main` method
- Tests: `*.Tests.csproj`, `xunit`, `nunit`, `mstest`
- Format: `.editorconfig`, `dotnet format`

## Commands to verify

```bash
dotnet --version
dotnet restore
dotnet build
dotnet test --list-tests
dotnet test
dotnet test --filter FullyQualifiedName~ClassName
dotnet format --verify-no-changes
```

## Common invariants

- Nullable reference types are enabled; warnings are not ignored on new code.
- EF Core migrations are additive and reviewed; no `EnsureCreated` in prod.
- Secrets via user-secrets/env/key vault, never `appsettings.json`.
- `bin/` and `obj/` are not edited or committed.
- API contracts and DTOs are validated at the boundary.
- Async code uses `CancellationToken` on request paths.

## Hazards

- Multiple target frameworks and conditional compilation.
- Integration tests needing SQL Server/containers.
- `launchSettings.json` contains local-only settings.
- Generated clients and migrations.
- Solution vs project build scope.

## Docs to generate

- `docs/testing.md`: test project layout, filters, containers.
- `docs/architecture.md`: projects, layers, data access.
- `docs/operations.md`: publish profile, runtime, migrations.
