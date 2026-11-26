# Security Policy

## Supported versions

The latest 1.x release receives fixes. Security fixes are released as patch
versions with a changelog entry.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting on the repository's Security tab, or contact the
maintainer through GitHub.

Include the affected version, the command or repository content that triggers
the issue, and the observed impact. You will receive an acknowledgement and a
coordinated disclosure timeline.

## Threat model

- The Python scripts are read-only and make no network requests.
- `smoke_commands.py` extracts documented commands and executes only categories
  explicitly requested. `setup`, `test`, `server`, `dangerous`, and unclassified
  commands stay manual.
- Classification is a safety aid, not a sandbox. A reviewed category can still
  run a command that is hostile by design. Never run the tool with an
  unreviewed category against an untrusted repository.
- Fixtures must never contain secrets, private keys, tokens, or personal data.
- The skill never reads `.env` contents; it only lists environment file names.
