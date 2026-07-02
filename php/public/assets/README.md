# php/public/assets

Static asset root for the PHP runtime (0524). The web server serves these
files directly from the document root; requests never pass through
`public/index.php`.

- `css/` — browser-ready stylesheets.
- `js/` — progressive enhancement scripts layered on top of the
  server-rendered HTML.

Only browser-ready output belongs here — no bundler-only artifacts and no
build step is required to serve these files. See
`docs/php-static-asset-serving.md` for the full policy and
`docs/php-ui-architecture.md` for the surrounding UI architecture.
