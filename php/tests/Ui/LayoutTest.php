<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\Layout의 최소 HTML skeleton 렌더링을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Layout;

$failures = [];
$layout = new Layout();

$html = $layout->render('MintWiki <Home>', '<main><h1>홈</h1></main>');

foreach ([
    '<!doctype html>' => 'doctype을 포함해야 한다.',
    '<html lang="ko">' => '기본 lang은 ko여야 한다.',
    '<meta charset="utf-8">' => 'UTF-8 meta charset을 포함해야 한다.',
    '<meta name="viewport" content="width=device-width, initial-scale=1">' => 'viewport meta를 포함해야 한다.',
    '<title>MintWiki &lt;Home&gt;</title>' => 'title은 escape해야 한다.',
    '<link rel="stylesheet" href="/assets/css/design-tokens.css">' => 'design-tokens CSS를 포함해야 한다.',
    '<link rel="stylesheet" href="/assets/css/print.css" media="print">' => 'print CSS를 포함해야 한다.',
    '<header></header>' => 'header landmark를 포함해야 한다.',
    '<main><h1>홈</h1></main>' => 'body HTML은 layout 안에 포함해야 한다.',
    '<footer></footer>' => 'footer landmark를 포함해야 한다.',
] as $needle => $message) {
    if (!str_contains($html, $needle)) {
        $failures[] = $message;
    }
}

$langHtml = $layout->render('Title', '<p>body</p>', 'ko" data-x="1');
if (!str_contains($langHtml, '<html lang="ko&quot; data-x=&quot;1">')) {
    $failures[] = 'lang attribute는 escape해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Layout 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Layout 테스트 통과.\n");
exit(0);
