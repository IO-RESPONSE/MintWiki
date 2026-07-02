<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentViewPage`의 동작을 확인하는 smoke test (태스크 0529).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서가 존재하는 경우와 없는 경우 모두
 * HTML 응답을 올바르게 렌더링하는지 확인한다. 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new DocumentViewPage($escaper, $layout);

// (1) 문서가 존재하는 경우
$document = new Document('test-id', '테스트 문서', 'revision-1');
$html = $page->render($document);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '문서 view HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>테스트 문서</title>')) {
    $failures[] = '문서 view의 title이 문서 제목이어야 한다.';
}

if (!str_contains($html, '<h1>테스트 문서</h1>')) {
    $failures[] = '문서 view가 문서 제목을 h1으로 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '문서 view가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '문서 view가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '문서 view가 footer landmark를 포함해야 한다.';
}

// (2) 문서 제목에 XSS 공격이 포함된 경우 escape 확인
$xssDocument = new Document('xss-id', '<script>alert("xss")</script>', null);
$xssHtml = $page->render($xssDocument);

if (str_contains($xssHtml, '<script>')) {
    $failures[] = '문서 제목의 script 태그는 escape되어야 한다.';
}

if (str_contains($xssHtml, '</script>')) {
    $failures[] = '문서 제목의 script 닫는 태그는 escape되어야 한다.';
}

if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '문서 제목이 escape되어야 한다.';
}

// (3) 문서가 없는 경우 (null)
$notFoundHtml = $page->render(null);

if (!str_contains($notFoundHtml, '<!doctype html>')) {
    $failures[] = '문서 없음 page가 doctype을 포함해야 한다.';
}

if (!str_contains($notFoundHtml, '문서를 찾을 수 없습니다')) {
    $failures[] = '문서 없음 page가 "문서를 찾을 수 없습니다" 메시지를 포함해야 한다.';
}

if (!str_contains($notFoundHtml, '<h1>문서를 찾을 수 없습니다</h1>')) {
    $failures[] = '문서 없음 page의 h1이 "문서를 찾을 수 없습니다"여야 한다.';
}

if (!str_contains($notFoundHtml, '<header></header>')) {
    $failures[] = '문서 없음 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($notFoundHtml, '<footer></footer>')) {
    $failures[] = '문서 없음 page가 footer landmark를 포함해야 한다.';
}

// (4) 다른 특수 문자도 escape되는지 확인
$specialDocument = new Document('special-id', '문서 & < > "test"', null);
$specialHtml = $page->render($specialDocument);

if (!str_contains($specialHtml, '문서 &amp; &lt; &gt; &quot;test&quot;')) {
    $failures[] = '특수 문자들이 올바르게 escape되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentViewPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentViewPage 테스트 통과.\n");
exit(0);
