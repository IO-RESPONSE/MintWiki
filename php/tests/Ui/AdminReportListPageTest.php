<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AdminReportListPage`의 동작을 확인하는 smoke test (태스크 0546).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 신고 목록 page가 올바르게 렌더링되는지
 * 확인한다. 빈 상태와 필터 영역이 표시되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AdminReportListPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new AdminReportListPage($escaper, $layout);

// (1) 기본 신고 목록 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '신고 목록 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>신고</title>')) {
    $failures[] = '신고 목록 page의 title이 "신고"이어야 한다.';
}

if (!str_contains($html, '<h1>신고</h1>')) {
    $failures[] = '신고 목록 page가 h1으로 "신고"를 표시해야 한다.';
}

if (!str_contains($html, '<p>신고가 없습니다.</p>')) {
    $failures[] = '신고 목록 page가 빈 상태 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<section aria-label="필터">')) {
    $failures[] = '신고 목록 page가 필터 영역을 포함해야 한다.';
}

if (!str_contains($html, '<section aria-label="신고 목록">')) {
    $failures[] = '신고 목록 page가 신고 목록 영역을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '신고 목록 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '신고 목록 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '신고 목록 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AdminReportListPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminReportListPage 테스트 통과.\n");
exit(0);
