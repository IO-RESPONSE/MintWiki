<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\DatabaseConfigWriter의 접속 시험/기록 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(InstallerLockTest.php와 동일한 방식).
 *
 * 검증 대상:
 * (1) testConnection()이 주입된 connector를 호출하는지, 실패 시 예외를 그대로
 *     전파하는지(호출자가 이를 잡아 "기록하지 않음" 처리를 하도록).
 * (2) write()가 임시 디렉터리에 local-config.php를 기록하고, 내용이
 *     database.php.sample과 동일한 배열 구조(driver/dsn/user/password/options)를
 *     가지는지 — @include로 다시 읽어 LocalConfigLoader가 읽는 형식과 같은지 확인한다.
 * (3) 기록된 파일의 권한이 0600으로 제한되는지.
 * (4) 접속 시험이 실패하면(예외) 아무 파일도 기록되지 않는지 — 호출자가 write()를
 *     호출하지 않는 흐름을 그대로 재현해 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\DatabaseConfigWriter;
use MintWiki\Persistence\ConnectionConfig;

$failures = [];
$tmpDir = sys_get_temp_dir() . '/mintwiki_db_config_writer_' . getmypid();

if (!mkdir($tmpDir, 0777, true) && !is_dir($tmpDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$tmpDir}\n");
    exit(1);
}

$connectionConfig = new ConnectionConfig('mysql', 'db.example.com', 3306, 'wiki_engine', 'wiki_user', 'sup3r-secret');

try {
    // (1) testConnection()은 주입된 connector를 호출하고, 실패 시 예외를 전파해야 한다.
    $calledWith = null;
    $failingWriter = new DatabaseConfigWriter($tmpDir, function (ConnectionConfig $config) use (&$calledWith): PDO {
        $calledWith = $config;
        throw new RuntimeException('접속 거부됨(테스트용)');
    });

    try {
        $failingWriter->testConnection($connectionConfig);
        $failures[] = 'connector가 예외를 던지면 testConnection()도 예외를 전파해야 한다.';
    } catch (RuntimeException $e) {
        if ($e->getMessage() !== '접속 거부됨(테스트용)') {
            $failures[] = 'testConnection()이 connector의 예외를 그대로 전파해야 한다.';
        }
    }

    if ($calledWith !== $connectionConfig) {
        $failures[] = 'testConnection()은 주입된 connector에 ConnectionConfig를 그대로 전달해야 한다.';
    }

    // (4) 접속 시험이 실패한 흐름에서는 write()를 호출하지 않았으므로 파일이 없어야 한다.
    if (is_file($failingWriter->path())) {
        $failures[] = '접속 시험이 실패했으면 local-config.php가 기록되어 있으면 안 된다.';
    }

    // (2)/(3) 접속 시험이 성공하면 write()가 올바른 구조/권한으로 파일을 기록해야 한다.
    $fakePdo = new PDO('sqlite::memory:');
    $succeedingWriter = new DatabaseConfigWriter($tmpDir, function () use ($fakePdo): PDO {
        return $fakePdo;
    });

    $succeedingWriter->testConnection($connectionConfig);
    $succeedingWriter->write($connectionConfig);

    $path = $succeedingWriter->path();
    if ($path !== $tmpDir . '/local-config.php') {
        $failures[] = 'path()는 configDir/local-config.php를 반환해야 한다.';
    }

    if (!is_file($path)) {
        $failures[] = 'write() 후 local-config.php 파일이 존재해야 한다.';
    } else {
        $permissions = fileperms($path) & 0777;
        if ($permissions !== 0600) {
            $failures[] = sprintf('local-config.php 권한은 0600이어야 하는데 %o였다.', $permissions);
        }

        $config = @include $path;
        if (!is_array($config)) {
            $failures[] = '기록된 local-config.php는 배열을 반환해야 한다.';
        } else {
            if (($config['driver'] ?? null) !== 'mysql') {
                $failures[] = '기록된 설정의 driver는 mysql이어야 한다.';
            }
            if (($config['dsn'] ?? null) !== 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4') {
                $failures[] = '기록된 설정의 dsn이 PdoConnectionFactory::dsn()과 동일해야 한다.';
            }
            if (($config['user'] ?? null) !== 'wiki_user') {
                $failures[] = '기록된 설정의 user가 입력한 사용자명과 같아야 한다.';
            }
            if (($config['password'] ?? null) !== 'sup3r-secret') {
                $failures[] = '기록된 설정의 password가 입력한 비밀번호와 같아야 한다.';
            }
            if (!isset($config['options'][PDO::ATTR_ERRMODE])) {
                $failures[] = '기록된 설정에 options.PDO::ATTR_ERRMODE가 있어야 한다.';
            }
        }

        $rawContents = (string) file_get_contents($path);
        if (str_contains($rawContents, 'sup3r-secret') === false) {
            // 비밀번호 자체는 파일에 존재해야 로컬 설정으로 기능하지만, 최소한 평문 그대로
            // 다른 필드(dsn 등)에 새어나가지 않았는지 확인한다.
            $failures[] = '기록된 파일에 비밀번호 값이 포함되어 있어야 한다(local-config.php 자체 목적).';
        }
        if (str_contains($rawContents, 'dsn') && str_contains($rawContents, 'sup3r-secret;')) {
            $failures[] = 'dsn 문자열에 비밀번호가 섞여 들어가면 안 된다.';
        }
    }
} finally {
    @unlink($tmpDir . '/local-config.php');
    @rmdir($tmpDir);
}

if ($failures !== []) {
    fwrite(STDERR, "DatabaseConfigWriter 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DatabaseConfigWriter 테스트 통과.\n");
exit(0);
