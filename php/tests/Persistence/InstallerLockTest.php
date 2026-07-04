<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\InstallerLock의 설치 완료 lock file 정책을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\InstallerLock;
use MintWiki\Installer\InstallerRouteGate;

$failures = [];
$tmpDir = sys_get_temp_dir() . '/mintwiki_installer_lock_' . getmypid();

if (!mkdir($tmpDir, 0777, true) && !is_dir($tmpDir)) {
    fwrite(STDERR, "installer lock 테스트 디렉터리를 만들 수 없습니다: {$tmpDir}\n");
    exit(1);
}

$lockPath = $tmpDir . '/' . InstallerLock::DEFAULT_FILENAME;

try {
    $lock = new InstallerLock($lockPath);

    if ($lock->path() !== $lockPath) {
        $failures[] = 'InstallerLock은 생성자에 전달한 lock 파일 경로를 보존해야 한다.';
    }

    if ($lock->isLocked()) {
        $failures[] = 'lock 파일이 없으면 isLocked()는 false를 반환해야 한다.';
    }

    $lock->markComplete(new DateTimeImmutable('2026-07-04T00:00:00+00:00'));

    if (!$lock->isLocked()) {
        $failures[] = 'markComplete() 후 isLocked()는 true를 반환해야 한다.';
    }

    $payload = json_decode((string) file_get_contents($lockPath), true);
    if (($payload['status'] ?? null) !== 'complete') {
        $failures[] = 'lock 파일은 status=complete를 기록해야 한다.';
    }
    if (($payload['completed_at'] ?? null) !== '2026-07-04T00:00:00+00:00') {
        $failures[] = 'lock 파일은 완료 시각을 DATE_ATOM 형식으로 기록해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = 'InstallerLock 완료 표시 테스트 실패: ' . $e->getMessage();
}

try {
    $missingLock = new InstallerLock($tmpDir . '/missing/storage/' . InstallerLock::DEFAULT_FILENAME);
    $missingLock->markComplete();
    $failures[] = '존재하지 않는 디렉터리에는 lock 파일을 만들면 안 된다.';
} catch (RuntimeException $e) {
    if (strpos($e->getMessage(), '디렉터리') === false) {
        $failures[] = '존재하지 않는 디렉터리 예외 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = '존재하지 않는 디렉터리 테스트가 예상하지 않은 예외를 던졌다: ' . get_class($e);
}

try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $gate = new InstallerRouteGate($connection, null, new InstallerLock($lockPath));

    if (!$gate->isInstallationComplete()) {
        $failures[] = 'installer lock 파일이 있으면 DB 스키마 상태와 무관하게 설치 완료로 판단해야 한다.';
    }

    if ($gate->canAccessInstallerRoute()) {
        $failures[] = 'installer lock 파일이 있으면 installer 라우트 접근을 차단해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = 'InstallerRouteGate lock 연동 테스트 실패: ' . $e->getMessage();
}

if (is_file($lockPath) && !unlink($lockPath)) {
    $failures[] = "installer lock 테스트 파일을 삭제할 수 없다: {$lockPath}";
}
if (is_dir($tmpDir) && !rmdir($tmpDir)) {
    $failures[] = "installer lock 테스트 디렉터리를 삭제할 수 없다: {$tmpDir}";
}

if ($failures !== []) {
    fwrite(STDERR, "Installer InstallerLock 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer InstallerLock 테스트 통과.\n");
exit(0);
