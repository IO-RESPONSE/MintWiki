<?php

declare(strict_types=1);

/**
 * `MintWiki\Render\NamuMarkDocumentRenderer` 테스트 (태스크 0706).
 *
 * (1) 대표 문서(제목/굵게/내부 링크/목록/표)가 올바른 HTML로 변환되는지,
 * (2) 목차(TOC) 생성/미생성 경계(제목 2개 이상일 때만 노출)가 지켜지는지,
 * (3) headings()/links() 메타데이터가 0705 BlockParser의 결과를 그대로
 *     옮겨 담는지, (4) XSS 안전(파서 계약 유지)까지 확인한다.
 * phpunit 없이 `php` CLI만으로 실행된다(다른 Render 테스트와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Render\DocumentRenderer;
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Render\RenderResult;

$failures = [];

// 0. DocumentRenderer 인터페이스 구현 확인
$reflection = new ReflectionClass(NamuMarkDocumentRenderer::class);
if (!$reflection->implementsInterface(DocumentRenderer::class)) {
    $failures[] = 'NamuMarkDocumentRenderer는 DocumentRenderer 인터페이스를 구현해야 한다.';
}

// (1) 대표 문서: 제목 2개 + 굵게 + 내부 링크 + 목록 + 표를 실제 HTML로 변환.
$renderer = new NamuMarkDocumentRenderer();
$source = <<<'NAMUMARK'
== 소개 ==
이 문서는 '''굵게''' 강조된 문장과 [[다른 문서]] 링크를 포함한다.

== 목록 ==
* 첫 항목
* 둘째 항목

||이름||나이||
||철수||20||
NAMUMARK;

$result = $renderer->render($source);

if (!($result instanceof RenderResult)) {
    $failures[] = 'render()는 RenderResult 인스턴스를 반환해야 한다.';
}

$html = $result->html();

if (!str_contains($html, '<h2 id="소개">소개</h2>')) {
    $failures[] = '대표 문서: 제목이 앵커 id와 함께 <h2>로 렌더링되어야 한다.';
}
if (!str_contains($html, '<strong>굵게</strong>')) {
    $failures[] = "대표 문서: '''굵게'''가 <strong>으로 렌더링되어야 한다.";
}
if (!str_contains($html, '<a href="/wiki/%EB%8B%A4%EB%A5%B8%20%EB%AC%B8%EC%84%9C">다른 문서</a>')) {
    $failures[] = '대표 문서: [[다른 문서]]가 내부 링크로 렌더링되어야 한다.';
}
if (!str_contains($html, '<ul><li>첫 항목</li><li>둘째 항목</li></ul>')) {
    $failures[] = '대표 문서: 목록이 <ul><li>로 렌더링되어야 한다.';
}
if (!str_contains($html, '<table>') || !str_contains($html, '<td>철수</td>')) {
    $failures[] = '대표 문서: 표가 <table><td>로 렌더링되어야 한다.';
}

// headings()/links() 메타데이터가 BlockParser 결과를 그대로 옮겨 담는지 확인.
$headings = $result->headings();
if (count($headings) !== 2) {
    $failures[] = "headings()는 제목 2개를 반환해야 하는데 " . count($headings) . "개였다.";
} else {
    if ($headings[0] !== ['level' => 1, 'text' => '소개', 'id' => '소개']) {
        $failures[] = 'headings()의 첫 제목이 예상과 다르다.';
    }
    if ($headings[1] !== ['level' => 1, 'text' => '목록', 'id' => '목록']) {
        $failures[] = 'headings()의 둘째 제목이 예상과 다르다.';
    }
}

if ($result->links() !== ['다른 문서']) {
    $failures[] = 'links()는 본문에서 발견한 내부 링크 문서 제목을 담아야 한다.';
}

// (2) TOC 생성 경계: 제목이 2개 이상이면 목차가 노출된다.
if (!str_contains($html, '<nav class="toc"')) {
    $failures[] = 'TOC 생성: 제목이 2개 이상이면 <nav class="toc">가 있어야 한다.';
}
if (!str_contains($html, '<a class="toc__link" href="#소개">소개</a>')) {
    $failures[] = 'TOC 생성: 목차 항목이 제목 앵커(#소개)로 점프해야 한다.';
}
if (!str_contains($html, '<a class="toc__link" href="#목록">목록</a>')) {
    $failures[] = 'TOC 생성: 목차 항목이 제목 앵커(#목록)로 점프해야 한다.';
}
// 목차 자체가 본문(제목/목록 등)보다 앞에 나와야 한다.
if (strpos($html, '<nav class="toc"') > strpos($html, '<h2')) {
    $failures[] = 'TOC 생성: 목차는 본문 상단(첫 제목보다 앞)에 배치되어야 한다.';
}

// (2) TOC 미생성 경계: 제목이 0개/1개면 목차가 노출되지 않는다.
$noHeadingResult = $renderer->render("그냥 평범한 문단입니다.");
if (str_contains($noHeadingResult->html(), 'class="toc"')) {
    $failures[] = 'TOC 미생성: 제목이 없으면 목차가 없어야 한다.';
}

$oneHeadingResult = $renderer->render("== 하나뿐인 제목 ==\n본문");
if (str_contains($oneHeadingResult->html(), 'class="toc"')) {
    $failures[] = 'TOC 미생성: 제목이 1개뿐이면 목차가 없어야 한다.';
}
if (!str_contains($oneHeadingResult->html(), '<h2 id="하나뿐인-제목">하나뿐인 제목</h2>')) {
    $failures[] = '제목이 1개인 문서도 본문 자체는 정상적으로 렌더링되어야 한다.';
}

// (3) XSS 안전: source에 포함된 원시 HTML 태그는 escape되어야 한다.
$xssResult = $renderer->render('<script>alert(1)</script>');
if (str_contains($xssResult->html(), '<script>')) {
    $failures[] = 'XSS 안전: source의 script 태그는 escape되어야 한다.';
}
if (!str_contains($xssResult->html(), '&lt;script&gt;')) {
    $failures[] = 'XSS 안전: source의 script 태그가 escape된 형태로 남아야 한다.';
}

// (4) 빈 source: 예외 없이 빈 문서로 처리된다.
$emptyResult = $renderer->render('');
if (!($emptyResult instanceof RenderResult)) {
    $failures[] = '빈 source도 RenderResult를 반환해야 한다.';
}
if ($emptyResult->headings() !== []) {
    $failures[] = '빈 source는 headings()가 빈 배열이어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "NamuMarkDocumentRenderer 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "NamuMarkDocumentRenderer 테스트 통과.\n");
exit(0);
