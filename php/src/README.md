# php/src

PHP application and module source. Empty at this task (0391) — the
composer autoload configuration (0392) and `Http` value objects
(0395-0397) were added by earlier Phase B tasks; `Modules/` (0399) holds
the per-module namespace skeleton, still empty of classes.

Classes here follow the namespace mapping fixed in
`docs/php-namespace-mapping.md`: `MintWiki\<Module>` for module code, with
one directory per module under `src/Modules` (`docs/php-namespace-mapping.md`
lists the 12 modules and their `MintWiki\<Module>` namespaces).
