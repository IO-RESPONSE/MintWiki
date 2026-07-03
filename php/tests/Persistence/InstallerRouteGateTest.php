<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\InstallerRouteGate의 설치 라우트 접근 제어 기능을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 in-memory SQLite를 사용하여 설치 상태 확인 로직을 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Installer\DBCheck;

$failures = [];

// InstallerRouteGate 초기화 테스트 - 설치 미완료 상태
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $gate = new InstallerRouteGate($connection);
    if ($gate === null) {
        $failures[] = 'InstallerRouteGate 초기화가 실패했다.';
    }
} catch (Exception $e) {
    $failures[] = "InstallerRouteGate 초기화 실패: " . $e->getMessage();
}

// 설치 미완료 상태 - schema_version 테이블이 없을 때
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $gate = new InstallerRouteGate($connection);

    if ($gate->isInstallationComplete()) {
        $failures[] = '스키마 버전 테이블이 없을 때 isInstallationComplete()은 false를 반환해야 한다.';
    }

    if (!$gate->canAccessInstallerRoute()) {
        $failures[] = '스키마 버전 테이블이 없을 때 canAccessInstallerRoute()는 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "설치 미완료 상태 테스트 실패: " . $e->getMessage();
}

// 설치 미완료 상태 - schema_version 테이블이 있지만 비어있을 때
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');

    $gate = new InstallerRouteGate($connection);

    if ($gate->isInstallationComplete()) {
        $failures[] = '스키마 버전 테이블이 비어있을 때 isInstallationComplete()는 false를 반환해야 한다.';
    }

    if (!$gate->canAccessInstallerRoute()) {
        $failures[] = '스키마 버전 테이블이 비어있을 때 canAccessInstallerRoute()는 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "설치 미완료 상태(빈 테이블) 테스트 실패: " . $e->getMessage();
}

// 설치 완료 상태 - schema_version 테이블에 1개 이상의 데이터가 있을 때
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");

    $gate = new InstallerRouteGate($connection);

    if (!$gate->isInstallationComplete()) {
        $failures[] = '스키마 버전 데이터가 1개 있을 때 isInstallationComplete()는 true를 반환해야 한다.';
    }

    if ($gate->canAccessInstallerRoute()) {
        $failures[] = '스키마 버전 데이터가 1개 있을 때 canAccessInstallerRoute()는 false를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "설치 완료 상태 테스트 실패: " . $e->getMessage();
}

// 설치 완료 상태 - schema_version 테이블에 여러 개의 데이터가 있을 때
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.2.0', '2026-07-02T01:00:00Z')");

    $gate = new InstallerRouteGate($connection);

    if (!$gate->isInstallationComplete()) {
        $failures[] = '스키마 버전 데이터가 여러 개 있을 때 isInstallationComplete()는 true를 반환해야 한다.';
    }

    if ($gate->canAccessInstallerRoute()) {
        $failures[] = '스키마 버전 데이터가 여러 개 있을 때 canAccessInstallerRoute()는 false를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "설치 완료 상태(여러 데이터) 테스트 실패: " . $e->getMessage();
}

// createBlockedResponse() 테스트 - HTTP 403 응답 확인
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");

    $gate = new InstallerRouteGate($connection);
    $response = $gate->createBlockedResponse();

    if ($response->status() !== 403) {
        $failures[] = 'createBlockedResponse()는 HTTP 403 상태를 반환해야 한다.';
    }

    $body = json_decode($response->body(), true);
    if (!isset($body['error']) || $body['error'] !== 'installation_already_complete') {
        $failures[] = 'createBlockedResponse()는 error 필드에 "installation_already_complete"을 포함해야 한다.';
    }

    if (!isset($body['message'])) {
        $failures[] = 'createBlockedResponse()는 message 필드를 포함해야 한다.';
    }

    $headers = $response->headers();
    if (($headers['Content-Type'] ?? null) !== 'application/json') {
        $failures[] = 'createBlockedResponse()는 Content-Type을 application/json으로 설정해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "createBlockedResponse() 테스트 실패: " . $e->getMessage();
}

// InstallerRouteGate에 커스텀 DBCheck를 주입할 수 있는지 확인
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $dbCheck = new DBCheck();
    $gate = new InstallerRouteGate($connection, $dbCheck);

    if ($gate === null) {
        $failures[] = 'InstallerRouteGate 생성자에 커스텀 DBCheck를 주입할 수 없다.';
    }
} catch (Exception $e) {
    $failures[] = "커스텀 DBCheck 주입 테스트 실패: " . $e->getMessage();
}

// 테스트 결과 출력
if ($failures !== []) {
    fwrite(STDERR, "Installer InstallerRouteGate 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer InstallerRouteGate 테스트 통과.\n");
exit(0);
