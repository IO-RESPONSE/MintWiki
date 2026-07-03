<?php

declare(strict_types=1);

/**
 * MintWiki\App 이메일 어댑터 뼈대의 오토로드와 no-op 계약을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\EmailAdapter;
use MintWiki\App\NullEmailAdapter;

$failures = [];

if (!interface_exists(EmailAdapter::class)) {
    $failures[] = 'EmailAdapter 인터페이스가 오토로드되어야 한다.';
}

$adapter = new NullEmailAdapter();

if (!$adapter instanceof EmailAdapter) {
    $failures[] = 'NullEmailAdapter는 EmailAdapter를 구현해야 한다.';
}

$result = $adapter->send('admin@example.test', '테스트 제목', '테스트 본문');
if ($result !== null) {
    $failures[] = 'NullEmailAdapter::send는 값을 반환하지 않아야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "EmailAdapter 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "EmailAdapter 테스트 통과.\n");
exit(0);
