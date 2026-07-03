<?php

declare(strict_types=1);

/**
 * `MintWiki\Ui\InstallCompletionPage`의 동작을 확인하는 smoke test (태스크 0625).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 설치 완료 page가 완료 상태와 다음
 * 조치를 올바르게 안내하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;
use MintWiki\Ui\InstallCompletionPage;
use MintWiki\Ui\Layout;

$failures = [];

$escaper = new Escaper();
$layout = new Layout();
$page = new InstallCompletionPage($escaper, $layout);

// (1) 기본 설치 완료 page 렌더링
$html = $page->render();

if (!str_contains($html, '<!doctype html>')) {
    $failures[] = '설치 완료 page HTML이 doctype을 포함해야 한다.';
}

if (!str_contains($html, '<title>설치 완료</title>')) {
    $failures[] = '설치 완료 page의 title이 "설치 완료"이어야 한다.';
}

if (!str_contains($html, '<h1>설치 완료</h1>')) {
    $failures[] = '설치 완료 page가 h1으로 "설치 완료"를 표시해야 한다.';
}

if (!str_contains($html, '<p>MintWiki 설치가 완료되었습니다.</p>')) {
    $failures[] = '설치 완료 page가 설치 완료 메시지를 표시해야 한다.';
}

if (!str_contains($html, '<p>보안을 위해 설치 도구 접근을 비활성화하고 관리자 계정으로 로그인하세요.</p>')) {
    $failures[] = '설치 완료 page가 보안 후속 조치를 안내해야 한다.';
}

if (!str_contains($html, '<h2 id="next-steps-title">다음 조치</h2>')) {
    $failures[] = '설치 완료 page가 다음 조치 섹션 제목을 표시해야 한다.';
}

if (!str_contains($html, '<li>설치 파일과 설정 파일 권한을 운영 환경에 맞게 제한하세요.</li>')) {
    $failures[] = '설치 완료 page가 파일 권한 제한 조치를 안내해야 한다.';
}

if (!str_contains($html, '<li>관리자 계정으로 로그인한 뒤 사이트 기본 설정을 확인하세요.</li>')) {
    $failures[] = '설치 완료 page가 관리자 설정 확인 조치를 안내해야 한다.';
}

if (!str_contains($html, '<li>첫 문서를 작성해 설치 상태를 확인하세요.</li>')) {
    $failures[] = '설치 완료 page가 첫 문서 작성 확인 조치를 안내해야 한다.';
}

if (!str_contains($html, '<a href="/login">관리자 로그인</a>')) {
    $failures[] = '설치 완료 page가 관리자 로그인 링크를 포함해야 한다.';
}

if (!str_contains($html, '<a href="/">사이트로 이동</a>')) {
    $failures[] = '설치 완료 page가 사이트 이동 링크를 포함해야 한다.';
}

if (!str_contains($html, '<main>')) {
    $failures[] = '설치 완료 page가 main 요소를 포함해야 한다.';
}

if (!str_contains($html, '<header></header>')) {
    $failures[] = '설치 완료 page가 header landmark를 포함해야 한다.';
}

if (!str_contains($html, '<footer></footer>')) {
    $failures[] = '설치 완료 page가 footer landmark를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InstallCompletionPage 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallCompletionPage 테스트 통과.\n");
exit(0);
