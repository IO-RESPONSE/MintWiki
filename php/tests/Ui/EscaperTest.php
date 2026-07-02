<?php

declare(strict_types=1);

/**
 * MintWiki\Ui\Escaper의 HTML/attribute escaping 동작을 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Ui\Escaper;

$failures = [];
$escaper = new Escaper();

if ($escaper->html('<script>alert("x")</script>') !== '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;') {
    $failures[] = 'html()은 태그와 따옴표를 escape해야 한다.';
}

if ($escaper->html("Bob's page") !== 'Bob&#039;s page') {
    $failures[] = 'html()은 작은따옴표를 escape해야 한다.';
}

if ($escaper->attribute('ko" onload="x') !== 'ko&quot; onload=&quot;x') {
    $failures[] = 'attribute()는 HTML attribute 값에 안전한 문자열을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Escaper 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Escaper 테스트 통과.\n");
exit(0);
