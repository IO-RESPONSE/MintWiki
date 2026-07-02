<?php

declare(strict_types=1);

/**
 * UI 접근성 기본 baseline 테스트.
 *
 * 서버 렌더링되는 HTML의 접근성 최소 요구사항을 확인한다:
 * - 언어 속성 (lang)
 * - 뷰포트 메타 태그
 * - 폼 레이블 및 입력 필드 관계
 * - 시맨틱 랜드마크 (header, main, footer)
 * - 제목 계층 구조
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

// ============================================================================
// 1. 언어(lang) 속성 확인
// ============================================================================

// (1-1) 기본 lang 속성이 존재하고 'ko'로 설정되어야 한다.
$html = $layout->render('테스트', '<main><h1>테스트</h1></main>');
if (!str_contains($html, '<html lang="ko">')) {
    $failures[] = '[lang] 기본 lang 속성이 "ko"로 설정되어야 한다.';
}

// (1-2) 다른 언어 지정 시 lang 속성이 올바르게 이스케이프되어야 한다.
$customLangHtml = $layout->render('테스트', '<main><h1>테스트</h1></main>', 'en');
if (!str_contains($customLangHtml, '<html lang="en">')) {
    $failures[] = '[lang] 커스텀 lang 값이 올바르게 설정되어야 한다.';
}

// (1-3) lang 속성의 특수문자가 적절히 이스케이프되어야 한다.
$xssTestHtml = $layout->render('테스트', '<main><h1>테스트</h1></main>', 'en" data-x="1');
if (!str_contains($xssTestHtml, '<html lang="en&quot; data-x=&quot;1">')) {
    $failures[] = '[lang] lang 속성의 특수문자가 적절히 이스케이프되어야 한다.';
}

// ============================================================================
// 2. 뷰포트 메타 태그 확인
// ============================================================================

// (2-1) 뷰포트 메타 태그가 반드시 포함되어야 한다.
$html = $layout->render('테스트', '<main><h1>테스트</h1></main>');
if (!str_contains($html, '<meta name="viewport"')) {
    $failures[] = '[viewport] 뷰포트 메타 태그가 포함되어야 한다.';
}

// (2-2) 뷰포트 설정이 반응형 디자인을 지원해야 한다.
if (!str_contains($html, 'width=device-width')) {
    $failures[] = '[viewport] 뷰포트가 device-width를 설정해야 한다.';
}

// (2-3) 초기 스케일이 설정되어야 한다.
if (!str_contains($html, 'initial-scale=1')) {
    $failures[] = '[viewport] 뷰포트의 초기 스케일이 1로 설정되어야 한다.';
}

// ============================================================================
// 3. 폼 레이블 확인
// ============================================================================

// (3-1) 폼 입력 필드에 id가 있고 label이 for 속성으로 연결되어야 한다.
$formHtml = $layout->render(
    '검색',
    '<main>'
    . '<form method="get" action="/search">'
    . '<label for="search-query">검색어:</label>'
    . '<input type="text" id="search-query" name="q" required>'
    . '<button type="submit">검색</button>'
    . '</form>'
    . '</main>'
);

if (!str_contains($formHtml, '<label for="search-query">')) {
    $failures[] = '[labels] 폼 레이블이 for 속성으로 입력 필드와 연결되어야 한다.';
}

if (!str_contains($formHtml, '<input type="text" id="search-query"')) {
    $failures[] = '[labels] 입력 필드가 고유한 id를 가져야 한다.';
}

// (3-2) 버튼은 명확한 텍스트 또는 aria-label을 가져야 한다.
if (!str_contains($formHtml, '<button type="submit">검색</button>')) {
    $failures[] = '[labels] 버튼이 명확한 텍스트를 포함해야 한다.';
}

// (3-3) 필수 입력 필드에 required 속성이 있어야 한다.
if (!str_contains($formHtml, '<input type="text" id="search-query" name="q" required>')) {
    $failures[] = '[labels] 필수 입력 필드에 required 속성이 있어야 한다.';
}

// ============================================================================
// 4. 시맨틱 랜드마크 확인
// ============================================================================

// (4-1) header 랜드마크가 있어야 한다.
$html = $layout->render('테스트', '<main><h1>테스트</h1></main>');
if (!str_contains($html, '<header></header>')) {
    $failures[] = '[landmarks] HTML이 header 랜드마크를 포함해야 한다.';
}

// (4-2) main 랜드마크가 있어야 한다.
if (!str_contains($html, '<main>')) {
    $failures[] = '[landmarks] HTML이 main 랜드마크를 포함해야 한다.';
}

// (4-3) footer 랜드마크가 있어야 한다.
if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '[landmarks] HTML이 footer 랜드마크를 포함해야 한다.';
}

// (4-4) 랜드마크들이 올바른 순서로 배치되어야 한다.
$landmarkPositions = [
    'header' => strpos($html, '<header>'),
    'main' => strpos($html, '<main>'),
    'footer' => strpos($html, '<footer>'),
];
$isCorrectOrder = $landmarkPositions['header'] < $landmarkPositions['main'] &&
                 $landmarkPositions['main'] < $landmarkPositions['footer'];
if (!$isCorrectOrder) {
    $failures[] = '[landmarks] 랜드마크가 올바른 순서(header → main → footer)로 배치되어야 한다.';
}

// ============================================================================
// 5. 제목 계층 구조 확인
// ============================================================================

// (5-1) h1은 정확히 한 개만 있어야 한다.
$h1Count = substr_count($html, '<h1>');
if ($h1Count !== 1) {
    $failures[] = '[headings] 페이지가 정확히 하나의 h1 제목을 포함해야 한다.';
}

// (5-2) 제목이 주요 콘텐츠를 설명해야 한다.
if (!str_contains($html, '<h1>')) {
    $failures[] = '[headings] 페이지가 h1 제목을 포함해야 한다.';
}

// ============================================================================
// 6. 문자 인코딩 확인
// ============================================================================

// (6-1) UTF-8 charset이 명시되어야 한다.
if (!str_contains($html, '<meta charset="utf-8">')) {
    $failures[] = '[charset] HTML이 UTF-8 charset을 명시해야 한다.';
}

// ============================================================================
// 7. 기타 접근성 요소
// ============================================================================

// (7-1) 문서 타입 선언이 있어야 한다.
if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '[doctype] HTML이 doctype 선언을 포함해야 한다.';
}

// (7-2) title 요소가 있어야 한다.
if (!str_contains($html, '<title>')) {
    $failures[] = '[title] HTML이 title 요소를 포함해야 한다.';
}

// ============================================================================
// 결과 처리
// ============================================================================

if ($failures !== []) {
    fwrite(STDERR, "UI 접근성 baseline 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI 접근성 baseline 테스트 통과.\n");
exit(0);
