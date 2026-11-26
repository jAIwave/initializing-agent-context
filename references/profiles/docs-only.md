# Profile: Docs-Only Repository

No application code. The repository is a knowledge base: marketing, research,
plans, content, or operations. `AGENTS.md` is a workflow router, not a code map.

## Detect

- Markdown/text dominates; no manifests or code entry points.
- Folders such as `marketing/`, `research/`, `plans/`, `content/`, `crm/`.
- May contain generated assets (images, video) and a render script.

## What to map

- Where the current truth lives (strategy, pricing, product facts).
- Where open work lives (one task list, stable IDs).
- Where decisions live (decision log/ADRs).
- Where evidence lives (dated research, sources).
- What is gitignored (leads, PII, consents, generated assets).

## AGENTS.md shape

- Scope: what this repo is and is not; which code repos it refers to.
- Start here: task -> read first.
- Source of truth: topic -> one home.
- Hard rules: PII, secrets, claims, pricing, legal review.
- Task/work protocol: update the one task list, record decisions, archive.
- Verification: link check, source check, review checklist.
- Ownership.

## Verification

```bash
python .kilo/skills/initializing-agent-context/scripts/check_agent_docs.py --root . --strict
```

Also check manually:

- Every claim with a number has a source and a date.
- No real names, emails, phone numbers, or customer data in git.
- No unreviewed price or legal claim presented as final.
- No duplicate facts across strategy, sales, and content docs.

## Common invariants

- One task list; no parallel TODO files.
- Stable task IDs; status and next step are mandatory.
- One fact, one home; summaries link to the source.
- Archive instead of delete when history matters.
- No PII or secrets in git; generated assets stay out.
- Legal/price claims are marked "draft" or "review" until approved.

## Hazards

- Stale strategy docs treated as current truth.
- Contradictory numbers in sales, website, and content.
- Leads or consents committed by accident.
- Generated assets bloating the repo.
- Render scripts with absolute local paths.

## Docs to generate

- `AGENTS.md` (router).
- `README.md` (human overview).
- `TODO.md` (single task list) if absent.
- `strategy/entscheidungen.md` or `docs/adr/` for durable decisions.
