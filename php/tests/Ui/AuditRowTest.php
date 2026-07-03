<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AuditRow`의 동작을 확인하는 smoke test (태스크 0573).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 감사 행 컴포넌트가 올바르게
 * 렌더링되고, 모든 사용자 입력은 escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AuditRow;
use MintWiki\Ui\Escaper;

$failures = [];

// 테스트용 escaper와 component 생성
$escaper = new Escaper();
$row = new AuditRow($escaper);

// (1) 기본 감사 행 렌더링
$html = $row->render('document.create', 'user123', '테스트 문서', '2026-07-03T10:30:00Z');

if (!str_contains($html, '<tr class="audit-row">')) {
    $failures[] = '감사 행이 tr 요소를 포함해야 한다.';
}

if (!str_contains($html, '<td class="audit-row__event-type">document.create</td>')) {
    $failures[] = '감사 행이 이벤트 유형 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="audit-row__actor">user123</td>')) {
    $failures[] = '감사 행이 행위자 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="audit-row__target">테스트 문서</td>')) {
    $failures[] = '감사 행이 대상 td를 포함해야 한다.';
}

if (!str_contains($html, '<td class="audit-row__time">2026-07-03T10:30:00Z</td>')) {
    $failures[] = '감사 행이 시간 td를 포함해야 한다.';
}

// (2) 이벤트 유형의 XSS escape 확인
$xssEventTypeHtml = $row->render('<script>alert("xss")</script>', 'user123', '대상', '2026-07-03T10:30:00Z');

if (str_contains($xssEventTypeHtml, '<script>')) {
    $failures[] = '이벤트 유형의 script 태그는 escape되어야 한다.';
}

if (!str_contains($xssEventTypeHtml, '&lt;script&gt;')) {
    $failures[] = '이벤트 유형이 &lt;script&gt;로 escape되어야 한다.';
}

// (3) 행위자의 XSS escape 확인
$xssActorHtml = $row->render('document.create', '<img src=x onerror=alert(1)>', '대상', '2026-07-03T10:30:00Z');

if (str_contains($xssActorHtml, '<img src=x onerror')) {
    $failures[] = '행위자의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssActorHtml, '&lt;img src=x onerror')) {
    $failures[] = '행위자가 escape되어야 한다.';
}

// (4) 대상의 XSS escape 확인
$xssTargetHtml = $row->render('document.create', 'user', '<img src=x onerror=alert(1)>', '2026-07-03T10:30:00Z');

if (str_contains($xssTargetHtml, '<img src=x onerror')) {
    $failures[] = '대상의 img 태그는 escape되어야 한다.';
}

if (!str_contains($xssTargetHtml, '&lt;img src=x onerror')) {
    $failures[] = '대상이 escape되어야 한다.';
}

// (5) 시간의 XSS escape 확인
$xssTimeHtml = $row->render('document.create', 'user', '대상', '" onclick="alert(1)"');

if (str_contains($xssTimeHtml, '" onclick=')) {
    $failures[] = '시간의 onclick 속성 breakout은 escape되어야 한다.';
}

if (!str_contains($xssTimeHtml, '&quot; onclick=')) {
    $failures[] = '시간이 escape되어야 한다.';
}

// (6) 특수 문자 escape 확인
$specialHtml = $row->render('document & create', 'user & admin', '문서 < > "테스트"', '2026-07-03 & time');

if (!str_contains($specialHtml, 'document &amp; create')) {
    $failures[] = '이벤트 유형의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, 'user &amp; admin')) {
    $failures[] = '행위자의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '문서 &lt; &gt; &quot;테스트&quot;')) {
    $failures[] = '대상의 특수 문자들이 escape되어야 한다.';
}

if (!str_contains($specialHtml, '2026-07-03 &amp; time')) {
    $failures[] = '시간의 특수 문자들이 escape되어야 한다.';
}

// (7) 빈 필드 처리 - 빈 이벤트 유형
$emptyEventTypeHtml = $row->render('', 'user', '대상', '2026-07-03T10:30:00Z');
if (!empty($emptyEventTypeHtml)) {
    $failures[] = '빈 이벤트 유형은 빈 문자열을 반환해야 한다.';
}

// (8) 빈 필드 처리 - null 행위자
$nullActorHtml = $row->render('document.create', null, '대상', '2026-07-03T10:30:00Z');
if (!empty($nullActorHtml)) {
    $failures[] = 'null 행위자는 빈 문자열을 반환해야 한다.';
}

// (9) 빈 필드 처리 - 빈 대상
$emptyTargetHtml = $row->render('document.create', 'user', '', '2026-07-03T10:30:00Z');
if (!empty($emptyTargetHtml)) {
    $failures[] = '빈 대상은 빈 문자열을 반환해야 한다.';
}

// (10) 빈 필드 처리 - 빈 시간
$emptyTimeHtml = $row->render('document.create', 'user', '대상', '');
if (!empty($emptyTimeHtml)) {
    $failures[] = '빈 시간은 빈 문자열을 반환해야 한다.';
}

// (11) 감사 행 테이블 렌더링
$rows = [
    ['eventType' => 'document.create', 'actor' => 'user1', 'target' => '문서 1', 'time' => '2026-07-03T10:30:00Z'],
    ['eventType' => 'document.edit', 'actor' => 'user2', 'target' => '문서 2', 'time' => '2026-07-03T10:35:00Z'],
];
$tableHtml = $row->renderTable($rows);

if (!str_contains($tableHtml, '<table class="audit-table">')) {
    $failures[] = '테이블이 audit-table 클래스를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<thead>')) {
    $failures[] = '테이블이 thead를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<tbody>')) {
    $failures[] = '테이블이 tbody를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="audit-table__header-event-type">이벤트</th>')) {
    $failures[] = '테이블이 이벤트 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="audit-table__header-actor">행위자</th>')) {
    $failures[] = '테이블이 행위자 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="audit-table__header-target">대상</th>')) {
    $failures[] = '테이블이 대상 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '<th class="audit-table__header-time">시간</th>')) {
    $failures[] = '테이블이 시간 헤더를 포함해야 한다.';
}

if (!str_contains($tableHtml, '문서 1')) {
    $failures[] = '테이블이 첫 번째 대상을 포함해야 한다.';
}

if (!str_contains($tableHtml, '문서 2')) {
    $failures[] = '테이블이 두 번째 대상을 포함해야 한다.';
}

// (12) 빈 테이블 처리
$emptyTableHtml = $row->renderTable([]);
if (!empty($emptyTableHtml)) {
    $failures[] = '빈 감사 행 목록은 빈 문자열을 반환해야 한다.';
}

// (13) 테이블의 XSS escape 확인
$xssRows = [
    ['eventType' => '<script>alert("xss")</script>', 'actor' => '<img src=x onerror=alert(1)>', 'target' => '<svg onload=alert(1)>', 'time' => '"><script>'],
];
$xssTableHtml = $row->renderTable($xssRows);

if (str_contains($xssTableHtml, '<script>')) {
    $failures[] = '테이블의 이벤트 유형에서 script 태그는 escape되어야 한다.';
}

if (str_contains($xssTableHtml, '<img src=x onerror')) {
    $failures[] = '테이블의 행위자에서 img 태그는 escape되어야 한다.';
}

if (str_contains($xssTableHtml, '<svg onload')) {
    $failures[] = '테이블의 대상에서 svg 태그는 escape되어야 한다.';
}

// (14) 테이블에서 필수 필드 없는 항목 건너뛰기
$invalidRows = [
    ['eventType' => '유효한 유형', 'actor' => 'user', 'target' => '대상', 'time' => '2026-07-03T10:30:00Z'],
    ['eventType' => '유형만', 'actor' => 'user'], // target과 time 없음
    ['actor' => 'user2', 'target' => '대상', 'time' => '2026-07-03T10:30:00Z'], // eventType 없음
];
$invalidTableHtml = $row->renderTable($invalidRows);

if (!str_contains($invalidTableHtml, '유효한 유형')) {
    $failures[] = '유효한 항목은 테이블에 포함되어야 한다.';
}

if (str_contains($invalidTableHtml, '유형만')) {
    $failures[] = '필드가 부족한 항목은 건너뛰어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AuditRow 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AuditRow 테스트 통과.\n");
exit(0);
