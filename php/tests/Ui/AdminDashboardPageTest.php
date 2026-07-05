<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\AdminDashboardPage`의 동작을 확인하는 smoke test (태스크 0544,
 * 하위 화면 링크 정리는 0697).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 관리자 대시보드 page가 올바르게 렌더링되는지,
 * 관리 하위 화면(감사 로그/신고/사용자 차단/유지보수/백업/복원/진단) 링크가
 * 표시되는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\AdminDashboardPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new AdminDashboardPage($escaper, $layout);

// (1) 기본 관리자 대시보드 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '관리자 대시보드 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>관리자 대시보드</title>')) {
    $failures[] = '관리자 대시보드 page의 title이 "관리자 대시보드"이어야 한다.';
}

if (!str_contains($html, '<h1>관리자 대시보드</h1>')) {
    $failures[] = '관리자 대시보드 page가 h1으로 "관리자 대시보드"를 표시해야 한다.';
}

if (!str_contains($html, '<a href="/admin/audit">감사 로그</a>')) {
    $failures[] = '관리자 대시보드 page가 감사 로그 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/reports">신고</a>')) {
    $failures[] = '관리자 대시보드 page가 신고 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/users/block">사용자 차단</a>')) {
    $failures[] = '관리자 대시보드 page가 사용자 차단 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/maintenance">유지보수</a>')) {
    $failures[] = '관리자 대시보드 page가 유지보수 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/backup">백업</a>')) {
    $failures[] = '관리자 대시보드 page가 백업 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/restore">복원</a>')) {
    $failures[] = '관리자 대시보드 page가 복원 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/admin/diagnostics">진단</a>')) {
    $failures[] = '관리자 대시보드 page가 진단 링크를 포함해야 한다.';
}

if (!str_contains($html, '<nav aria-label="관리 기능">')) {
    $failures[] = '관리자 대시보드 page가 관리 기능 navigation을 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '관리자 대시보드 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '관리자 대시보드 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '관리자 대시보드 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AdminDashboardPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminDashboardPage 테스트 통과.\n");
exit(0);
