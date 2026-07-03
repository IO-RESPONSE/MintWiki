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
use MintWiki\Render\PlainTextDocumentRenderer;
use MintWiki\Render\DocumentRenderer;
use MintWiki\Render\RenderResult;

$failures = [];

// 테스트용 escaper, layout, renderer 생성
$escaper = new Escaper();
$layout = new Layout();
$renderer = new PlainTextDocumentRenderer();
$page = new DocumentViewPage($escaper, $layout, $renderer);

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

// (5) render output 연결 테스트: source가 제공되면 렌더링된 내용을 표시해야 한다.
$documentWithSource = new Document('doc-id', 'Test Document with Source', 'revision-1');
$sourceContent = "Hello World\n\nThis is a test document.";
$htmlWithSource = $page->render($documentWithSource, $sourceContent);

if (!str_contains($htmlWithSource, '<p>Hello World</p>')) {
    $failures[] = 'render output: 렌더링된 source 내용이 표시되어야 한다.';
}

if (!str_contains($htmlWithSource, '<p>This is a test document.</p>')) {
    $failures[] = 'render output: 렌더링된 multiple paragraphs가 표시되어야 한다.';
}

// (6) unsafe HTML 정책 테스트: source의 HTML 태그는 escape되어야 한다.
$documentWithHtml = new Document('html-id', 'Document with HTML', null);
$sourceWithHtml = '<script>alert("xss")</script><p>content</p>';
$htmlWithUnsafeHtml = $page->render($documentWithHtml, $sourceWithHtml);

if (str_contains($htmlWithUnsafeHtml, '<script>')) {
    $failures[] = 'unsafe HTML 정책: source의 script 태그는 escape되어야 한다.';
}

if (str_contains($htmlWithUnsafeHtml, '</script>')) {
    $failures[] = 'unsafe HTML 정책: source의 script 닫는 태그는 escape되어야 한다.';
}

if (!str_contains($htmlWithUnsafeHtml, '&lt;script&gt;')) {
    $failures[] = 'unsafe HTML 정책: source의 HTML 태그가 escape되어야 한다.';
}

if (!str_contains($htmlWithUnsafeHtml, '&lt;p&gt;')) {
    $failures[] = 'unsafe HTML 정책: source의 p 태그도 escape되어야 한다.';
}

// (7) source가 없을 때: placeholder 표시
$documentWithoutSource = new Document('no-source-id', 'Document without Source', 'revision-2');
$htmlWithoutSource = $page->render($documentWithoutSource, null);

if (!str_contains($htmlWithoutSource, '문서 내용이 여기에 표시됩니다.')) {
    $failures[] = 'render output: source가 없을 때 placeholder를 표시해야 한다.';
}

// (8) unsafe HTML 정책: 동적 속성 시도
$documentWithAttr = new Document('attr-id', 'Document with Attributes', null);
$sourceWithAttr = '<div onclick="alert(1)">test</div>';
$htmlWithAttr = $page->render($documentWithAttr, $sourceWithAttr);

// onclick은 escaped 되면서 &lt;div onclick=&quot;...&quot;&gt; 형태가 되므로,
// 실행 가능한 HTML 형태의 <div onclick 이 없고 &lt;div 로 escape되었는지만 확인
if (str_contains($htmlWithAttr, '<div onclick')) {
    $failures[] = 'unsafe HTML 정책: 실행 가능한 형태의 div onclick이 있으면 안 된다.';
}

if (!str_contains($htmlWithAttr, '&lt;div')) {
    $failures[] = 'unsafe HTML 정책: div 태그가 escape되어야 한다.';
}

// (9) 렌더러 실패 fallback 상태: renderer가 exception을 던질 때
// 테스트용 renderer 클래스: exception을 던지는 renderer
class FailingDocumentRenderer implements DocumentRenderer
{
    public function render(string $source): RenderResult
    {
        throw new \RuntimeException('렌더링 중 오류 발생');
    }
}

$failingRenderer = new FailingDocumentRenderer();
$pageWithFailingRenderer = new DocumentViewPage($escaper, $layout, $failingRenderer);

$documentForFailure = new Document('fail-id', 'Failing Document', 'revision-1');
$sourceForFailure = "This is a source that will fail to render";
$fallbackHtml = $pageWithFailingRenderer->render($documentForFailure, $sourceForFailure);

if (!str_contains($fallbackHtml, 'render-fallback')) {
    $failures[] = 'render fallback: fallback div가 있어야 한다.';
}

if (!str_contains($fallbackHtml, '문서 렌더링에 실패했습니다')) {
    $failures[] = 'render fallback: 오류 메시지가 표시되어야 한다.';
}

if (!str_contains($fallbackHtml, '원본 소스입니다')) {
    $failures[] = 'render fallback: 소스 안내 메시지가 있어야 한다.';
}

if (!str_contains($fallbackHtml, $sourceForFailure)) {
    $failures[] = 'render fallback: escape된 source가 표시되어야 한다.';
}

if (!str_contains($fallbackHtml, '<pre')) {
    $failures[] = 'render fallback: source가 pre 태그로 표시되어야 한다.';
}

// (10) render fallback: source의 특수문자가 escape되는지 확인
$dangerousSource = "<script>alert('xss')</script>";
$dangerousFallbackHtml = $pageWithFailingRenderer->render($documentForFailure, $dangerousSource);

if (str_contains($dangerousFallbackHtml, '<script>')) {
    $failures[] = 'render fallback: script 태그는 escape되어야 한다.';
}

if (!str_contains($dangerousFallbackHtml, '&lt;script&gt;')) {
    $failures[] = 'render fallback: script 태그가 escape되어야 한다.';
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
