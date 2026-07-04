<?php

declare(strict_types=1);

/**
 * MintWiki\Jobs\WebTriggerGuard의 토큰 검증과 rate limit을 확인한다.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Jobs\WebTriggerGuard;

$failures = [];
$now = 1000;
$clock = static function () use (&$now): int {
    return $now;
};

$guard = new WebTriggerGuard('runner-secret', 2, 10, $clock);

if (!$guard->allows('runner-secret', '127.0.0.1')) {
    $failures[] = '올바른 토큰은 웹 잡 실행을 허용해야 한다.';
}

if ($guard->allows('wrong-secret', '127.0.0.1')) {
    $failures[] = '잘못된 토큰은 웹 잡 실행을 허용하면 안 된다.';
}

if ($guard->allows('runner-secret', '127.0.0.1')) {
    $failures[] = '같은 rate limit 윈도우에서 허용 횟수를 넘은 요청은 올바른 토큰이어도 차단해야 한다.';
}

if (!$guard->allows('runner-secret', '192.0.2.10')) {
    $failures[] = 'rate limit은 클라이언트 키별로 독립적으로 적용해야 한다.';
}

$now = 1011;

if (!$guard->allows('runner-secret', '127.0.0.1')) {
    $failures[] = 'rate limit 윈도우가 지나면 같은 클라이언트의 요청을 다시 허용해야 한다.';
}

$blankClientGuard = new WebTriggerGuard('runner-secret', 1, 10, $clock);

if (!$blankClientGuard->allows('runner-secret', '')) {
    $failures[] = '빈 클라이언트 키는 기본 버킷으로 처리해 첫 요청을 허용해야 한다.';
}

if ($blankClientGuard->allows('runner-secret', '   ')) {
    $failures[] = '공백 클라이언트 키는 같은 기본 버킷을 공유해 제한을 적용해야 한다.';
}

try {
    new WebTriggerGuard('');
    $failures[] = '비어 있는 비밀 토큰은 설정 오류로 거부해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 설정 차단이다.
}

try {
    new WebTriggerGuard('runner-secret', 0);
    $failures[] = '0 이하의 시도 제한은 설정 오류로 거부해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 설정 차단이다.
}

try {
    new WebTriggerGuard('runner-secret', 1, 0);
    $failures[] = '0 이하의 제한 윈도우는 설정 오류로 거부해야 한다.';
} catch (InvalidArgumentException) {
    // 기대한 설정 차단이다.
}

if ($failures !== []) {
    fwrite(STDERR, "WebTriggerGuard 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "WebTriggerGuard 테스트 통과.\n");
exit(0);
