<?php

declare(strict_types=1);

/**
 * `docs/php-parity-test-plan.md` 4번 항목("아직 포팅되지 않은 모듈의
 * 처리")이 0428/0429 에서 확정하라고 남겨둔 **expected-failure 정책**을
 * render 모듈에 적용한 placeholder parity 테스트.
 * `Modules/Parser/ParityPlaceholderTest.php`(0428)와 같은 세 단계
 * 관용구를 따르되, guard 2 만 render 사정에 맞게 다르다 — parser 는
 * manifest 의 `repository.interface`(`PlainTextBlockParser`)가 미래
 * 클래스 이름을 그대로 가리키지만, render 는 단일 진입 클래스가 없고
 * `src/modules/render/__init__.py` 가 재노출하는 순수 함수 집합
 * (`escape_html`, `sanitize_url`, `render_heading` 등)이 공개 계약이라
 * (manifest `contract_notes` 참고) 미래 클래스 이름을 하나로 특정할 수
 * 없다. 대신 `php/src/Modules/Render/README.md`가 이미 고정한 사실 —
 * "이 파일 외에는 아직 클래스가 없다" — 을 그대로 검증 항목으로 쓴다.
 *
 * ## Expected-failure 정책 (이 파일이 고정하는 관용구)
 *
 * `src/modules/<module>/manifest.json`의 `port.status`가 `ready`가 아닌
 * 동안에는, 그 모듈의 parity 테스트는 실제 PHP 포트를 호출해 fixture와
 * 비교할 수 없다 — 비교 대상 클래스 자체가 없기 때문이다. 이런 모듈은
 * 다음 세 가지를 하는 placeholder 테스트로 대신한다(pass/fail 판정은
 * 이 세 가지에만 걸리고, "아직 렌더링 결과가 다르다"는 절대 실패로
 * 집계하지 않는다):
 *
 * 1. **가드**: manifest의 `port.status`가 지금도 `not_started`인지
 *    확인한다. 이 값이 바뀌면(포팅 착수) 가드가 즉시 실패해, 이 placeholder
 *    를 0426/0427(document/acl)처럼 실제 fixture 비교 테스트로 교체하라는
 *    신호를 준다 — 조용히 낡은 placeholder로 남지 않는다.
 * 2. **expected failure 고정**: `php/src/Modules/Render` 아래에 아직
 *    `.php` 클래스 파일이 하나도 없음을 명시적으로 확인한다. 즉 "포트가
 *    없어서 비교를 건너뛴다"는 사실 자체를 하나의 검증 항목으로 만들어,
 *    실수로 클래스만 추가되고 이 테스트가 갱신되지 않는 상황을 잡아낸다.
 * 3. **fixture 무결성만 검증**: 실제 렌더링 결과 비교 없이, 0425
 *    `Support/FixtureLoader`로 `tests/modules/render/fixtures/`의 모든
 *    `.json` fixture가 `docs/cross-language-fixture-schema.md` 구조
 *    (`schema_version`/`input`/`expected`/`errors`)를 지키는지만
 *    확인한다. render fixture는 함수마다 `input`의 형태가 달라
 *    (`escape_html`은 `{text}`, `render_heading`은 `{level, content}`)
 *    parser placeholder처럼 `input.source`가 문자열인지는 검사하지
 *    않는다. 포트가 준비되기 전에 fixture 자체가 깨지는 것을 조기에
 *    잡기 위함이며, 렌더링 동작의 parity 판정은 하지 않는다.
 *
 * 포트가 `ready`로 바뀌면 이 파일 전체를 0426(`TitleFixtureRunnerTest.php`)
 * 패턴을 따르는 실제 parity 테스트로 교체해야 한다 — 이 파일을 남겨둔 채
 * 조건만 느슨하게 고치지 않는다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;
require __DIR__ . '/../../Support/FixtureLoader.php';

use MintWiki\Tests\Support\FixtureLoader;

const EXPECTED_PORT_STATUS = 'not_started';

/**
 * `$dir` 아래(하위 디렉터리 포함)의 `.php` 파일명을 모두 모은다.
 *
 * @return list<string>
 */
function collectPhpFiles(string $dir): array
{
    if (!is_dir($dir)) {
        return [];
    }

    $found = [];
    foreach (scandir($dir) ?: [] as $entry) {
        if ($entry === '.' || $entry === '..') {
            continue;
        }

        $path = $dir . '/' . $entry;
        if (is_dir($path)) {
            $found = array_merge($found, collectPhpFiles($path));
        } elseif (str_ends_with($entry, '.php')) {
            $found[] = $path;
        }
    }

    return $found;
}

$failures = [];

$loader = new FixtureLoader();
$manifestPath = $loader->repositoryRoot() . '/src/modules/render/manifest.json';

if (!is_file($manifestPath)) {
    $failures[] = "render manifest 파일을 찾을 수 없습니다: {$manifestPath}";
} else {
    $manifest = json_decode((string) file_get_contents($manifestPath), true);
    if (!is_array($manifest)) {
        $failures[] = "render manifest 파일이 올바른 JSON 객체가 아닙니다: {$manifestPath}";
    } else {
        $actualStatus = $manifest['port']['status'] ?? null;
        // 1. 가드: 이 placeholder는 port.status가 not_started일 때만 유효하다.
        if ($actualStatus !== EXPECTED_PORT_STATUS) {
            $failures[] = "render manifest의 port.status가 '" . EXPECTED_PORT_STATUS
                . "'가 아니라 '{$actualStatus}'입니다 — render 포트가 진행된 것으로 보이므로 "
                . "이 placeholder 테스트를 0426/0427 패턴의 실제 fixture parity 테스트로 교체해야 합니다.";
        }
    }
}

// 2. expected failure 고정: render 네임스페이스에 클래스가 아직 없다는 사실 자체를 검증한다.
$renderSrcDir = $loader->repositoryRoot() . '/php/src/Modules/Render';
$existingPhpFiles = collectPhpFiles($renderSrcDir);
if ($existingPhpFiles !== []) {
    $failures[] = 'php/src/Modules/Render 아래에 .php 클래스 파일이 이미 존재합니다 ('
        . implode(', ', $existingPhpFiles) . ') — render 포트가 시작된 것으로 보이므로 '
        . '이 placeholder 테스트를 실제 parity 비교 테스트로 교체해야 합니다.';
}

// 3. fixture 무결성만 검증 (렌더링 결과 비교는 하지 않는다).
$fixtureDir = $loader->moduleFixtureDir('render');
$fixtureNames = $loader->listFixtures($fixtureDir);

if ($fixtureNames === []) {
    $failures[] = "fixture 디렉터리에 .json 파일이 없습니다: {$fixtureDir}";
}

foreach ($fixtureNames as $fixtureName) {
    $fixture = $loader->loadFixture($fixtureDir, $fixtureName);

    if (($fixture['schema_version'] ?? null) === null) {
        $failures[] = "[{$fixtureName}] schema_version 필드가 없습니다.";
    }
    if (!isset($fixture['input'], $fixture['expected'], $fixture['errors'])) {
        $failures[] = "[{$fixtureName}] input/expected/errors 필드를 모두 포함해야 합니다.";
        continue;
    }
    if (!is_array($fixture['errors'])) {
        $failures[] = "[{$fixtureName}] errors 필드는 배열이어야 합니다.";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Render Parity Placeholder 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(
    STDOUT,
    "Render Parity Placeholder 테스트 통과 — port.status=" . EXPECTED_PORT_STATUS
        . ", expected-failure(placeholder): " . count($fixtureNames) . "개 fixture (실제 렌더링 비교 없음).\n"
);
exit(0);
