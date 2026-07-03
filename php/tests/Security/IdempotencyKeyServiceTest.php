<?php

declare(strict_types=1);

/**
 * MintWiki\Security\IdempotencyKeyService의 동작을 확인하는 test (태스크 0569).
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\IdempotencyKeyService;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// 테스트 1: 키 생성
$service = new IdempotencyKeyService();
$key1 = $service->generate();

if (empty($key1)) {
    $failures[] = 'generate()는 비어있지 않은 키를 반환해야 한다.';
}

if (!is_string($key1)) {
    $failures[] = 'generate()는 문자열을 반환해야 한다.';
}

// 테스트 2: 생성된 키의 형식
if (strlen($key1) !== 64) {
    $failures[] = 'generate()는 64자 길이의 16진수 키를 반환해야 한다.';
}

if (!ctype_xdigit($key1)) {
    $failures[] = 'generate()는 16진수 문자만 포함하는 키를 반환해야 한다.';
}

// 테스트 3: 여러 키 생성
$_SESSION = [];
$key2 = $service->generate();
$key3 = $service->generate();

if ($key2 === $key3) {
    $failures[] = 'generate()는 호출할 때마다 서로 다른 키를 생성해야 한다.';
}

// 테스트 4: 유효한 키 검증
$_SESSION = [];
$validKey = $service->generate();
$isValid = $service->validate($validKey);

if (!$isValid) {
    $failures[] = 'validate()는 generate()로 생성한 키를 유효하다고 판정해야 한다.';
}

// 테스트 5: 유효하지 않은 키 검증
$_SESSION = [];
$invalidKey = '0000000000000000000000000000000000000000000000000000000000000000';
$isValid = $service->validate($invalidKey);

if ($isValid) {
    $failures[] = 'validate()는 존재하지 않는 키를 유효하지 않다고 판정해야 한다.';
}

// 테스트 6: 키 재사용 불가 (중복 제출 방지)
$_SESSION = [];
$key = $service->generate();
$firstValidate = $service->validate($key);
$secondValidate = $service->validate($key);

if (!$firstValidate) {
    $failures[] = 'validate()는 첫 번째 검증에서 유효한 키를 반환해야 한다.';
}

if ($secondValidate) {
    $failures[] = 'validate()는 같은 키를 두 번째에는 유효하지 않다고 판정해야 한다 (키가 소비되어야 한다).';
}

// 테스트 7: 여러 키 동시 관리
$_SESSION = [];
$serviceNew = new IdempotencyKeyService();
$keyA = $serviceNew->generate();
$keyB = $serviceNew->generate();
$keyC = $serviceNew->generate();

$validateA = $serviceNew->validate($keyA);
$validateC = $serviceNew->validate($keyC);
$validateB = $serviceNew->validate($keyB);

if (!$validateA || !$validateB || !$validateC) {
    $failures[] = 'validate()는 생성된 모든 키를 유효하다고 판정해야 한다.';
}

// 테스트 8: 빈 키 검증
if ($service->validate('')) {
    $failures[] = 'validate()는 빈 문자열을 유효하지 않다고 판정해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "IdempotencyKeyService 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "IdempotencyKeyService 테스트 통과.\n");
exit(0);
