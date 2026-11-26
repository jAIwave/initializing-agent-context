# Profile: Ruby

## Detect

- `Gemfile`, `Gemfile.lock`, `.ruby-version`
- Framework: `config.ru`, `bin/rails`, `Rakefile`
- Entry: `config.ru`, `bin/rails`, `app/`
- Tests: `.rspec`, `spec/`, `test/`, `rails test`
- Lint: `.rubocop.yml`, `standardrb`

## Commands to verify

```bash
bundle install
bundle exec rspec --dry-run
bundle exec rspec spec/models/user_spec.rb
bundle exec rubocop
bin/rails test
bin/rails test test/models/user_test.rb
```

## Common invariants

- Migrations are additive; never edit an applied migration.
- Strong parameters / boundary validation for request data.
- Secrets in credentials/env; never commit the master key.
- Background jobs are idempotent.
- N+1 queries are treated as a bug on request paths.
- Generated schema (`db/schema.rb`) is updated by migrations, not by hand.

## Hazards

- `vendor/bundle`, `tmp/`, `log/` are generated.
- Multiple databases (primary/replica) and connection switching.
- Rails env (`development`, `test`, `production`) changes behavior.
- Asset pipeline / JS bundling.
- Fixtures/factories can hide test coupling.

## Docs to generate

- `docs/testing.md`: RSpec vs Minitest, factories, test DB.
- `docs/architecture.md`: domain models, jobs, boundaries.
- `docs/operations.md`: migrations, jobs, deploy, credentials.
