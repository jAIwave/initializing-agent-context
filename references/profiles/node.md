# Profile: Node / TypeScript

## Detect

- `package.json`, `pnpm-workspace.yaml`, `tsconfig.json`
- Lockfile: `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), `yarn.lock`
  (yarn), `bun.lockb`/`bun.lock` (bun)
- `packageManager` field and `engines` in `package.json`
- Entry: `src/main.*`, `src/index.*`, `src/App.*`, `vite.config.*`,
  `next.config.*`, `nuxt.config.*`, `package.json#bin`
- Tests: `vitest.config.*`, `jest.config.*`, `playwright.config.*`,
  `cypress.config.*`, `__tests__/`, `*.test.*`, `*.spec.*`
- Lint/type: `eslint.config.*`, `.eslintrc*`, `tsconfig.json`, `biome.json`

## Package manager

Use the lockfile and `packageManager`; never assume npm.

```bash
npm ci            # npm with lockfile
pnpm install      # pnpm
yarn install --frozen-lockfile
bun install
```

## Commands to verify

```bash
npm run <script>            # list scripts from package.json first
npx tsc --noEmit            # if tsconfig exists
npx eslint .                # if eslint config exists
npx vitest run              # if vitest config exists
npx jest --listTests        # if jest config exists
npx playwright test --list  # if playwright config exists
```

## Common invariants

- One lockfile and one package manager per repo or workspace.
- Do not commit `node_modules`, build output, or `.env`.
- Client bundles contain only public env vars (`VITE_*`, `NEXT_PUBLIC_*`).
- Auth cookies need `credentials: 'include'`; CSRF header from the cookie.
- SSR/client boundaries: no server-only secret in a client component.
- Service worker/PWA caches must not cache auth or API responses.
- Generated files (routes, clients, icons) are not hand-edited.

## Hazards

- Workspaces: root command vs package command; document both.
- `dev`/`start`/`serve` are long-running; never run during discovery.
- Build output in the repo can confuse search; exclude it.
- Multiple Vite configs and ports; document the mapping.
- Native dependencies and platform-specific installs.

## Docs to generate

- `docs/testing.md`: unit vs E2E, browser install, fixtures, base URL.
- `docs/architecture.md`: apps/packages, shared modules, env prefixes.
- `docs/operations.md`: build output, deploy target, cache headers.
