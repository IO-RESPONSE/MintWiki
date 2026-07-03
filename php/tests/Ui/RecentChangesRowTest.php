<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\RecentChangesRow`의 동작을 확인하는 smoke test (태스크 0572).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 최근 변경 행 컴포넌트가 올바르게
 * 렌더링되고, 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\RecentChangesRow;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 component 생성
$escaper = new Escaper();
$row = new RecentChangesRow($escaper);

// (1) 기본 최근 변경 행 렌더링
$html = $row->render('테스트 문서', 'user123', '초기 작성', '2026-07-03T10:30:00Z');

if (!str_contains($html, '<tr class="recent-changes-row">')) {
    $failures[] = '최근 변경 행이 tr 요소를 포함해야 한다.';
}

if (!str_contains($html, '<td class="recent-changes-row__document">테스트 문서</td>')) {
    $failures[] = '최근 변경 행이 문서명 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="recent-changes-row__user">user123</td>')) {
    $failures[] = '최근 변경 행이 사용자 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="recent-changes-row__summary">초기 작성</td>')) {
    $failures[] = '최근 변경 행이 요약 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="recent-changes-row__time">2026-07-03T10:30:00Z</td>')) {
    $failures[] = '최근 변경 행이 시간 td를 포함해야 한다.';
}

// (2) 문서명의 XSS escape 확인
$xssDocHtml = $row->render('<script>alert("xss")</script>', 'user123', '요약', '2026-07-03T10:30:00Z');

if (str_contains($xssDocHtml, '<script>')) {
    $failures[] = '문서명의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssDocHtml, '&lt;script&gt;')) {
    $failures[] = '문서명이 &lt;script&gt;로 escape되어야 한다.';
}

// (3) 사용자 이름의 XSS escape 확인
$xssUserHtml = $row->render('문서', '<img src=x onerror=alert(1)>', '요약', '2026-07-03T10:30:00Z');

if (str_contains($xssUserHtml, '<img src=x onerror')) {
    $failures[] = '사용자 이름의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssUserHtml, '&lt;img src=x onerror')) {
    $failures[] = '사용자 이름이 escape되어야 한다.';
}

// (4) 요약의 XSS escape 확인
$xssSummaryHtml = $row->render('문서', 'user', '<img src=x onerror=alert(1)>', '2026-07-03T10:30:00Z');

if (str_contains($xssSummaryHtml, '<img src=x onerror')) {
    $failures[] = '요약의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssSummaryHtml, '&lt;img src=x onerror')) {
    $failures[] = '요약이 escape되어야 한다.';
}

// (5) 시간의 XSS escape 확인
$xssTimeHtml = $row->render('문서', 'user', '요약', '" onclick="alert(1)"');

if (str_contains($xssTimeHtml, '" onclick=')) {
    $failures[] = '시간의 onclick 속성 breakout은 escape되어야 한다.';
}

if (!str_contains($xssTimeHtml, '&quot; onclick=')) {
    $failures[] = '시간이 escape되어야 한다.';
}

// (6) 특수 문자 escape 확인
$specialHtml = $row->render('문서 & < > "테스트"', 'user & test', '요약 & <더보기>', '2026-07-03 & time');

if (!str_contains($specialHtml, '문서 &amp; &lt; &gt; &quot;테스트&quot;')) {
    $failures[] = '문서명의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'user &amp; test')) {
    $failures[] = '사용자 이름의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '요약 &amp; &lt;더보기&gt;')) {
    $failures[] = '요약의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '2026-07-03 &amp; time')) {
    $failures[] = '시간의 특수 문자들이 escape되어야 한다.';
}

// (7) 빈 필드 처리 - 빈 문서명
$emptyDocHtml = $row->render('', 'user', '요약', '2026-07-03T10:30:00Z');
if (!empty($emptyDocHtml)) {
    $failures[] = '빈 문서명은 빈 문자열을 반환해야 한다.';
}

// (8) 빈 필드 처리 - 빈 사용자
$emptyUserHtml = $row->render('문서', '', '요약', '2026-07-03T10:30:00Z');
if (!empty($emptyUserHtml)) {
    $failures[] = '빈 사용자는 빈 문자열을 반환해야 한다.';
}

// (9) 빈 필드 처리 - 빈 요약
$emptySummaryHtml = $row->render('문서', 'user', '', '2026-07-03T10:30:00Z');
if (!empty($emptySummaryHtml)) {
    $failures[] = '빈 요약은 빈 문자열을 반환해야 한다.';
}

// (10) 빈 필드 처리 - 빈 시간
$emptyTimeHtml = $row->render('문서', 'user', '요약', '');
if (!empty($emptyTimeHtml)) {
    $failures[] = '빈 시간은 빈 문자열을 반환해야 한다.';
}

// (11) 최근 변경 행 테이블 렌더링
$rows = [
    ['documentName' => '문서 1', 'user' => 'user1', 'summary' => '초기 작성', 'time' => '2026-07-03T10:30:00Z'],
    ['documentName' => '문서 2', 'user' => 'user2', 'summary' => '편집', 'time' => '2026-07-03T10:35:00Z'],
];
$tableHtml = $row->renderTable($rows);

if (!str_contains($tableHtml, '<table class="recent-changes-table">')) {
    $failures[] = '테이블이 recent-changes-table 클래스를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<thead>')) {
    $failures[] = '테이블이 thead를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<tbody>')) {
    $failures[] = '테이블이 tbody를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="recent-changes-table__header-document">문서</th>')) {
    $failures[] = '테이블이 문서 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="recent-changes-table__header-user">사용자</th>')) {
    $failures[] = '테이블이 사용자 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="recent-changes-table__header-summary">요약</th>')) {
    $failures[] = '테이블이 요약 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="recent-changes-table__header-time">시간</th>')) {
    $failures[] = '테이블이 시간 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '문서 1')) {
    $failures[] = '테이블이 첫 번째 문서를 포함해야 한다.';
}

if (!str_contains($tableHtml, '문서 2')) {
    $failures[] = '테이블이 두 번째 문서를 포함해야 한다.';
}

// (12) 빈 테이블 처리
$emptyTableHtml = $row->renderTable([]);
if (!empty($emptyTableHtml)) {
    $failures[] = '빈 최근 변경 행 목록은 빈 문자열을 반환해야 한다.';
}

// (13) 테이블의 XSS escape 확인
$xssRows = [
    ['documentName' => '<script>alert("xss")</script>', 'user' => '<img src=x onerror=alert(1)>', 'summary' => '<svg onload=alert(1)>', 'time' => '"><script>'],
];
$xssTableHtml = $row->renderTable($xssRows);

if (str_contains($xssTableHtml, '<script>')) {
    $failures[] = '테이블의 문서명에서 script 태그는 escape되어야 한다.';
}

if (str_contains($xssTableHtml, '<img src=x onerror')) {
    $failures[] = '테이블의 사용자에서 img 태그는 escape되어야 한다.';
}

if (str_contains($xssTableHtml, '<svg onload')) {
    $failures[] = '테이블의 요약에서 svg 태그는 escape되어야 한다.';
}

// (14) 테이블에서 필수 필드 없는 항목 건너뛰기
$invalidRows = [
    ['documentName' => '유효한 문서', 'user' => 'user', 'summary' => '요약', 'time' => '2026-07-03T10:30:00Z'],
    ['documentName' => '제목만', 'user' => 'user'], // summary와 time 없음
    ['user' => 'user2', 'summary' => '요약', 'time' => '2026-07-03T10:30:00Z'], // documentName 없음
];
$invalidTableHtml = $row->renderTable($invalidRows);

if (!str_contains($invalidTableHtml, '유효한 문서')) {
    $failures[] = '유효한 항목은 테이블에 포함되어야 한다.';
}

if (str_contains($invalidTableHtml, '제목만')) {
    $failures[] = '필드가 부족한 항목은 건너뛰어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "RecentChangesRow 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "RecentChangesRow 테스트 통과.\n");
exit(0);
