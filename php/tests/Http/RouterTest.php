<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Router의 정적 route 매칭 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0396 RequestTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Router;

$failures = [];

$router = new Router();
$router->register('GET', '/', static fn (): string => 'home');
$router->register('GET', '/articles', static fn (): string => 'articles');

$homeMatch = $router->match(new Request('GET', '/'));
if ($homeMatch === null || $homeMatch() !== 'home') {
    $failures[] = '등록된 method와 path가 정확히 일치하면 해당 핸들러를 반환해야 한다.';
}

$caseInsensitiveMatch = $router->match(new Request('get', '/'));
if ($caseInsensitiveMatch === null || $caseInsensitiveMatch() !== 'home') {
    $failures[] = 'method 매칭은 대소문자를 구분하지 않아야 한다.';
}

$unknownPath = $router->match(new Request('GET', '/missing'));
if ($unknownPath !== null) {
    $failures[] = '등록되지 않은 path는 null을 반환해야 한다.';
}

$unknownMethod = $router->match(new Request('POST', '/'));
if ($unknownMethod !== null) {
    $failures[] = '등록되지 않은 method는 null을 반환해야 한다.';
}

$dynamicLikePath = $router->match(new Request('GET', '/articles/1'));
if ($dynamicLikePath !== null) {
    $failures[] = '정적 매칭만 지원하므로 등록된 path의 부분 문자열은 매칭되지 않아야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Router 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Router 테스트 통과.\n");
exit(0);
