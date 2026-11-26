# State: Audit an Existing Agent Setup (S3)

You are not rewriting. You are finding what is missing, stale, duplicated, or
unenforced, and fixing only that.

## 1. Run the checks

```bash
SKILL=.kilo/skills/initializing-agent-context
python "$SKILL/scripts/scan_repo.py" --root .
python "$SKILL/scripts/check_agent_docs.py" --root . --strict --duplicates
python "$SKILL/scripts/smoke_commands.py" --root .
```

Read the output, then inspect the files yourself. The checker finds mechanical
issues; it does not judge whether the content is true.

### Checker triage

- **Site-absolute links** (`/docs/...`, `/api/...`) are routes of the published
  site, not repository files. The checker skips them; do not add `../` or move
  content to make them resolve.
- **Published or generated content** (Astro/Next content collections, API
  reference builds) is not agent documentation. Exclude it with path globs in
  `.agent-docs.json` (`"exclude": ["frontend/site/src/content/**"]`) instead of
  editing published pages.
- **Nested doc dirs** are checked only when listed. Add them to `include` when
  they are current truth, for example `"server/docs/**/*.md"`.
- **Anchors** are GitHub slugs: punctuation is removed, every space becomes a
  hyphen (runs are not collapsed), and duplicate headings get `-1`, `-2`.
  Do not rename an intentional heading to satisfy a link; fix the fragment.
- **Mojibake warnings** (`Ã¤`, `â€“`) mean a file was written with the wrong
  encoding. Rewrite it as UTF-8 instead of adding aliases around it.

## 2. Audit rubric

Score each item pass / warn / fail. Do not fix everything at once; order by
impact.

| # | Check | Pass looks like |
|---|---|---|
| 1 | Entry point | Root `AGENTS.md` exists, is a router, and is linked from `README.md` |
| 2 | Size | Root <= 120 lines target; no file over 260 |
| 3 | Required sections | Commands, Read next, Ownership; invariants for code repos |
| 4 | Commands | Exact, copy-pasteable, workdir, prerequisites, focused test |
| 5 | Verification | Every command run or marked `unverified`; CI/hook exists |
| 6 | Invariants | 5-10 concrete rules with evidence |
| 7 | Boundaries | `Ask first` and `Never` are explicit |
| 8 | One fact, one home | No duplicated email/ports/test counts; links instead |
| 9 | Nested files | Only units with real deltas; parent links child |
| 10 | Freshness | Owner + review date; not overdue |
| 11 | Noise | Generated/vendored/worktree dirs excluded from the agent path |
| 12 | Cold start | A fresh agent finds the entry point and test without help |

## 3. Repair order

Fix in this order; stop when the budget is reached.

1. **Broken links, anchors, escaping paths.** Cheap, mechanical, high trust.
2. **Stale or wrong commands.** Replace with verified commands or mark
   `unverified`.
3. **Missing entry point or missing root router.** Create or repair the router.
4. **Size and duplication.** Move detail to `docs/`; replace copies with links.
   When splitting an oversized root, migrate the verified content to
   `docs/architecture.md` or `docs/testing.md`; do not delete useful knowledge.
   For a root over roughly 500 lines, extract sections, merge repeated
   feature sections, and keep only routing, commands, boundaries, and links.
   First drop tables that duplicate the start-here router (for example a
   separate unit table listing the same child files). Preserve "resolved, do
   not re-fix" notes and known-failure caveats.
   Before compressing a large unit file, list its unique facts (commands, env
   vars, exceptions, gotchas, gates) and check after the rewrite that each one
   survives or is linked. Re-adding lost facts after the first pass is normal.
5. **Missing boundaries.** Add `Ask first` / `Never` where a mistake is costly.
6. **Missing verification.** Wire the checker and one smoke test into CI.
7. **Freshness.** Add owner and review dates; set a review trigger.
8. **Noise.** Exclude worktrees/generated dirs; remove root artifacts.

Do not reorder 1-4 behind a documentation rewrite.

## 4. What not to do

- Do not regenerate a maintained file because the template looks cleaner.
- Do not rename headings just to satisfy a checker; update the checker config
  (`section_aliases` in `.agent-docs.json`) instead if the existing structure is
  intentional.
- Do not add a nested file for every folder.
- Do not copy a rule into three files to "make sure it is seen".
- Do not delete history; move it to `plans/` or an ADR.
- Do not claim a command works because it is written down.
- If an existing nested instruction claims exclusive ownership of a path
  (a docs role, a generated file, another agent's workspace), do not silently
  override it. Keep the change inside your scope, or state the conflict and
  leave that path untouched.

## 5. Duplicate facts

Duplicates are a leading indicator of drift. Look for:

- the same email/port/auth rule in root and unit files,
- the same command in several unit files,
- a port table in the router and in `docs/ports.md`,
- test counts or "Stand <date>" in `AGENTS.md`.

Fix: choose one home, replace the others with a one-line link. If the fact is
generated, link to the generator.

## 6. Index coverage

Every child `AGENTS.md` must be linked from its nearest parent. If a new service
exists without a parent link, the router is incomplete. The checker reports this
as `index coverage`.

## 7. Freshness

- `Last reviewed` is the date of the last content review.
- `Review by` is at most 12 months later.
- An overdue review is a warning; in `--strict` it fails.
- A review date without an owner is not ownership.

## 8. Host-platform failures

A red command is not automatically a product bug. Record the host OS, exact
command, failing test, stack location, and whether the cause is
environment-specific. Do not mark the suite green and do not silently fix
unrelated app code. Put a "Known failure" section in `docs/testing.md` and a
follow-up in the handover.

## 9. Re-audit

After fixes:

```bash
python "$SKILL/scripts/check_agent_docs.py" --root . --strict
python "$SKILL/scripts/smoke_commands.py" --root .
```

Inspect the classification before executing anything. If a documented command
looks dangerous but is classified `safe`/`info`, fix the doc or the classifier
first; never run a category you have not reviewed.

Then run the cold-start test. If the checker is green but the agent still gets
lost, the content is wrong, not the format.

## Done criteria

- No errors; warnings are either fixed or explicitly accepted.
- Commands are verified or marked.
- Duplicates are reduced to canonical links.
- The root is under budget.
- The checker runs in CI or a hook.
- The handover lists what was not fixed and why.
