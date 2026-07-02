<?php

declare(strict_types=1);

/**
 * composer.json 의 PSR-4 오토로드 설정("MintWiki\\" => "src/")이
 * `composer install`이 생성한 vendor/autoload.php 를 통해 실제로
 * 등록되는지 확인하는 smoke test. phpunit 등 외부 테스트 프레임워크
 * 없이 `php` CLI만으로 실행되며, composer.json 에 패키지 의존성이
 * 없으므로 `composer install` 자체도 네트워크 접근 없이 끝난다.
 */

$autoloadFile = __DIR__ . '/../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

/** @var mixed $classLoader */
$classLoader = require $autoloadFile;

$failures = [];

if (!$classLoader instanceof Composer\Autoload\ClassLoader) {
    $failures[] = 'vendor/autoload.php가 Composer\\Autoload\\ClassLoader 인스턴스를 반환하지 않았습니다.';
} else {
    $expectedPrefix = 'MintWiki\\';
    $expectedDir = realpath(__DIR__ . '/../src');
    $psr4 = $classLoader->getPrefixesPsr4();

    if (!array_key_exists($expectedPrefix, $psr4)) {
        $failures[] = "PSR-4 접두사 '{$expectedPrefix}'가 등록되어 있지 않습니다.";
    } else {
        $registeredDirs = array_map('realpath', $psr4[$expectedPrefix]);
        if (!in_array($expectedDir, $registeredDirs, true)) {
            $failures[] = "PSR-4 접두사 '{$expectedPrefix}'가 예상 디렉터리(src/)로 매핑되어 있지 않습니다.";
        }
    }
}

if ($failures !== []) {
    fwrite(STDERR, "Autoload smoke test 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Autoload smoke test 통과: MintWiki\\ => src/ PSR-4 매핑 확인 완료.\n");
exit(0);
