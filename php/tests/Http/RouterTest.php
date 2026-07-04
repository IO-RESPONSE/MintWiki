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
    $failures[] = '"/articles"만 등록한 상태에서는 "/articles/1"이 매칭되지 않아야 한다.';
}

// 동적 세그먼트 매칭 (태스크 0675)

$dynamicRouter = new Router();
$dynamicRouter->register('GET', '/wiki/{title}', static fn (array $params): string => "wiki:{$params['title']}");
$dynamicRouter->register('GET', '/articles/{id}/comments/{commentId}', static fn (array $params): string => "{$params['id']}/{$params['commentId']}");
$dynamicRouter->register('GET', '/articles', static fn (): string => 'articles-index');

$wikiMatch = $dynamicRouter->match(new Request('GET', '/wiki/HomePage'));
if ($wikiMatch === null || $wikiMatch() !== 'wiki:HomePage') {
    $failures[] = '`{title}` 세그먼트는 실제 값으로 치환되어 매칭되고, 핸들러가 해당 값을 받아야 한다.';
}

$multiSegmentMatch = $dynamicRouter->match(new Request('GET', '/articles/42/comments/7'));
if ($multiSegmentMatch === null || $multiSegmentMatch() !== '42/7') {
    $failures[] = '여러 개의 동적 세그먼트를 모두 추출해 핸들러에 전달해야 한다.';
}

$staticPriorityMatch = $dynamicRouter->match(new Request('GET', '/articles'));
if ($staticPriorityMatch === null || $staticPriorityMatch() !== 'articles-index') {
    $failures[] = '정적 route가 동적 route보다 우선해야 한다.';
}

$segmentCountMismatch = $dynamicRouter->match(new Request('GET', '/wiki/HomePage/extra'));
if ($segmentCountMismatch !== null) {
    $failures[] = '세그먼트 개수가 다르면 동적 route도 매칭되지 않아야 한다.';
}

$noMatch = $dynamicRouter->match(new Request('GET', '/unknown/path'));
if ($noMatch !== null) {
    $failures[] = '어떤 route와도 일치하지 않으면 null을 반환해야 한다.';
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
