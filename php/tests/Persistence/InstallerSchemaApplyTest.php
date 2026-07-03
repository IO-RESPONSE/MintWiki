<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\SchemaApply의 dry-run/confirm placeholder 흐름을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\SchemaApply;

$failures = [];

try {
    $schemaApply = new SchemaApply();
} catch (Exception $e) {
    $failures[] = 'SchemaApply 초기화 실패: ' . $e->getMessage();
}

$schemaApply = new SchemaApply();

try {
    $result = $schemaApply->apply(true);

    if (($result['mode'] ?? null) !== 'dry-run') {
        $failures[] = 'dry-run 모드는 mode=dry-run을 반환해야 한다.';
    }
    if (($result['confirmed'] ?? null) !== false) {
        $failures[] = 'dry-run 모드는 confirmed=false를 반환해야 한다.';
    }
    if (($result['applied'] ?? null) !== false) {
        $failures[] = 'dry-run 모드는 실제 적용하지 않아야 한다.';
    }
} catch (Exception $e) {
    $failures[] = 'dry-run 적용 요청이 예외를 던지면 안 된다: ' . $e->getMessage();
}

try {
    $schemaApply->apply(false, false);
    $failures[] = '확인 없는 실제 적용 요청은 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    if (strpos($e->getMessage(), '확인') === false) {
        $failures[] = '확인 누락 예외 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = '확인 없는 실제 적용 요청이 예상하지 않은 예외를 던졌다: ' . get_class($e);
}

try {
    $result = $schemaApply->apply(false, true);

    if (($result['mode'] ?? null) !== 'confirm') {
        $failures[] = '확인된 적용 요청은 mode=confirm을 반환해야 한다.';
    }
    if (($result['confirmed'] ?? null) !== true) {
        $failures[] = '확인된 적용 요청은 confirmed=true를 반환해야 한다.';
    }
    if (($result['applied'] ?? null) !== false) {
        $failures[] = 'placeholder는 아직 실제 스키마를 적용하면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '확인된 적용 요청이 예외를 던지면 안 된다: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "Installer SchemaApply 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer SchemaApply 테스트 통과.\n");
exit(0);
