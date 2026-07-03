<?php

declare(strict_types=1);

/**
 * UI form 연기 테스트(smoke test). 문서 생성/편집 form의 CSRF 토큰 흐름을
 * 검증한다(태스크 0603).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. DocumentCreatePage와
 * DocumentEditPage가 올바르게 CSRF 토큰을 생성하고 embedd하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Ui\DocumentCreatePage;
use MintWiki\Ui\DocumentEditPage;
use MintWiki\Ui\Escaper;
use MintWiki\Ui\Layout;
use MintWiki\Security\CsrfTokenService;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

$escaper = new Escaper();
$layout = new Layout();
$csrfService = new CsrfTokenService();

// (1) 문서 생성 form의 CSRF 토큰 생성 확인
$_SESSION = [];
$createPage = new DocumentCreatePage($escaper, $layout, $csrfService);
$createHtml = $createPage->render();

if (!preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $createHtml, $matches)) {
    $failures[] = '생성 form이 유효한 형식의 CSRF 토큰을 포함해야 한다.';
}

if (!isset($matches[1]) || empty($matches[1])) {
    $failures[] = '생성 form의 CSRF 토큰 값이 비어있으면 안 된다.';
}

$createToken = $matches[1] ?? null;

// (2) 문서 편집 form의 CSRF 토큰 생성 확인
// 별도의 서비스/세션으로 테스트 - 동일한 session 상태에서 동작하는지 확인
$document = new Document('doc-123', '테스트 문서', 'rev-1');
$editPage = new DocumentEditPage($escaper, $layout, new CsrfTokenService());
$_SESSION = [];
$editHtml = $editPage->render($document, '편집 내용');

if (!preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $editHtml, $matches)) {
    $failures[] = '편집 form이 유효한 형식의 CSRF 토큰을 포함해야 한다.';
}

if (!isset($matches[1]) || empty($matches[1])) {
    $failures[] = '편집 form의 CSRF 토큰 값이 비어있으면 안 된다.';
}

$editToken = $matches[1] ?? null;

// (3) CSRF 토큰은 16진수만 포함해야 한다
if ($createToken && !preg_match('/^[a-f0-9]{64}$/', $createToken)) {
    $failures[] = '생성 form의 CSRF 토큰은 64자의 16진수여야 한다.';
}

if ($editToken && !preg_match('/^[a-f0-9]{64}$/', $editToken)) {
    $failures[] = '편집 form의 CSRF 토큰은 64자의 16진수여야 한다.';
}

// (4) 생성 form의 CSRF 토큰이 생성할 때마다 달라야 한다
$createHtml2 = $createPage->render();
if (preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $createHtml2, $matches2)) {
    if ($createToken === $matches2[1]) {
        $failures[] = '생성 form의 CSRF 토큰은 매번 다르게 생성되어야 한다.';
    }
}

// (5) 편집 form의 CSRF 토큰이 생성할 때마다 달라야 한다
$editHtml2 = $editPage->render($document, '편집 내용');
if (preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $editHtml2, $matches2)) {
    if ($editToken === $matches2[1]) {
        $failures[] = '편집 form의 CSRF 토큰은 매번 다르게 생성되어야 한다.';
    }
}

// (6) 생성된 CSRF 토큰을 validate할 수 있어야 한다
// 토큰 생성/검증을 위해 새로운 서비스와 세션 구성
if ($createToken) {
    $_SESSION = [];
    $validateService = new CsrfTokenService();
    $validatePage = new DocumentCreatePage($escaper, $layout, $validateService);
    $validateHtml = $validatePage->render();

    // 같은 서비스/세션에서 토큰을 추출하고 검증
    if (preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $validateHtml, $validateMatches)) {
        $testToken = $validateMatches[1];
        $isValid = $validateService->validate($testToken);
        if (!$isValid) {
            $failures[] = '생성된 CSRF 토큰은 검증되어야 한다.';
        }
    }
}

// (7) 검증된 CSRF 토큰은 재사용할 수 없어야 한다 (한 번 사용하면 제거됨)
if ($createToken) {
    $_SESSION = [];
    $reuseService = new CsrfTokenService();
    $reusePage = new DocumentCreatePage($escaper, $layout, $reuseService);
    $reuseHtml = $reusePage->render();

    if (preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $reuseHtml, $reuseMatches)) {
        $testToken = $reuseMatches[1];
        // 첫 번째 검증 - 성공해야 함
        $isValid1 = $reuseService->validate($testToken);
        if (!$isValid1) {
            $failures[] = 'CSRF 토큰 검증이 실패했다.';
        }

        // 두 번째 검증 - 실패해야 함 (이미 제거됨)
        $isValid2 = $reuseService->validate($testToken);
        if ($isValid2) {
            $failures[] = '검증된 CSRF 토큰은 재사용할 수 없어야 한다.';
        }
    }
}

// (8) 편집 form의 CSRF 토큰도 검증 가능해야 한다
if ($editToken) {
    $_SESSION = [];
    $editValidateService = new CsrfTokenService();
    $editValidatePage = new DocumentEditPage($escaper, $layout, $editValidateService);
    $editValidateHtml = $editValidatePage->render($document, '테스트');

    if (preg_match('/<input type="hidden" name="csrf_token" value="([a-f0-9]{64})">/', $editValidateHtml, $editValidateMatches)) {
        $editTestToken = $editValidateMatches[1];
        $isValid = $editValidateService->validate($editTestToken);
        if (!$isValid) {
            $failures[] = '편집 form의 CSRF 토큰은 검증되어야 한다.';
        }
    }
}

// (9) 존재하지 않는 CSRF 토큰 검증 실패
$_SESSION = [];
$invalidService = new CsrfTokenService();
$invalidToken = 'a' . str_repeat('0', 63);
if ($invalidService->validate($invalidToken)) {
    $failures[] = '존재하지 않는 CSRF 토큰의 검증은 실패해야 한다.';
}

// (10) form 요소들이 올바르게 포함되어 있는지 확인
if (!str_contains($createHtml, '<form method="post" action="/documents">')) {
    $failures[] = '생성 form이 올바른 action을 가져야 한다.';
}

if (!str_contains($editHtml, '<form method="post" action="/documents/doc-123">')) {
    $failures[] = '편집 form이 올바른 action을 가져야 한다.';
}

// (11) CSRF 토큰 input이 올바른 위치(form 내부)에 있는지 확인
if (preg_match('/<form[^>]*>.*csrf_token/s', $createHtml) === 0) {
    $failures[] = '생성 form의 CSRF 토큰 input이 form 요소 내부에 있어야 한다.';
}

if (preg_match('/<form[^>]*>.*csrf_token/s', $editHtml) === 0) {
    $failures[] = '편집 form의 CSRF 토큰 input이 form 요소 내부에 있어야 한다.';
}

// (12) CSRF 토큰이 XSS로부터 보호되어야 한다
if (str_contains($createHtml, '<script>') || str_contains($createHtml, 'javascript:')) {
    $failures[] = '생성 form의 CSRF 토큰 렌더링이 XSS 공격을 포함해서는 안 된다.';
}

if (str_contains($editHtml, '<script>') || str_contains($editHtml, 'javascript:')) {
    $failures[] = '편집 form의 CSRF 토큰 렌더링이 XSS 공격을 포함해서는 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "UI form 연기 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI form 연기 테스트 통과.\n");
exit(0);
