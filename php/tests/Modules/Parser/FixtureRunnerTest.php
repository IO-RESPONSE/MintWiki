<?php

declare(strict_types=1);

/**
 * MintWiki\Tests\Parser\FixtureRunner의 로딩/실행 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0402
 * Modules/Document/RepositoryTest.php와 동일한 방식).
 *
 * parser 모듈의 PHP 포팅은 아직 placeholder(0399)이므로, 실제
 * `MintWiki\Parser` 클래스 대신 이 파일에서 정의한 스텁 콜백으로
 * run()의 비교 로직만 검증한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/FixtureRunner.php';

use MintWiki\Tests\Parser\FixtureRunner;

$failures = [];

$runner = new FixtureRunner();

if (!is_dir($runner->fixtureDir())) {
    $failures[] = "기본 fixture 디렉터리가 존재하지 않습니다: {$runner->fixtureDir()}";
}

$fixtures = $runner->listFixtures();
if ($fixtures === []) {
    $failures[] = 'listFixtures()는 최소 1개 이상의 fixture를 반환해야 한다.';
}
foreach ($fixtures as $name) {
    if (!str_ends_with($name, '.json')) {
        $failures[] = "listFixtures()는 .json 파일만 반환해야 하는데 '{$name}'을 포함했다.";
    }
}
$sorted = $fixtures;
sort($sorted);
if ($fixtures !== $sorted) {
    $failures[] = 'listFixtures()는 알파벳 순으로 정렬되어 반환되어야 한다.';
}

$fixture = $runner->loadFixture('heading_with_text.json');
if (($fixture['schema_version'] ?? null) !== '1.0') {
    $failures[] = "loadFixture()는 schema_version 필드를 그대로 반환해야 한다.";
}
if (!isset($fixture['input'], $fixture['expected'], $fixture['errors'])) {
    $failures[] = 'loadFixture()는 input/expected/errors 필드를 모두 포함해야 한다.';
}

try {
    $runner->loadFixture('nonexistent_fixture.json');
    $failures[] = 'loadFixture()는 없는 파일에 대해 예외를 던져야 한다.';
} catch (\RuntimeException $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

$expected = $fixture['expected'];
$passThrough = static fn (string $source): array => $expected;
$result = $runner->run('heading_with_text.json', $passThrough);
if ($result['success'] !== true) {
    $failures[] = 'run()은 콜백 결과가 expected와 일치하면 success=true를 반환해야 한다.';
}
if ($result['fixture'] !== 'heading_with_text.json') {
    $failures[] = 'run()은 결과에 사용된 fixture 파일명을 포함해야 한다.';
}

$wrongCallback = static fn (string $source): array => ['blocks' => [], 'metadata' => ['links' => [], 'categories' => [], 'headings' => []]];
$mismatch = $runner->run('heading_with_text.json', $wrongCallback);
if ($mismatch['success'] !== false) {
    $failures[] = 'run()은 콜백 결과가 expected와 다르면 success=false를 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Parser FixtureRunner 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Parser FixtureRunner 테스트 통과.\n");
exit(0);
