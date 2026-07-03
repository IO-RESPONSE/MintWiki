<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\Pagination`의 동작을 확인하는 smoke test (태스크 0552).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 페이지네이션 컴포넌트가 올바르게
 * 렌더링되는지 확인한다. 페이지 링크, 이전/다음 네비게이션, 쿼리 매개변수
 * 보존이 올바르게 동작해야 한다. 모든 URL과 텍스트는 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Pagination;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 pagination 생성
$escaper = new Escaper();
$pagination = new Pagination($escaper);

// (1) 단일 페이지 렌더링 (페이지네이션 불필요)
$html = $pagination->render('/documents', 1, 1, []);

if ($html !== '') {
    $failures[] = '전체 페이지가 1이면 빈 문자열을 반환해야 한다.';
}

// (2) 유효하지 않은 현재 페이지 (currentPage > totalPages)
$html = $pagination->render('/documents', 5, 3, []);

if ($html !== '') {
    $failures[] = '현재 페이지가 전체 페이지를 초과하면 빈 문자열을 반환해야 한다.';
}

// (3) 유효하지 않은 현재 페이지 (currentPage < 1)
$html = $pagination->render('/documents', 0, 3, []);

if ($html !== '') {
    $failures[] = '현재 페이지가 1 미만이면 빈 문자열을 반환해야 한다.';
}

// (4) 기본 페이지네이션 렌더링 (3개 페이지)
$html = $pagination->render('/documents', 1, 3, []);

if (!str_contains($html, '<nav class="pagination"')) {
    $failures[] = 'nav 요소에 pagination 클래스를 가져야 한다.';
}

if (!str_contains($html, 'aria-label="페이지 네비게이션"')) {
    $failures[] = 'nav 요소에 aria-label 속성을 가져야 한다.';
}

if (!str_contains($html, '<ul class="pagination__list">')) {
    $failures[] = 'ul 요소에 pagination__list 클래스를 가져야 한다.';
}

if (!str_contains($html, 'pagination__item')) {
    $failures[] = 'li 요소에 pagination__item 클래스를 가져야 한다.';
}

// (5) 첫 번째 페이지에서 이전 버튼이 비활성화됨
$html = $pagination->render('/documents', 1, 3, []);

if (!str_contains($html, 'pagination__item--disabled')) {
    $failures[] = '첫 번째 페이지에서 이전 버튼이 비활성화되어야 한다.';
}

if (!str_contains($html, '<span class="pagination__link" aria-disabled="true">이전</span>')) {
    $failures[] = '비활성화된 이전 버튼이 span으로 렌더링되어야 한다.';
}

// (6) 첫 번째 페이지에서 다음 링크 존재
if (!str_contains($html, 'href="/documents?page=2')) {
    $failures[] = '첫 번째 페이지에서 다음 버튼이 존재해야 한다.';
}

// (7) 마지막 페이지에서 다음 버튼이 비활성화됨
$html = $pagination->render('/documents', 3, 3, []);

if (!str_contains($html, '<span class="pagination__link" aria-disabled="true">다음</span>')) {
    $failures[] = '마지막 페이지에서 다음 버튼이 비활성화되어야 한다.';
}

// (8) 현재 페이지 표시
$html = $pagination->render('/documents', 2, 3, []);

if (!str_contains($html, '<span class="pagination__link" aria-current="page">2</span>')) {
    $failures[] = '현재 페이지가 aria-current="page"로 표시되어야 한다.';
}

// (9) 페이지 링크 렌더링
$html = $pagination->render('/documents', 2, 3, []);

if (!str_contains($html, '<a href="/documents?page=1" class="pagination__link">1</a>')) {
    $failures[] = '페이지 1 링크가 렌더링되어야 한다.';
}

if (!str_contains($html, '<a href="/documents?page=3" class="pagination__link">3</a>')) {
    $failures[] = '페이지 3 링크가 렌더링되어야 한다.';
}

// (10) 쿼리 매개변수 보존
$html = $pagination->render('/documents', 1, 3, ['search' => 'test', 'sort' => 'name']);

if (!str_contains($html, 'search=test')) {
    $failures[] = '쿼리 매개변수 search가 보존되어야 한다.';
}

if (!str_contains($html, 'sort=name')) {
    $failures[] = '쿼리 매개변수 sort가 보존되어야 한다.';
}

if (!str_contains($html, 'page=2')) {
    $failures[] = '페이지 매개변수가 추가되어야 한다.';
}

// (11) 특수 문자 escape - URL에서
$html = $pagination->render('/documents?test', 1, 3, ['q' => '<script>alert("xss")</script>']);

if (str_contains($html, '<script>')) {
    $failures[] = 'URL의 script 태그는 escape되어야 한다.';
}

if (!str_contains($html, '%3Cscript%3E')) {
    $failures[] = '쿼리 매개변수가 URL-encoded되어야 한다.';
}

// (12) 특수 문자 escape - 페이지 번호에서
$html = $pagination->render('/documents', 1, 10, []);

// 페이지 번호는 숫자이므로 escape되면 안 됨
if (str_contains($html, '&lt;')) {
    $failures[] = '페이지 번호는 escape되면 안 된다.';
}

// (13) 많은 페이지 렌더링 (maxLinks 초과)
$html = $pagination->render('/documents', 5, 20, [], 5);

// … 문자가 나타나야 함 (spacer)
if (!str_contains($html, 'pagination__item--spacer')) {
    $failures[] = '많은 페이지에서 spacer가 나타나야 한다.';
}

// (14) 많은 페이지에서 첫 페이지와 마지막 페이지 링크
$html = $pagination->render('/documents', 5, 20, [], 5);

if (!str_contains($html, '<a href="/documents?page=1"')) {
    $failures[] = '많은 페이지에서 첫 페이지 링크가 나타나야 한다.';
}

if (!str_contains($html, '<a href="/documents?page=20"')) {
    $failures[] = '많은 페이지에서 마지막 페이지 링크가 나타나야 한다.';
}

// (15) maxLinks 커스터마이징
$html = $pagination->render('/documents', 1, 10, [], 3);

// 페이지 1, 2, 3과 ... 그리고 10이 표시되어야 함
if (!str_contains($html, '>1<')) {
    $failures[] = 'maxLinks가 3으로 설정되면 3개의 페이지 링크가 표시되어야 한다.';
}

// (16) 비어있는 쿼리 매개변수
$html = $pagination->render('/documents', 1, 3, []);

if (str_contains($html, '?&')) {
    $failures[] = '비어있는 쿼리 매개변수가 있으면 안 된다.';
}

// (17) basePath 기본 경로
$html = $pagination->render('/docs', 1, 3, []);

if (!str_contains($html, 'href="/docs?page=2')) {
    $failures[] = '기본 basePath가 올바르게 처리되어야 한다.';
}

// (18) 페이지 2에서 이전/다음 버튼
$html = $pagination->render('/documents', 2, 3, []);

if (!str_contains($html, '<a href="/documents?page=1" class="pagination__link">이전</a>')) {
    $failures[] = '페이지 2에서 이전 버튼이 페이지 1로 링크되어야 한다.';
}

if (!str_contains($html, '<a href="/documents?page=3" class="pagination__link">다음</a>')) {
    $failures[] = '페이지 2에서 다음 버튼이 페이지 3으로 링크되어야 한다.';
}

// (19) 한국어 텍스트 URL-encoding 테스트
$html = $pagination->render('/documents', 1, 3, ['keyword' => '한글']);

// 한글은 URL-encoding되어야 함
if (!str_contains($html, 'keyword=')) {
    $failures[] = '한글 쿼리 매개변수가 keyword 매개변수로 포함되어야 한다.';
}

// URL-encoded 한글 값이 포함되어야 함 (%ED%95%9C%EA%B8%80은 '한글'의 URL-encoding)
if (!str_contains($html, '%')) {
    $failures[] = '한글 쿼리 매개변수가 URL-encoded되어야 한다.';
}

// (20) closing tags 확인
$html = $pagination->render('/documents', 1, 3, []);

if (!str_contains($html, '</ul>')) {
    $failures[] = 'ul 닫는 태그가 있어야 한다.';
}

if (!str_contains($html, '</nav>')) {
    $failures[] = 'nav 닫는 태그가 있어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Pagination 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Pagination 테스트 통과.\n");
exit(0);
