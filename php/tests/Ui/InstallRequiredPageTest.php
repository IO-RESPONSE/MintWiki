<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallRequiredPage`의 동작을 확인하는 smoke test (태스크 0588).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 설치 필요 page가 올바르게 렌더링되는지
 * 확인한다. 데이터베이스 미설치 상태를 안내하고 모든 사용자 입력은
 * escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new InstallRequiredPage($escaper, $layout);

// (1) 기본 설치 필요 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '설치 필요 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>설치 필요</title>')) {
    $failures[] = '설치 필요 page의 title이 "설치 필요"이어야 한다.';
}

if (!str_contains($html, '<h1>설치 필요</h1>')) {
    $failures[] = '설치 필요 page가 h1으로 "설치 필요"을 표시해야 한다.';
}

if (!str_contains($html, '<p>데이터베이스가 설치되지 않았습니다.</p>')) {
    $failures[] = '설치 필요 page가 데이터베이스 미설치 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<p>관리자는 데이터베이스를 설치하고 마이그레이션을 실행해야 합니다.</p>')) {
    $failures[] = '설치 필요 page가 안내 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '설치 필요 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '설치 필요 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '설치 필요 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallRequiredPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallRequiredPage 테스트 통과.\n");
exit(0);
