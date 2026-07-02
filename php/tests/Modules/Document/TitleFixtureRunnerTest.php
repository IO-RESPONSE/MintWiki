<?php

declare(strict_types=1);

/**
 * `tests/modules/document/fixtures/` 아래의 교차언어(cross-language) JSON
 * fixture(`docs/cross-language-fixture-schema.md`)를 읽어
 * `MintWiki\Document\Title::normalize()`를 검증하는 parity 러너
 * (`docs/php-parity-test-plan.md`의 0426 항목).
 *
 * `TitleTest.php`(0401)는 같은 시나리오 값을 손으로 옮겨 적었지만, 이
 * 파일은 fixture 파일 자체를 읽어 Python 쪽 test_title_fixtures.py와
 * 정확히 같은 입력을 실행한다 — fixture 를 고치면 두 언어 테스트가 다음
 * 실행에서 자동으로 같은 값을 집는다. JSON 로딩은 0425 Support/
 * FixtureLoader.php를 재사용하며 이 파일에서 다시 구현하지 않는다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/../../Support/FixtureLoader.php';

use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\Title;
use MintWiki\Tests\Support\FixtureLoader;

$failures = [];

$loader = new FixtureLoader();
$fixtureDir = $loader->moduleFixtureDir('document');

$fixtureNames = $loader->listFixtures($fixtureDir);
if ($fixtureNames === []) {
    $failures[] = "fixture 디렉터리에 .json 파일이 없습니다: {$fixtureDir}";
}

foreach ($fixtureNames as $fixtureName) {
    $fixture = $loader->loadFixture($fixtureDir, $fixtureName);
    $title = $fixture['input']['title'];

    if ($fixture['errors'] === []) {
        // 성공 케이스: normalize() 결과가 expected.title과 정확히 일치해야 한다.
        try {
            $actual = Title::normalize($title);
        } catch (EmptyTitleError $error) {
            $failures[] = "[{$fixtureName}] 성공이 기대되었지만 EmptyTitleError가 발생했습니다.";
            continue;
        }

        if ($actual !== $fixture['expected']['title']) {
            $failures[] = "[{$fixtureName}] 기대값 " . var_export($fixture['expected']['title'], true)
                . ", 실제값 " . var_export($actual, true);
        }
    } else {
        // 실패 케이스: expected는 null이어야 하고, 예외의 CODE가 errors와 일치해야 한다.
        if ($fixture['expected'] !== null) {
            $failures[] = "[{$fixtureName}] errors가 비어 있지 않은 fixture는 expected가 null이어야 합니다.";
        }

        try {
            Title::normalize($title);
            $failures[] = "[{$fixtureName}] EmptyTitleError를 던지지 않았습니다.";
        } catch (EmptyTitleError $error) {
            if (!in_array(EmptyTitleError::CODE, $fixture['errors'], true)) {
                $failures[] = "[{$fixtureName}] EmptyTitleError::CODE(" . EmptyTitleError::CODE
                    . ")가 fixture의 errors 목록에 없습니다.";
            }
        }
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Document Title FixtureRunner 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Document Title FixtureRunner 테스트 통과 (" . count($fixtureNames) . "개 fixture).\n");
exit(0);
