# php/tests

PHP test suite. Empty at this task (0391) — the autoload smoke test (0393)
and fixture runners (0398, 0406, 0407, ...) are added by later Phase B
tasks and must run without any network dependency
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

Cross-language fixtures these runners consume live under
`tests/modules/<module>/fixtures/` or `tests/fixtures/` in the repository
root (`docs/fixture-directory-convention.md`), not here.
