# Profile: PHP

## Detect

- `composer.json`, `composer.lock`
- Framework: `artisan` (Laravel), `bin/console` (Symfony), `wp-config.php`
- Entry: `public/index.php`, `artisan`, `config.ru` equivalent
- Tests: `phpunit.xml`, `phpunit.xml.dist`, `tests/`
- Lint/type: `phpstan.neon`, `psalm.xml`, `.php-cs-fixer.php`, `pint.json`

## Commands to verify

```bash
composer install
composer test
vendor/bin/phpunit --list-tests
vendor/bin/phpunit --filter TestName
vendor/bin/phpstan analyse
vendor/bin/php-cs-fixer fix --dry-run --diff
```

Laravel:

```bash
php artisan about
php artisan route:list
php artisan test
php artisan migrate:status
```

## Common invariants

- Validate at the boundary; never trust request data.
- Migrations are additive; never edit an applied migration.
- Secrets in `.env`; never commit it.
- Queues/jobs are idempotent and have retry/backoff rules.
- Authorization is checked server-side, not only in the UI.
- Generated caches/config are not edited by hand.

## Hazards

- `vendor/` and `storage/` are generated; exclude from search.
- Framework magic (facades, service container) hides dependencies.
- Queue workers need a separate process.
- Multiple env files and config caches.
- File permissions and upload directories.

## Docs to generate

- `docs/testing.md`: test DB, factories, queue fakes.
- `docs/architecture.md`: modules, routes, data ownership.
- `docs/operations.md`: queue worker, scheduler, deploy, migrations.
