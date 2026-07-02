<?php

declare(strict_types=1);

/**
 * MintWiki\App\ErrorCodeRegistry의 계약을 확인하는 smoke test. phpunit
 * 없이 `php` CLI만으로 실행된다 (0415 ConfigLoaderTest.php와 동일한 방식).
 *
 * (1) document 모듈의 세 code가 Python
 * `tests/modules/document/test_error_codes.py`와 이름이 같은 문자열로
 * 등록되어 있는지, (2) 등록된 code가 유일한지, (3) 등록된 code가 모두
 * `<module>.<reason>` 형식을 따르는지, (4) 형식에 맞지 않는 문자열은
 * `isValidFormat()`이 거부하는지만 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ErrorCodeRegistry;

$failures = [];

// (1) document 모듈 code는 Python test_error_codes.py와 이름이 같아야 한다.
$expectedCodes = [
    'document.empty_title',
    'document.duplicate_title',
    'document.not_found',
];

foreach ($expectedCodes as $expectedCode) {
    if (!ErrorCodeRegistry::has($expectedCode)) {
        $failures[] = "registry에 {$expectedCode}가 등록되어 있어야 한다.";
    }
}

// (2) 등록된 code는 서로 유일해야 한다.
$allCodes = ErrorCodeRegistry::all();
if (count($allCodes) !== count(array_unique($allCodes))) {
    $failures[] = 'registry에 등록된 code는 서로 유일해야 한다.';
}

if ($allCodes !== $expectedCodes) {
    $failures[] = 'registry가 등록한 code 목록이 예상과 다르다.';
}

// (3) 등록된 code는 모두 <module>.<reason> 형식을 따라야 한다.
foreach ($allCodes as $code) {
    if (!ErrorCodeRegistry::isValidFormat($code)) {
        $failures[] = "등록된 code {$code}는 <module>.<reason> 형식을 따라야 한다.";
    }
}

// (4) 형식에 맞지 않는 문자열은 거부해야 한다.
$invalidCodes = [
    'document',
    'Document.not_found',
    'document.',
    '.not_found',
    'document..not_found',
    'document-not_found',
    'document.not-found',
];

foreach ($invalidCodes as $invalidCode) {
    if (ErrorCodeRegistry::isValidFormat($invalidCode)) {
        $failures[] = "{$invalidCode}는 형식에 맞지 않으므로 거부되어야 한다.";
    }
}

if (ErrorCodeRegistry::has('document.does_not_exist')) {
    $failures[] = '등록되지 않은 code는 has()가 false를 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ErrorCodeRegistry 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ErrorCodeRegistry 테스트 통과.\n");
exit(0);
