# php/public

Web server document root for the PHP runtime. Empty at this task (0391) —
the front controller (`index.php`) is added in 0394 and only reads request
information and returns a placeholder response at that point.

This is the only directory a web server should expose directly; everything
under `php/src` stays outside the document root.
