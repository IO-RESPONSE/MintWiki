<?php

declare(strict_types=1);

/**
 * MintWiki\App\AppBootstrap의 계약을 확인하는 smoke test.
 *
 * AppBootstrap이 다음을 정확히 수행하는지 검증한다:
 * (1) DB 설정(local-config.php)이 있으면 ConnectionConfig를 구성하고,
 *     주입한 connector를 통해 PDO를 생성하는지
 * (2) .env의 WIKI_DATABASE_URL만 있어도 ConnectionConfig를 구성하는지
 * (3) DB 설정이 전혀 없으면 예외 없이 null을 반환하는지("미설정" 상태)
 *
 * php CLI만으로 실행된다 (phpunit 없음, LocalConfigLoaderTest.php와 동일한
 * 방식). 실제 DB 서버에는 접속하지 않는다 — connector를 주입해 대체한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\AppBootstrap;
use MintWiki\Persistence\ConnectionConfig;

$failures = [];

$testDir = sys_get_temp_dir() . '/mint-wiki-bootstrap-test-' . uniqid();
mkdir($testDir, 0755, true);

try {
    // Test 1: 설정이 전혀 없으면 예외 없이 null을 반환해야 한다.
    $bootstrap = new AppBootstrap($testDir);

    if ($bootstrap->connectionConfig() !== null) {
        $failures[] = '설정이 없으면 connectionConfig()가 null을 반환해야 한다.';
    }
    if ($bootstrap->pdo() !== null) {
        $failures[] = '설정이 없으면 pdo()가 null을 반환해야 한다.';
    }

    // Test 2: local-config.php(driver/dsn/user/password)가 있으면
    // ConnectionConfig를 구성하고, 주입된 connector로 PDO를 생성해야 한다.
    file_put_contents($testDir . '/local-config.php', <<<'PHP'
<?php
return [
    'driver' => 'mysql',
    'dsn' => 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4',
    'user' => 'wiki_user',
    'password' => 'secret123',
];
PHP
    );

    $capturedConfig = null;
    $fakePdo = new PDO('sqlite::memory:');
    $connector = function (ConnectionConfig $config) use (&$capturedConfig, $fakePdo): PDO {
        $capturedConfig = $config;
        return $fakePdo;
    };

    $bootstrap = new AppBootstrap($testDir, $connector);
    $config = $bootstrap->connectionConfig();

    if (!$config instanceof ConnectionConfig) {
        $failures[] = 'local-config.php가 있으면 connectionConfig()가 ConnectionConfig를 반환해야 한다.';
    } else {
        if ($config->driver() !== 'mysql') {
            $failures[] = 'ConnectionConfig의 driver가 mysql이어야 한다.';
        }
        if ($config->host() !== 'db.example.com') {
            $failures[] = 'ConnectionConfig의 host가 DSN에서 파싱한 값이어야 한다.';
        }
        if ($config->port() !== 3306) {
            $failures[] = 'ConnectionConfig의 port가 DSN에서 파싱한 값이어야 한다.';
        }
        if ($config->database() !== 'wiki_engine') {
            $failures[] = 'ConnectionConfig의 database가 DSN에서 파싱한 값이어야 한다.';
        }
        if ($config->username() !== 'wiki_user') {
            $failures[] = 'ConnectionConfig의 username이 local-config.php의 user여야 한다.';
        }
        if ($config->password() !== 'secret123') {
            $failures[] = 'ConnectionConfig의 password가 local-config.php의 password여야 한다.';
        }
    }

    $pdo = $bootstrap->pdo();
    if ($pdo !== $fakePdo) {
        $failures[] = 'pdo()가 주입한 connector의 반환값을 그대로 반환해야 한다.';
    }
    if (!$capturedConfig instanceof ConnectionConfig) {
        $failures[] = 'pdo()가 connector에 ConnectionConfig를 전달해야 한다.';
    }

    // Test 3: .env의 WIKI_DATABASE_URL만 있어도(마리아DB 전용 DSN 없이도)
    // ConnectionConfig를 구성할 수 있어야 한다.
    @unlink($testDir . '/local-config.php');
    file_put_contents($testDir . '/.env', "WIKI_DATABASE_URL=mysql://url_user:url_pass@url-host:3307/url_db\n");

    $bootstrap = new AppBootstrap($testDir);
    $config = $bootstrap->connectionConfig();

    if (!$config instanceof ConnectionConfig) {
        $failures[] = 'WIKI_DATABASE_URL만 있어도 connectionConfig()가 ConnectionConfig를 반환해야 한다.';
    } else {
        if ($config->driver() !== 'mysql') {
            $failures[] = 'database_url의 mysql:// 스킴은 driver mysql로 매핑되어야 한다.';
        }
        if ($config->host() !== 'url-host') {
            $failures[] = 'database_url에서 host를 파싱해야 한다.';
        }
        if ($config->port() !== 3307) {
            $failures[] = 'database_url에서 port를 파싱해야 한다.';
        }
        if ($config->database() !== 'url_db') {
            $failures[] = 'database_url에서 database 이름을 파싱해야 한다.';
        }
        if ($config->username() !== 'url_user') {
            $failures[] = 'database_url에서 username을 파싱해야 한다.';
        }
        if ($config->password() !== 'url_pass') {
            $failures[] = 'database_url에서 password를 파싱해야 한다.';
        }
    }
} finally {
    @unlink($testDir . '/.env');
    @unlink($testDir . '/local-config.php');
    @rmdir($testDir);
}

if ($failures !== []) {
    fwrite(STDERR, "AppBootstrap 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AppBootstrap 테스트 통과.\n");
exit(0);
