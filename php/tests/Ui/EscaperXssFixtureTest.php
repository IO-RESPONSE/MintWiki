<?php

declare(strict_types=1);

/**
 * XSS fixture(tests/fixtures/xss/html_escaping.json)의 payload들을
 * MintWiki\Ui\Escaper에 통과시켜, HTML/attribute 문맥에서 위험한 raw
 * 마크업이 남지 않고 안전한 이스케이프 결과가 나오는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;

$fixturePath = __DIR__ . '/../fixtures/xss/html_escaping.json';

if (!is_file($fixturePath)) {
    fwrite(STDERR, "XSS fixture 파일을 찾을 수 없습니다: {$fixturePath}\n");
    exit(1);
}

$fixture = json_decode((string) file_get_contents($fixturePath), true);

if (!is_array($fixture) || !isset($fixture['cases']) || !is_array($fixture['cases'])) {
    fwrite(STDERR, "XSS fixture 형식이 올바르지 않습니다: {$fixturePath}\n");
    exit(1);
}

$failures = [];
$escaper = new Escaper();

foreach ($fixture['cases'] as $index => $case) {
    $name = is_array($case) && isset($case['name']) ? (string) $case['name'] : "case #{$index}";

    if (!is_array($case) || !array_key_exists('input', $case) || !array_key_exists('expected_html', $case)) {
        $failures[] = "{$name}: fixture case에는 input과 expected_html이 있어야 한다.";
        continue;
    }

    $input = (string) $case['input'];
    $expected = (string) $case['expected_html'];

    $actual = $escaper->html($input);
    if ($actual !== $expected) {
        $failures[] = "{$name}: html()이 기대한 이스케이프 결과와 다르다. expected={$expected}, actual={$actual}";
    }

    // attribute()는 html()과 동일한 이스케이프를 보장하므로 같은 fixture로 확인한다.
    if ($escaper->attribute($input) !== $expected) {
        $failures[] = "{$name}: attribute()도 html()과 동일하게 이스케이프해야 한다.";
    }

    // 이스케이프 결과에 활성화 가능한 raw 마크업 문자가 남으면 안 된다.
    foreach (['<', '>', '"'] as $dangerous) {
        if (str_contains($actual, $dangerous)) {
            $failures[] = "{$name}: 이스케이프 결과에 위험한 raw 문자 '{$dangerous}'가 남아 있다: {$actual}";
        }
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Escaper XSS fixture 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Escaper XSS fixture 테스트 통과.\n");
exit(0);
