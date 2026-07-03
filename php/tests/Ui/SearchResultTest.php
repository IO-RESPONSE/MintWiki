<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\SearchResult`의 동작을 확인하는 smoke test (태스크 0571).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 검색 결과 컴포넌트가 올바르게
 * 렌더링되고, 모든 사용자 입력은 escape되어야 한다. 특히 snippet escape를
 * 보장한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\SearchResult;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 component 생성
$escaper = new Escaper();
$result = new SearchResult($escaper);

// (1) 기본 검색 결과 렌더링 (제목 + URL)
$html = $result->render('테스트 문서', '/documents/test');

if (!str_contains($html, '<div class="search-result">')) {
    $failures[] = '검색 결과가 search-result 클래스 div를 포함해야 한다.';
}

if (!str_contains($html, '<h3 class="search-result__title">')) {
    $failures[] = '검색 결과의 제목이 h3으로 표시되어야 한다.';
}

if (!str_contains($html, '<a href="/documents/test">테스트 문서</a>')) {
    $failures[] = '검색 결과의 제목이 링크로 표시되어야 한다.';
}

// (2) Snippet을 포함한 검색 결과 렌더링
$htmlWithSnippet = $result->render('문서 제목', '/docs/1', '이것은 문서의 발췌입니다.');

if (!str_contains($htmlWithSnippet, '<p class="search-result__snippet">')) {
    $failures[] = '검색 결과가 snippet 단락을 포함해야 한다.';
}

if (!str_contains($htmlWithSnippet, '이것은 문서의 발췌입니다.')) {
    $failures[] = '검색 결과가 snippet 텍스트를 포함해야 한다.';
}

// (3) 제목의 XSS escape 확인
$xssTitleHtml = $result->render('<script>alert("xss")</script>', '/docs/1');

if (str_contains($xssTitleHtml, '<script>')) {
    $failures[] = '제목의 script 태그는 escape되어야 한다.';
}

if (str_contains($xssTitleHtml, '</script>')) {
    $failures[] = '제목의 script 닫는 태그는 escape되어야 한다.';
}

if (!str_contains($xssTitleHtml, '&lt;script&gt;')) {
    $failures[] = '제목이 &lt;script&gt;로 escape되어야 한다.';
}

// (4) URL의 XSS escape 확인 (속성 context)
$xssUrlHtml = $result->render('테스트', '"><img src=x onerror=alert(1)>');

if (str_contains($xssUrlHtml, '"><img')) {
    $failures[] = 'URL의 attribute breakout 시도는 escape되어야 한다.';
}

if (!str_contains($xssUrlHtml, '&quot;&gt;&lt;img')) {
    $failures[] = 'URL이 escape되어야 한다.';
}

// (5) Snippet의 XSS escape 확인
$xssSnippetHtml = $result->render('제목', '/docs/1', '<img src=x onerror=alert(1)>');

if (str_contains($xssSnippetHtml, '<img src=x onerror')) {
    $failures[] = 'snippet의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssSnippetHtml, '&lt;img src=x onerror')) {
    $failures[] = 'snippet이 escape되어야 한다.';
}

// (6) 특수 문자 escape 확인
$specialHtml = $result->render('문서 & < > "테스트"', '/docs/1?q=test&page=1', '내용 & 더 <내용>');

if (!str_contains($specialHtml, '문서 &amp; &lt; &gt; &quot;테스트&quot;')) {
    $failures[] = '제목의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '내용 &amp; 더 &lt;내용&gt;')) {
    $failures[] = 'snippet의 특수 문자들이 escape되어야 한다.';
}

// (7) 빈 제목이나 URL 필드 처리
$emptyHtml = $result->render('', '/docs/1');
if (!empty($emptyHtml)) {
    $failures[] = '빈 제목은 빈 문자열을 반환해야 한다.';
}

$emptyUrlHtml = $result->render('제목', '');
if (!empty($emptyUrlHtml)) {
    $failures[] = '빈 URL은 빈 문자열을 반환해야 한다.';
}

// (8) Null snippet 처리 (snippet 없음)
$noSnippetHtml = $result->render('제목', '/docs/1', null);
if (str_contains($noSnippetHtml, 'search-result__snippet')) {
    $failures[] = 'null snippet일 때는 snippet 단락이 없어야 한다.';
}

// (9) 빈 snippet 처리 (snippet 문자열이 비어 있음)
$emptySnippetHtml = $result->render('제목', '/docs/1', '');
if (str_contains($emptySnippetHtml, 'search-result__snippet')) {
    $failures[] = '빈 snippet일 때는 snippet 단락이 없어야 한다.';
}

// (10) 검색 결과 목록 렌더링 - 기본
$resultsList = [
    ['title' => '문서 1', 'url' => '/docs/1', 'snippet' => '첫 번째 문서 내용'],
    ['title' => '문서 2', 'url' => '/docs/2', 'snippet' => '두 번째 문서 내용'],
];
$listHtml = $result->renderList($resultsList);

if (!str_contains($listHtml, '<div class="search-results">')) {
    $failures[] = '검색 결과 목록이 search-results 클래스 div를 포함해야 한다.';
}

if (!str_contains($listHtml, '문서 1')) {
    $failures[] = '검색 결과 목록이 첫 번째 문서를 포함해야 한다.';
}

if (!str_contains($listHtml, '문서 2')) {
    $failures[] = '검색 결과 목록이 두 번째 문서를 포함해야 한다.';
}

// (11) 빈 목록 처리
$emptyListHtml = $result->renderList([]);
if (!empty($emptyListHtml)) {
    $failures[] = '빈 검색 결과 목록은 빈 문자열을 반환해야 한다.';
}

// (12) 목록의 XSS escape 확인
$xssListResults = [
    ['title' => '<script>alert("xss")</script>', 'url' => '/docs/1', 'snippet' => '<img src=x onerror=alert(1)>'],
];
$xssListHtml = $result->renderList($xssListResults);

if (str_contains($xssListHtml, '<script>')) {
    $failures[] = '목록의 제목에서 script 태그는 escape되어야 한다.';
}

if (str_contains($xssListHtml, '<img src=x onerror')) {
    $failures[] = '목록의 snippet에서 img 태그는 escape되어야 한다.';
}

// (13) 목록에서 필수 필드 없는 항목 건너뛰기
$invalidListResults = [
    ['title' => '유효한 문서', 'url' => '/docs/1'],
    ['title' => '제목만 있음'], // URL이 없음
    ['url' => '/docs/2'], // 제목이 없음
];
$invalidListHtml = $result->renderList($invalidListResults);

// 유효한 항목만 포함되어야 함
if (!str_contains($invalidListHtml, '유효한 문서')) {
    $failures[] = '유효한 항목은 목록에 포함되어야 한다.';
}

if (str_contains($invalidListHtml, '제목만 있음')) {
    $failures[] = 'URL이 없는 항목은 건너뛰어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "SearchResult 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "SearchResult 테스트 통과.\n");
exit(0);
