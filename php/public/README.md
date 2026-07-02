# php/public

Web server document root for the PHP runtime.

- `index.php` (0394) — front controller skeleton. Reads `REQUEST_METHOD`
  and `REQUEST_URI` from `$_SERVER` and returns a fixed placeholder text
  response; no routing or application logic is wired up yet. Routing
  arrives in later Phase B tasks (0398, 0419, 0526,
  `docs/php-db-ui-micro-job-prompts-0351-0670.md`).

This is the only directory a web server should expose directly; everything
under `php/src` stays outside the document root.
