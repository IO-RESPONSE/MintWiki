# php

PHP runtime tree for the module-by-module replacement described in
`docs/php-replacement-strategy.md`. This directory holds only the empty
skeleton added by Phase B: PHP Runtime Skeleton, 0391-0440
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`); no PHP code runs yet.

- `src/` — application and module source, namespaced under `MintWiki\`
  (`docs/php-namespace-mapping.md`).
- `public/` — web server document root; the front controller lands in 0394.
- `tests/` — PHP test suite; the autoload smoke test lands in 0393.

Contract manifests, fixtures, and policies that this tree must eventually
satisfy live under `src/modules/*/manifest.json` and `docs/` — see
`docs/php-replacement-strategy.md` for the readiness gate each module must
pass before its PHP implementation replaces the Python one.
