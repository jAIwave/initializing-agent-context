# Publishing

The repository is prepared for a public GitHub release. The only step left is
creating the remote and pushing.

## Preflight

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `python scripts/check_agent_docs.py --root . --strict` passes.
- [ ] The copyright holder in `LICENSE` is correct.
- [ ] The owner in `README.md` badges and clone URLs is correct
      (`johannes3502` by default; change it if you publish under another account).
- [ ] `SKILL.md` version, `CHANGELOG.md`, and the intended tag agree.

## Create the public repository

With the GitHub CLI (recommended):

```bash
gh auth login
gh repo create initializing-agent-context --public --source . --remote origin --push
```

Without `gh`:

```bash
git remote add origin https://github.com/johannes3502/initializing-agent-context.git
git push -u origin main
```

## Repository settings

Set the description and topics first:

- Description: `Portable agent skill: bootstrap and audit AGENTS.md docs, commands, and checks for any repository`
- Topics: `ai-agents`, `agent-skills`, `agents-md`, `claude-code`, `kilo`,
  `developer-tools`, `documentation`, `codex`

Security and collaboration:

- Enable Issues.
- Enable private vulnerability reporting (Security tab).
- Enable secret scanning and push protection.
- Enable Dependabot alerts and security updates.
- Protect `main`: require the CI check, disallow force pushes, require a pull
  request for changes.
- Protect tags matching `v*`.
- Optional: enable Discussions for usage questions.

## First release

After the first push:

```bash
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
```

The release workflow creates a GitHub release with generated notes. Update the
release text if the changelog needs more context.

## After publishing

- Pin the repository if it is widely used.
- Add the repository to relevant awesome lists or skill directories.
- Link the skill from your profile or organization README.
