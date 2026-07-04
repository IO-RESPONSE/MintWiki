<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallWelcomePage`의 동작을 확인하는 smoke test (태스크 0619).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 설치 환영 page가 올바르게 렌더링되는지
 * 확인한다. 설치 프로세스의 시작을 안내하고 모든 사용자 입력은
 * escape되어야 한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\InstallWelcomePage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;

$failures = [];

// 테스트용 escaper와 layout 생성
$escaper = new Escaper();
$layout = new Layout();
$page = new InstallWelcomePage($escaper, $layout);

// (1) 기본 설치 환영 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '설치 환영 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>설치 환영</title>')) {
    $failures[] = '설치 환영 page의 title이 "설치 환영"이어야 한다.';
}

if (!str_contains($html, '<h1>설치 환영</h1>')) {
    $failures[] = '설치 환영 page가 h1으로 "설치 환영"을 표시해야 한다.';
}

if (!str_contains($html, '<p>MintWiki 설치를 시작합니다.</p>')) {
    $failures[] = '설치 환영 page가 환영 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<p>다음 단계에서 시스템 요구사항을 확인하고 데이터베이스 설정을 진행합니다.</p>')) {
    $failures[] = '설치 환영 page가 절차 안내 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '설치 환영 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '설치 환영 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer>')) {
    $failures[] = '설치 환영 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallWelcomePage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallWelcomePage 테스트 통과.\n");
exit(0);
