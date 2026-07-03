<?php

declare(strict_types=1);

/**
 * MintWiki\App\LocalConfigLoader의 계약을 확인하는 smoke test.
 *
 * LocalConfigLoader가 다음을 정확히 수행하는지 검증한다:
 * (1) .env 파일을 읽어서 key=value를 파싱하는지
 * (2) WIKI_ 접두어를 제거하는지
 * (3) local-config.php (PHP 배열 파일)을 로드하는지
 * (4) 주석 라인을 건너뛰는지
 * (5) 파일이 없으면 빈 배열을 반환하는지
 * (6) .env가 local-config.php보다 우선인지
 *
 * php CLI만으로 실행된다 (phpunit 없음, ConfigLoaderTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\LocalConfigLoader;

$failures = [];

// 임시 테스트 디렉토리 생성
$testDir = sys_get_temp_dir() . '/mint-wiki-config-test-' . uniqid();
mkdir($testDir, 0755, true);

try {
    // Test 1: 파일이 없으면 빈 배열 반환
    $loader = new LocalConfigLoader($testDir);
    $result = $loader->load();
    if ($result !== []) {
        $failures[] = '파일이 없을 때 빈 배열을 반환해야 한다.';
    }

    // Test 2: .env 파일 파싱 (WIKI_ 접두어 제거)
    $envFile = $testDir . '/.env';
    file_put_contents($envFile, <<<'ENV'
# 주석 라인은 스킵
WIKI_APP_NAME=test-wiki
WIKI_ENVIRONMENT=production
WIKI_MARIADB_DSN=mysql:host=localhost;dbname=test
# 또 다른 주석
INVALID_LINE_WITHOUT_EQUALS
WIKI_EMPTY_VALUE=
WIKI_STORAGE_PATH=/home/account/wiki-storage

# 빈 라인도 스킵

WIKI_DATABASE_URL=mysql://test:pass@localhost/db
ENV
    );

    $loader = new LocalConfigLoader($testDir);
    $result = $loader->load();

    if (($result['app_name'] ?? null) !== 'test-wiki') {
        $failures[] = '.env에서 WIKI_APP_NAME을 파싱해서 app_name (소문자, WIKI_ 제거)로 변환해야 한다.';
    }

    if (($result['environment'] ?? null) !== 'production') {
        $failures[] = '.env에서 WIKI_ENVIRONMENT를 파싱해야 한다.';
    }

    if (($result['mariadb_dsn'] ?? null) !== 'mysql:host=localhost;dbname=test') {
        $failures[] = '.env에서 WIKI_MARIADB_DSN을 파싱해야 한다.';
    }

    if (($result['database_url'] ?? null) !== 'mysql://test:pass@localhost/db') {
        $failures[] = '.env에서 WIKI_DATABASE_URL을 파싱해야 한다.';
    }

    if (($result['storage_path'] ?? null) !== '/home/account/wiki-storage') {
        $failures[] = '.env에서 WIKI_STORAGE_PATH를 파싱해야 한다.';
    }

    if (($result['empty_value'] ?? 'NOT_FOUND') === 'NOT_FOUND') {
        $failures[] = '.env에서 빈 값도 파싱해야 한다 (empty string로 설정).';
    }

    // Test 3: local-config.php 로드 (PHP 배열 반환 파일)
    // Test 2의 .env 파일 제거 후 독립적으로 테스트
    @unlink($envFile);

    $localConfigFile = $testDir . '/local-config.php';
    file_put_contents($localConfigFile, <<<'PHP'
<?php
return [
    'driver' => 'mysql',
    'dsn' => 'mysql:host=db.example.com;dbname=wiki_db;charset=utf8mb4',
    'user' => 'wiki_user',
    'password' => 'secret123',
    'app_name' => 'wiki-engine',
    'storage_path' => '/home/account/private/storage',
];
PHP
    );

    $loader = new LocalConfigLoader($testDir);
    $result = $loader->load();

    if (($result['mariadb_driver'] ?? null) !== 'mysql') {
        $failures[] = 'local-config.php에서 driver를 mariadb_driver로 매핑해야 한다.';
    }

    if (($result['mariadb_dsn'] ?? null) !== 'mysql:host=db.example.com;dbname=wiki_db;charset=utf8mb4') {
        $failures[] = 'local-config.php에서 dsn을 mariadb_dsn으로 매핑해야 한다.';
    }

    if (($result['mariadb_user'] ?? null) !== 'wiki_user') {
        $failures[] = 'local-config.php에서 user를 mariadb_user로 매핑해야 한다.';
    }

    if (($result['mariadb_password'] ?? null) !== 'secret123') {
        $failures[] = 'local-config.php에서 password를 mariadb_password로 매핑해야 한다.';
    }

    if (($result['app_name'] ?? null) !== 'wiki-engine') {
        $failures[] = 'local-config.php에서 app_name을 직접 매핑해야 한다.';
    }

    if (($result['storage_path'] ?? null) !== '/home/account/private/storage') {
        $failures[] = 'local-config.php에서 storage_path를 직접 매핑해야 한다.';
    }

    // Test 4: .env가 local-config.php보다 우선
    // local-config.php는 여전히 존재 (Test 3에서 생성함)
    file_put_contents($envFile, "WIKI_APP_NAME=env-override\nWIKI_ENVIRONMENT=test\n");

    $loader = new LocalConfigLoader($testDir);
    $result = $loader->load();

    if (($result['app_name'] ?? null) !== 'env-override') {
        $failures[] = '.env이 local-config.php보다 우선되어야 한다.';
    }

    if (($result['environment'] ?? null) !== 'test') {
        $failures[] = '.env의 값이 local-config.php의 값을 덮어써야 한다.';
    }

    // Test 5: 소문자 변환 확인
    if (($result['app_name'] ?? null) !== 'env-override' || ($result['WIKI_APP_NAME'] ?? 'NOT_FOUND') !== 'NOT_FOUND') {
        $failures[] = 'env 파일의 WIKI_로 시작하는 키는 소문자로 변환되어야 한다.';
    }

} finally {
    // 테스트 디렉토리 정리
    $files = @glob($testDir . '/*');
    if (is_array($files)) {
        foreach ($files as $file) {
            @unlink($file);
        }
    }
    @rmdir($testDir);
}

if ($failures !== []) {
    fwrite(STDERR, "LocalConfigLoader 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LocalConfigLoader 테스트 통과.\n");
exit(0);
