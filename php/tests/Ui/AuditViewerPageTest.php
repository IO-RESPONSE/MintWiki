<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AuditViewerPage`의 동작을 확인하는 smoke test (태스크 0545).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 감사 로그 page가 올바르게 렌더링되는지
 * 확인한다. 빈 상태와 필터 영역이 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

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

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '감사 로그 page가 footer landmark를 포함해야 한다.';
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
