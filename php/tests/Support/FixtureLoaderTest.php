<?php

declare(strict_types=1);

/**
 * MintWiki\Tests\Support\FixtureLoader의 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0406 Modules/Parser/
 * FixtureRunnerTest.php와 동일한 방식).
 *
 * 실제 저장소 루트의 `tests/modules/parser/fixtures/`,
 * `tests/fixtures/`를 대상으로 경로 계산/목록/로딩/에러 처리를
 * 검증한다 — 이 로더는 fixture 사본을 만들지 않고 두 언어가 공유하는
 * 같은 파일을 그대로 읽는다(`docs/php-parity-test-plan.md`).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/FixtureLoader.php';

use MintWiki\Tests\Support\FixtureLoader;

$failures = [];

$loader = new FixtureLoader();

// (1) repositoryRoot()는 실제 저장소 루트를 가리켜야 한다.
if (!is_dir($loader->repositoryRoot() . '/tests/modules')) {
    $failures[] = "repositoryRoot()가 저장소 루트를 가리키지 않는다: {$loader->repositoryRoot()}";
}

// (2) moduleFixtureDir()/sharedFixtureDir()는 기존 fixture 디렉터리와 일치해야 한다.
$parserDir = $loader->moduleFixtureDir('parser');
if (!is_dir($parserDir)) {
    $failures[] = "moduleFixtureDir('parser')가 존재하지 않는 경로를 반환했다: {$parserDir}";
}

$sharedDir = $loader->sharedFixtureDir();
if (!is_dir($sharedDir)) {
    $failures[] = "sharedFixtureDir()가 존재하지 않는 경로를 반환했다: {$sharedDir}";
}

// (3) listFixtures()는 .json 파일만, 알파벳 순으로 반환해야 한다.
$fixtures = $loader->listFixtures($parserDir);
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

// (4) loadFixture()는 schema_version/input/expected/errors 필드를 그대로 반환해야 한다.
$fixture = $loader->loadFixture($parserDir, 'heading_with_text.json');
if (($fixture['schema_version'] ?? null) !== '1.0') {
    $failures[] = 'loadFixture()는 schema_version 필드를 그대로 반환해야 한다.';
}
if (!isset($fixture['input'], $fixture['expected'], $fixture['errors'])) {
    $failures[] = 'loadFixture()는 input/expected/errors 필드를 모두 포함해야 한다.';
}

// (5) 다른 모듈(shared 디렉터리의 예시 fixture)에서도 동일하게 동작해야 한다.
$exampleDir = $sharedDir . '/schema/examples';
$exampleFixture = $loader->loadFixture($exampleDir, 'success_example.json');
if (!array_key_exists('expected', $exampleFixture)) {
    $failures[] = 'loadFixture()는 shared fixture 디렉터리에서도 동작해야 한다.';
}

// (6) 없는 파일은 RuntimeException을 던져야 한다.
try {
    $loader->loadFixture($parserDir, 'nonexistent_fixture.json');
    $failures[] = 'loadFixture()는 없는 파일에 대해 예외를 던져야 한다.';
} catch (\RuntimeException $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

if ($failures !== []) {
    fwrite(STDERR, "FixtureLoader 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "FixtureLoader 테스트 통과.\n");
exit(0);
