# Profile: Go

## Detect

- `go.mod`, `go.sum`, `go.work`
- Entry: `main.go`, `cmd/*/main.go`
- Tests: `*_test.go`, build tags, `testdata/`
- Lint: `.golangci.yml`, `.golangci.yaml`

## Commands to verify

```bash
go version
go build ./...
go vet ./...
go test ./...
go test ./pkg/name -run TestX -v
golangci-lint run
```

Integration tests often need a tag or a service. Find it before documenting:

```bash
rg -n 'go:build|// \\+build' --glob '*.go'
```

## Common invariants

- Errors are handled or returned; no silent `_ =` on important paths.
- `context.Context` is the first parameter on request/IO paths.
- No global mutable state in libraries; inject dependencies.
- Migrations are additive; schema changes ship with a rollback note.
- Generated code (protobuf, mocks) is not hand-edited.
- Goroutines have an owner and a shutdown path.

## Hazards

- Slow full test suite; document the focused package command.
- Build tags and platform-specific files.
- `go generate` outputs committed or ignored; document which.
- CGO and system libraries.
- Module replacements and private modules.

## Docs to generate

- `docs/testing.md`: package-level loop, integration tags, required services.
- `docs/architecture.md`: packages, command binaries, data ownership.
- `docs/operations.md`: build flags, cross-compilation, deploy artifact.
