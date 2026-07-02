<?php

declare(strict_types=1);

/**
 * `tests/modules/acl/fixtures/` 아래의 교차언어(cross-language) JSON
 * fixture(`docs/cross-language-fixture-schema.md`)를 읽어
 * `MintWiki\Acl\Decision` 이 표현하는 `reason` code가 Python
 * `tests/modules/acl/test_decision_code_fixtures.py`와 같은 값으로
 * 고정되어 있는지 검증하는 parity 러너(`docs/php-parity-test-plan.md`의
 * 0427 항목).
 *
 * `src/modules/acl/manifest.json`의 `port.status`가 아직 `not_started`라서
 * PHP 쪽에는 규칙을 평가하는 `AclService`가 없다(0399 README 참고).
 * 그래서 이 러너는 `AclService::check()`를 호출하는 대신, fixture의
 * `expected` 필드로 `Decision` value object(0408)를 직접 구성해
 * getter가 fixture 값을 그대로 돌려주는지 확인하고, 모든 fixture가
 * `acl.matched_rule`/`acl.no_matching_rule` 두 code만 쓰는지 고정한다.
 * 규칙 평가 로직 자체의 parity는 `AclService`가 포팅된 이후 태스크의
 * 범위다. JSON 로딩은 0425 Support/FixtureLoader.php를 재사용한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/../../Support/FixtureLoader.php';

use MintWiki\Acl\Decision;
use MintWiki\Tests\Support\FixtureLoader;

const EXPECTED_REASON_CODES = ['acl.matched_rule', 'acl.no_matching_rule'];

$failures = [];

$loader = new FixtureLoader();
$fixtureDir = $loader->moduleFixtureDir('acl');

$fixtureNames = $loader->listFixtures($fixtureDir);
if ($fixtureNames === []) {
    $failures[] = "fixture 디렉터리에 .json 파일이 없습니다: {$fixtureDir}";
}

$seenReasons = [];

foreach ($fixtureNames as $fixtureName) {
    $fixture = $loader->loadFixture($fixtureDir, $fixtureName);

    if ($fixture['errors'] !== []) {
        $failures[] = "[{$fixtureName}] ACL decision code fixture는 errors가 항상 빈 배열이어야 한다.";
        continue;
    }

    $expected = $fixture['expected'];
    $decision = new Decision(
        $fixture['input']['permission'],
        $expected['allowed'],
        $expected['reason'],
        $expected['matched_rule_id']
    );

    if ($decision->permission() !== $fixture['input']['permission']) {
        $failures[] = "[{$fixtureName}] permission()이 fixture input.permission과 일치하지 않았다.";
    }
    if ($decision->isAllowed() !== $expected['allowed']) {
        $failures[] = "[{$fixtureName}] isAllowed()가 fixture expected.allowed와 일치하지 않았다.";
    }
    if ($decision->reason() !== $expected['reason']) {
        $failures[] = "[{$fixtureName}] reason()이 fixture expected.reason과 일치하지 않았다.";
    }
    if ($decision->matchedRuleId() !== $expected['matched_rule_id']) {
        $failures[] = "[{$fixtureName}] matchedRuleId()가 fixture expected.matched_rule_id와 일치하지 않았다.";
    }

    $seenReasons[$expected['reason']] = true;
}

// fixture 전체가 정확히 acl.matched_rule / acl.no_matching_rule 두 code만 써야 한다.
$seenReasonList = array_keys($seenReasons);
sort($seenReasonList);
$expectedReasonList = EXPECTED_REASON_CODES;
sort($expectedReasonList);
if ($fixtureNames !== [] && $seenReasonList !== $expectedReasonList) {
    $failures[] = 'fixture들이 사용하는 reason code 집합이 [' . implode(', ', $expectedReasonList)
        . ']와 일치하지 않는다. 실제: [' . implode(', ', $seenReasonList) . ']';
}

// reason code는 <module>.<reason> 형식(소문자, acl. 접두사)을 따라야 한다.
foreach (EXPECTED_REASON_CODES as $reasonCode) {
    if (!str_starts_with($reasonCode, 'acl.')) {
        $failures[] = "reason code '{$reasonCode}'는 'acl.' 접두사로 시작해야 한다.";
    }
    if ($reasonCode !== strtolower($reasonCode)) {
        $failures[] = "reason code '{$reasonCode}'는 소문자여야 한다.";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "ACL Decision Code FixtureRunner 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ACL Decision Code FixtureRunner 테스트 통과 (" . count($fixtureNames) . "개 fixture).\n");
exit(0);
