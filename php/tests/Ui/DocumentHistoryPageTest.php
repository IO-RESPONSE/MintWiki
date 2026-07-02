<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\DocumentHistoryPage`의 동작을 확인하는 smoke test (태스크 0534).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 히스토리 page가 올바르게 렌더링되는지
 * 확인한다. 리비전 목록이 표시되어야 하고, 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;
use MintWiki\Ui\DocumentHistoryPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new DocumentHistoryPage($escaper, $layout);

// (1) 빈 리비전 목록 렌더링
$document = new Document('doc-123', '테스트 문서', 'revision-1');
$html = $page->render($document, []);

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '히스토리 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>문서 히스토리</title>')) {
    $failures[] = '히스토리 page의 title이 "문서 히스토리"여야 한다.';
}

if (!str_contains($html, '<h1>테스트 문서 - 히스토리</h1>')) {
    $failures[] = '히스토리 page가 h1으로 문서 제목과 "- 히스토리"를 표시해야 한다.';
}

if (!str_contains($html, '리비전이 없습니다.')) {
    $failures[] = '히스토리 page가 빈 리비전 목록에서 "리비전이 없습니다." 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '히스토리 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '히스토리 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '히스토리 page가 footer landmark를 포함해야 한다.';
}

// (2) 리비전 목록 렌더링
$revisions = [
    new Revision('rev-1', 'doc-123', '초기 내용', 'user-1', '초기 버전', null),
    new Revision('rev-2', 'doc-123', '수정된 내용', 'user-2', '오타 수정', 'rev-1'),
    new Revision('rev-3', 'doc-123', '최종 내용', 'user-1', '최종 편집', 'rev-2'),
];
$htmlWithRevisions = $page->render($document, $revisions);

if (!str_contains($htmlWithRevisions, '<ul>')) {
    $failures[] = '히스토리 page가 리비전을 리스트로 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, '<li>')) {
    $failures[] = '히스토리 page가 각 리비전을 list item으로 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, 'ID: rev-1')) {
    $failures[] = '히스토리 page가 리비전 ID를 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, '작성자: user-1')) {
    $failures[] = '히스토리 page가 작성자 ID를 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, '요약: 초기 버전')) {
    $failures[] = '히스토리 page가 리비전 요약을 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, 'ID: rev-2')) {
    $failures[] = '히스토리 page가 모든 리비전을 표시해야 한다.';
}

if (!str_contains($htmlWithRevisions, 'ID: rev-3')) {
    $failures[] = '히스토리 page가 모든 리비전을 표시해야 한다.';
}

// (3) 문서 제목에 XSS 공격이 포함된 경우 escape 확인
$xssDocument = new Document('xss-id', '<script>alert("xss")</script>', null);
$xssHtml = $page->render($xssDocument, []);

// title이 h1에서 script 태그가 unescaped로 나타나면 안 됨
if (preg_match('/<h1>[^<]*<script/', $xssHtml)) {
    $failures[] = '문서 제목의 script 태그는 escape되어야 한다.';
}

// title이 &lt;script&gt; 형태로 escape되어야 함
if (!str_contains($xssHtml, '&lt;script&gt;')) {
    $failures[] = '문서 제목이 escape되어야 한다.';
}

// (4) 리비전 데이터에 XSS 공격이 포함된 경우 escape 확인
$xssRevision = new Revision(
    '<img src=x>',
    'doc-123',
    '내용',
    '<script>alert("xss")</script>',
    '요약 <img src=x>',
    null
);
$xssRevisionHtml = $page->render($document, [$xssRevision]);

// Revision ID에서 img 태그가 &lt;img&gt;로 escape되어야 함
if (!str_contains($xssRevisionHtml, '&lt;img src=x&gt;')) {
    $failures[] = '리비전 ID가 escape되어야 한다.';
}

// 작성자 ID에서 script 태그가 &lt;script&gt;로 escape되어야 함
if (!str_contains($xssRevisionHtml, '&lt;script&gt;')) {
    $failures[] = '작성자 ID가 escape되어야 한다.';
}

// 요약에서 img 태그가 &lt;img&gt;로 escape되어야 함
if (!str_contains($xssRevisionHtml, '요약 &lt;img src=x&gt;')) {
    $failures[] = '리비전 요약이 escape되어야 한다.';
}

// (5) 다른 특수 문자도 escape되는지 확인
$specialDocument = new Document('special-id', '문서 & < > "test"', null);
$specialRevision = new Revision(
    'rev-&-test',
    'doc-123',
    '내용',
    'user-&-id',
    '요약 & < > "quote"',
    null
);
$specialHtml = $page->render($specialDocument, [$specialRevision]);

if (!str_contains($specialHtml, '<h1>문서 &amp; &lt; &gt; &quot;test&quot; - 히스토리</h1>')) {
    $failures[] = '문서 제목의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'ID: rev-&amp;-test')) {
    $failures[] = '리비전 ID의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, '작성자: user-&amp;-id')) {
    $failures[] = '작성자 ID의 특수 문자들이 올바르게 escape되어야 한다.';
}

if (!str_contains($specialHtml, '요약: 요약 &amp; &lt; &gt; &quot;quote&quot;')) {
    $failures[] = '리비전 요약의 특수 문자들이 올바르게 escape되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentHistoryPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentHistoryPage 테스트 통과.\n");
exit(0);
