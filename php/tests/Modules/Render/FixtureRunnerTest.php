<?php

declare(strict_types=1);

/**
 * MintWiki\Tests\Render\FixtureRunner의 로딩/실행 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0406
 * Modules/Parser/FixtureRunnerTest.php와 동일한 방식).
 *
 * render 모듈의 PHP 포팅은 아직 placeholder(0399)이므로, 실제
 * `MintWiki\Render` 함수 대신 이 파일에서 정의한 스텁 콜백으로 run()의
 * 비교 로직만 검증한다. render fixture는 함수마다 `input`/`expected`의
 * 형태가 다르므로(`render_heading__generates_id_from_spaced_text.json`은
 * `{level, content}` -> `{html}`), 콜백이 `input` 배열에서 필요한 필드를
 * 직접 꺼내 쓰는 방식으로 검증한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/FixtureRunner.php';

use MintWiki\Tests\Render\FixtureRunner;

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

$fixtureName = 'render_heading__generates_id_from_spaced_text.json';
$fixture = $runner->loadFixture($fixtureName);
if (($fixture['schema_version'] ?? null) !== '1.0') {
    $failures[] = "loadFixture()는 schema_version 필드를 그대로 반환해야 한다.";
}
if (!isset($fixture['input'], $fixture['expected'], $fixture['errors'])) {
    $failures[] = 'loadFixture()는 input/expected/errors 필드를 모두 포함해야 한다.';
}
if (($fixture['expected']['html'] ?? null) === null) {
    $failures[] = 'render fixture의 expected는 html 키를 가진 배열이어야 한다.';
}

try {
    $runner->loadFixture('nonexistent_fixture.json');
    $failures[] = 'loadFixture()는 없는 파일에 대해 예외를 던져야 한다.';
} catch (\RuntimeException $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

$renderHeadingStub = static function (array $input): array {
    return ['html' => "<h{$input['level']} id=\"hello-world\">{$input['content']}</h{$input['level']}>"];
};
$result = $runner->run($fixtureName, $renderHeadingStub);
if ($result['success'] !== true) {
    $failures[] = 'run()은 콜백 결과가 expected와 일치하면 success=true를 반환해야 한다.';
}
if ($result['fixture'] !== $fixtureName) {
    $failures[] = 'run()은 결과에 사용된 fixture 파일명을 포함해야 한다.';
}

$wrongCallback = static fn (array $input): array => ['html' => '<h2>다른 내용</h2>'];
$mismatch = $runner->run($fixtureName, $wrongCallback);
if ($mismatch['success'] !== false) {
    $failures[] = 'run()은 콜백 결과가 expected와 다르면 success=false를 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Render FixtureRunner 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Render FixtureRunner 테스트 통과.\n");
exit(0);
