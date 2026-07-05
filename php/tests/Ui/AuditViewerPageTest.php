<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AuditViewerPage`의 동작을 확인하는 smoke test (태스크 0545,
 * 실데이터(`AuditEventRecord[]`) 렌더링 검증은 0698).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 감사 로그 page가 올바르게 렌더링되는지
 * 확인한다. 빈 상태와 필터 영역, 그리고 실제 이벤트 목록이 주어졌을 때
 * `AuditRow` 표로 렌더링되는지(actor_id가 null인 이벤트 포함)를 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Audit\AuditEventRecord;
use MintWiki\Ui\AuditViewerPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new AuditViewerPage($escaper, $layout);

// (1) 기본 감사 로그 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '감사 로그 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>감사 로그</title>')) {
    $failures[] = '감사 로그 page의 title이 "감사 로그"이어야 한다.';
}

if (!str_contains($html, '<h1>감사 로그</h1>')) {
    $failures[] = '감사 로그 page가 h1으로 "감사 로그"을 표시해야 한다.';
}

if (!str_contains($html, '<p>감사 로그가 없습니다.</p>')) {
    $failures[] = '감사 로그 page가 빈 상태 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<section aria-label="필터">')) {
    $failures[] = '감사 로그 page가 필터 영역을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="export 액션">')) {
    $failures[] = '감사 로그 page가 export 액션 영역을 포함해야 한다.';
}

if (!str_contains($html, '<button class="audit-export-button"')) {
    $failures[] = '감사 로그 page가 export 버튼을 포함해야 한다.';
}

if (!str_contains($html, 'CSV로 export')) {
    $failures[] = '감사 로그 page의 export 버튼에 "CSV로 export" 텍스트가 있어야 한다.';
}

if (!str_contains($html, '<section aria-label="감사 로그 목록">')) {
    $failures[] = '감사 로그 page가 감사 로그 목록 영역을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '감사 로그 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '감사 로그 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '감사 로그 page가 footer landmark를 포함해야 한다.';
}

// (2) 실제 이벤트 목록이 주어지면 빈 상태 대신 AuditRow 표로 렌더링해야 한다.
$auditEvents = [
    new AuditEventRecord('evt-1', 'acl', 'rule_added', 'rule-1', null, 'user-1', '2026-07-03T10:30:00Z'),
    new AuditEventRecord('evt-2', 'discussion', 'thread_created', 'thread-1', null, null, '2026-07-03T11:00:00Z'),
];
$htmlWithEvents = $page->render($auditEvents);

if (str_contains($htmlWithEvents, '<p>감사 로그가 없습니다.</p>')) {
    $failures[] = '이벤트가 있으면 빈 상태 메시지를 표시하지 않아야 한다.';
}

if (!str_contains($htmlWithEvents, '<table class="audit-table">')) {
    $failures[] = '이벤트가 있으면 AuditRow 표를 렌더링해야 한다.';
}

if (!str_contains($htmlWithEvents, '<td class="audit-row__event-type">acl.rule_added</td>')) {
    $failures[] = '이벤트 유형은 category.action 형식으로 표시되어야 한다.';
}

if (!str_contains($htmlWithEvents, '<td class="audit-row__actor">user-1</td>')) {
    $failures[] = 'actor_id가 있는 이벤트는 그 값을 행위자로 표시해야 한다.';
}

if (!str_contains($htmlWithEvents, '<td class="audit-row__target">rule-1</td>')) {
    $failures[] = 'entity_id는 대상 열에 표시되어야 한다.';
}

if (!str_contains($htmlWithEvents, '<td class="audit-row__event-type">discussion.thread_created</td>')) {
    $failures[] = '두 번째 이벤트도 표에 포함되어야 한다.';
}

if (str_contains($htmlWithEvents, '<td class="audit-row__actor"></td>')) {
    $failures[] = 'actor_id가 null인 이벤트도 대체 값으로 표시되어 행이 누락되지 않아야 한다.';
}

if (!str_contains($htmlWithEvents, '<td class="audit-row__target">thread-1</td>')) {
    $failures[] = 'actor_id가 null인 이벤트도 표에서 누락되지 않아야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AuditViewerPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AuditViewerPage 테스트 통과.\n");
exit(0);
