<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\InstallCompletionHandler(`GET /install/complete` 처리, 태스크 0682)의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 검증 대상:
 * (1) 아직 lock이 없는 상태에서 handle()을 호출하면 완료 화면(200, InstallCompletionPage)을
 *     렌더링하고, InstallerLock에 완료 기록(lock 파일)을 남긴다.
 * (2) 이미 lock이 기록된 상태에서 다시 handle()을 호출해도 오류 없이 완료 화면을
 *     보여주고, 기존 완료 시각을 덮어쓰지 않는다(재실행 안전).
 * (3) 기본 생성자(인자 없음)는 docroot 밖 `config/install.lock`을 가리키는
 *     InstallerLock::atDefaultPath()를 사용한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\InstallCompletionHandler;
use MintWiki\Installer\InstallerLock;

$failures = [];
$tmpDir = sys_get_temp_dir() . '/mintwiki_install_completion_handler_' . getmypid();

if (!mkdir($tmpDir, 0777, true) && !is_dir($tmpDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$tmpDir}\n");
    exit(1);
}

$lockPath = $tmpDir . '/' . InstallerLock::DEFAULT_FILENAME;

try {
    $lock = new InstallerLock($lockPath);
    $handler = new InstallCompletionHandler($lock);

    if ($lock->isLocked()) {
        $failures[] = '테스트 시작 전에는 lock이 없어야 한다.';
    }

    // (1) 최초 호출 → 200, 완료 화면, lock 기록.
    $response1 = $handler->handle();

    if ($response1->status() !== 200) {
        $failures[] = 'handle()은 200을 반환해야 하는데 ' . $response1->status() . '이었다.';
    }
    if (!str_contains($response1->body(), '<h1>설치 완료</h1>')) {
        $failures[] = 'handle() 응답은 InstallCompletionPage의 완료 화면이어야 한다.';
    }
    if (!$lock->isLocked()) {
        $failures[] = 'handle() 호출 후 InstallerLock이 완료를 기록해야 한다.';
    }

    $firstPayload = json_decode((string) file_get_contents($lockPath), true);
    if (($firstPayload['status'] ?? null) !== 'complete') {
        $failures[] = 'lock 파일은 status=complete를 기록해야 한다.';
    }

    // (2) 재호출 → 여전히 200/완료 화면이지만 완료 시각을 덮어쓰지 않는다.
    $response2 = $handler->handle();

    if ($response2->status() !== 200) {
        $failures[] = '재호출도 200을 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
    if (!str_contains($response2->body(), '<h1>설치 완료</h1>')) {
        $failures[] = '재호출 응답도 완료 화면이어야 한다.';
    }

    $secondPayload = json_decode((string) file_get_contents($lockPath), true);
    if (($secondPayload['completed_at'] ?? null) !== ($firstPayload['completed_at'] ?? null)) {
        $failures[] = '이미 완료된 설치의 완료 시각이 재호출로 바뀌면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = 'InstallCompletionHandler 테스트 실패: ' . $e->getMessage();
}

// (3) 기본 생성자는 InstallerLock::atDefaultPath()(docroot 밖 config/install.lock)를 사용한다.
try {
    $defaultHandler = new InstallCompletionHandler();
    $reflection = new ReflectionProperty($defaultHandler, 'installerLock');
    $reflection->setAccessible(true);
    $defaultLock = $reflection->getValue($defaultHandler);

    $expectedPath = dirname(__DIR__, 2) . '/config/' . InstallerLock::DEFAULT_FILENAME;
    if ($defaultLock->path() !== $expectedPath) {
        $failures[] = 'InstallCompletionHandler 기본 생성자는 config/install.lock 경로를 사용해야 하는데 '
            . $defaultLock->path() . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '기본 lock 경로 테스트 실패: ' . $e->getMessage();
}

if (is_file($lockPath) && !unlink($lockPath)) {
    $failures[] = "테스트 lock 파일을 삭제할 수 없다: {$lockPath}";
}
if (is_dir($tmpDir) && !rmdir($tmpDir)) {
    $failures[] = "테스트 디렉터리를 삭제할 수 없다: {$tmpDir}";
}

if ($failures !== []) {
    fwrite(STDERR, "InstallCompletionHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallCompletionHandler 테스트 통과.\n");
exit(0);
