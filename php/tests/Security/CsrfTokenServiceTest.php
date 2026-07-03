<?php

declare(strict_types=1);

/**
 * MintWiki\Security\CsrfTokenService의 동작을 확인하는 test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\CsrfTokenService;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// 테스트 1: 토큰 생성
$service = new CsrfTokenService();
$token1 = $service->generate();

if (empty($token1)) {
    $failures[] = 'generate()는 비어있지 않은 토큰을 반환해야 한다.';
}

if (!is_string($token1)) {
    $failures[] = 'generate()는 문자열을 반환해야 한다.';
}

// 테스트 2: 생성된 토큰의 형식
if (strlen($token1) !== 64) {
    $failures[] = 'generate()는 64자 길이의 16진수 토큰을 반환해야 한다.';
}

if (!ctype_xdigit($token1)) {
    $failures[] = 'generate()는 16진수 문자만 포함하는 토큰을 반환해야 한다.';
}

// 테스트 3: 여러 토큰 생성
$_SESSION = [];
$token2 = $service->generate();
$token3 = $service->generate();

if ($token2 === $token3) {
    $failures[] = 'generate()는 호출할 때마다 서로 다른 토큰을 생성해야 한다.';
}

// 테스트 4: 유효한 토큰 검증
$_SESSION = [];
$validToken = $service->generate();
$isValid = $service->validate($validToken);

if (!$isValid) {
    $failures[] = 'validate()는 generate()로 생성한 토큰을 유효하다고 판정해야 한다.';
}

// 테스트 5: 유효하지 않은 토큰 검증
$_SESSION = [];
$invalidToken = '0000000000000000000000000000000000000000000000000000000000000000';
$isValid = $service->validate($invalidToken);

if ($isValid) {
    $failures[] = 'validate()는 존재하지 않는 토큰을 유효하지 않다고 판정해야 한다.';
}

// 테스트 6: 토큰 재사용 불가
$_SESSION = [];
$token = $service->generate();
$firstValidate = $service->validate($token);
$secondValidate = $service->validate($token);

if (!$firstValidate) {
    $failures[] = 'validate()는 첫 번째 검증에서 유효한 토큰을 반환해야 한다.';
}

if ($secondValidate) {
    $failures[] = 'validate()는 같은 토큰을 두 번째에는 유효하지 않다고 판정해야 한다 (토큰이 소비되어야 한다).';
}

// 테스트 7: 여러 토큰 동시 관리
$_SESSION = [];
$serviceNew = new CsrfTokenService();
$tokenA = $serviceNew->generate();
$tokenB = $serviceNew->generate();
$tokenC = $serviceNew->generate();

$validateA = $serviceNew->validate($tokenA);
$validateC = $serviceNew->validate($tokenC);
$validateB = $serviceNew->validate($tokenB);

if (!$validateA || !$validateB || !$validateC) {
    $failures[] = 'validate()는 생성된 모든 토큰을 유효하다고 판정해야 한다.';
}

// 테스트 8: 빈 토큰 검증
if ($service->validate('')) {
    $failures[] = 'validate()는 빈 문자열을 유효하지 않다고 판정해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "CsrfTokenService 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "CsrfTokenService 테스트 통과.\n");
exit(0);
