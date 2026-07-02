<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentDiffPage`의 동작을 확인하는 smoke test (태스크 0535).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 diff page가 올바르게 렌더링되는지
 * 확인한다. 두 리비전 ID가 표시되어야 하고, 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;
use MintWiki\Ui\DocumentDiffPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new DocumentDiffPage($escaper, $layout);

// (1) 기본 diff page 렌더링
$document = new Document('doc-123', '테스트 문서', 'revision-2');
$fromRevision = new Revision('rev-1', 'doc-123', '초기 내용', 'user-1', '초기 버전', null);
$toRevision = new Revision('rev-2', 'doc-123', '수정된 내용', 'user-2', '오타 수정', 'rev-1');

$html = $page->render($document, $fromRevision, $toRevision);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = 'diff page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>테스트 문서 - diff</title>')) {
    $failures[] = 'diff page의 title이 "테스트 문서 - diff"여야 한다.';
}

if (!str_contains($html, '<h1>테스트 문서 - diff</h1>')) {
    $failures[] = 'diff page가 h1으로 문서 제목과 " - diff"를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = 'diff page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = 'diff page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = 'diff page가 footer landmark를 포함해야 한다.';
}

// (2) 리비전 ID가 표시되는지 확인
if (!str_contains($html, 'From: rev-1')) {
    $failures[] = 'diff page가 이전 리비전 ID를 표시해야 한다.';
}

if (!str_contains($html, 'To: rev-2')) {
    $failures[] = 'diff page가 이후 리비전 ID를 표시해야 한다.';
}

if (!str_contains($html, '리비전 비교')) {
    $failures[] = 'diff page가 "리비전 비교" 텍스트를 포함해야 한다.';
}

if (!str_contains($html, '실제 diff 내용은 후속 작업에서 구현됩니다.')) {
    $failures[] = 'diff page가 placeholder 메시지를 표시해야 한다.';
}

// (3) 문서 제목에 XSS 공격이 포함된 경우 escape 확인
$xssDocument = new Document('xss-id', '<script>alert("xss")</script>', null);
$xssFromRevision = new Revision('rev-safe', 'xss-id', '내용', 'user-1', '요약', null);
$xssToRevision = new Revision('rev-2', 'xss-id', '수정된 내용', 'user-2', '요약', 'rev-safe');
$xssHtml = $page->render($xssDocument, $xssFromRevision, $xssToRevision);

// title이 h1에서 script 태그가 unescaped로 나타나면 안 됨
if (preg_match('/<h1>[^<]*<script/', $xssHtml)) {
    $failures[] = '문서 제목의 script 태그는 escape되어야 한다.';
}

// title이 &lt;script&gt; 형태로 escape되어야 함
if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '문서 제목이 escape되어야 한다.';
}

// (4) 리비전 ID에 XSS 공격이 포함된 경우 escape 확인
$xssFromRevisionId = new Revision('<img src=x>', 'doc-123', '내용', 'user-1', '요약', null);
$xssToRevisionId = new Revision('<script>alert("xss")</script>', 'doc-123', '수정된 내용', 'user-2', '요약', '<img src=x>');
$xssRevisionIdHtml = $page->render($document, $xssFromRevisionId, $xssToRevisionId);

// From 리비전 ID에서 img 태그가 &lt;img&gt;로 escape되어야 함
if (!str_contains($xssRevisionIdHtml, 'From: &lt;img src=x&gt;')) {
    $failures[] = '이전 리비전 ID가 escape되어야 한다.';
}

// To 리비전 ID에서 script 태그가 &lt;script&gt;로 escape되어야 함
if (!str_contains($xssRevisionIdHtml, 'To: &lt;script&gt;')) {
    $failures[] = '이후 리비전 ID가 escape되어야 한다.';
}

// (5) 다른 특수 문자도 escape되는지 확인
$specialDocument = new Document('special-id', '문서 & < > "test"', null);
$specialFromRevision = new Revision('rev-&-1', 'special-id', '내용', 'user-1', '요약', null);
$specialToRevision = new Revision('rev-&-2', 'special-id', '수정된 내용', 'user-2', '요약', 'rev-&-1');
$specialHtml = $page->render($specialDocument, $specialFromRevision, $specialToRevision);

if (!str_contains($specialHtml, '<h1>문서 &amp; &lt; &gt; &quot;test&quot; - diff</h1>')) {
    $failures[] = '문서 제목의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'From: rev-&amp;-1')) {
    $failures[] = '이전 리비전 ID의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'To: rev-&amp;-2')) {
    $failures[] = '이후 리비전 ID의 특수 문자들이 올바르게 escape되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentDiffPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentDiffPage 테스트 통과.\n");
exit(0);
