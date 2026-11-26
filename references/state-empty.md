# State: Empty Repository (S0)

No code, no manifests, or only a stub README. The goal is not a documentation
set. The goal is a **feedback loop** and a few decisions.

## 1. Ask only what code cannot answer

Ask at most five questions; if the user does not answer, record a decision
backlog instead of guessing.

1. What is the product, and who uses it?
2. What stack constraints exist (team skills, hosting, compliance, existing
   services)?
3. Where will it run (local only, container, serverless, existing platform)?
4. Who owns it, and what must never happen (data, security, cost)?
5. What is the first user-visible behavior that proves it works?

## 2. Create a decision backlog

Create `docs/adr/` only when a decision is actually made. Otherwise keep a
short list in the handover report:

```text
Open decisions
- Language/runtime: unknown
- Deploy target: unknown
- Database: unknown
- Auth: unknown
- Test framework: unknown
```

Do not write architecture prose for code that does not exist.

## 3. Build a walking skeleton

As soon as the stack is known, create the smallest runnable path:

| Shape | Skeleton |
|---|---|
| Web app | One page, one route, one render test |
| API | One endpoint, one schema, one request test |
| CLI | One command, `--help`, one output test |
| Library | One public function, one unit test, one import example |
| Worker | One job handler, one dry-run invocation, one test |

The skeleton must include:

- an entry point,
- one test that fails before the implementation and passes after,
- one command that runs the test,
- one command that starts the thing locally.

This is the most valuable agent context in an empty repo.

## 4. Files to create

First pass, maximum four; the ADR counts as one of the four:

```text
README.md                 purpose, status, how to run (once it runs)
AGENTS.md                 router: scope, commands, Ask first, Never, DoD
.gitignore                runtime artifacts, secrets, build output
docs/adr/0001-stack.md    only if the stack decision is made
```

Optional, only when justified:

- `.editorconfig` if formatting is otherwise ambiguous.
- CI skeleton if the repo already has a remote.
- `docs/testing.md` once there is more than one test command.

## 5. Root AGENTS.md focus

For an empty repo the router is mostly boundaries:

- Scope: what this repo is and is not.
- Commands: install, dev, test once they exist; otherwise `TBD` with a date.
- `Ask first`: stack, database, auth, deploy, dependency additions.
- `Never`: secrets in git, destructive migrations, unreviewed deploy.
- Definition of done: the test command that must pass.
- Ownership: owner and review date.

Keep it under 100 lines. It will change quickly; do not over-document.

## 6. Handover

Report:

- decisions made and decisions still open,
- files created,
- the command that currently proves the skeleton works,
- the first feature to build,
- the review trigger: "revisit AGENTS.md after the first real feature".

## Done criteria

- One command runs the skeleton.
- One test proves it.
- `AGENTS.md` states the boundaries and the current verification command.
- No invented architecture, no placeholder claims presented as facts.

## Anti-patterns

- Writing a 200-line architecture doc before the first commit.
- Choosing a stack silently.
- Creating nested `AGENTS.md` files for empty folders.
- Marking commands as working when they have never run.
