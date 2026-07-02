# php/public

Web server document root for the PHP runtime.

- `index.php` (0394, 0419) — front controller. Registers a single
  `GET /health` route on `MintWiki\Http\Router` that returns a JSON
  `{"status": "ok", "app": <app name>}` response (app name from
  `MintWiki\App\ConfigLoader`'s `app_name` key, defaulting to
  `wiki-engine`). Any other method/path still falls back to the original
  placeholder text response built from `REQUEST_METHOD`/`REQUEST_URI` —
  no other routing or application logic is wired up yet. Remaining routes
  arrive in later Phase B tasks (0526,
  `docs/php-db-ui-micro-job-prompts-0351-0670.md`).

- `assets/` (0524) — static asset root served directly by the web server,
  not through `index.php`. CSS lives under `assets/css/` and progressive
  enhancement JavaScript under `assets/js/`, referenced by document-root
  absolute URLs (e.g. `/assets/css/app.css`). See
  `docs/php-static-asset-serving.md` for the shared-hosting serving model,
  the no-build default, and where cache/integrity policy (0577, 0578, 0606)
  attaches.

This is the only directory a web server should expose directly; everything
under `php/src` stays outside the document root.
