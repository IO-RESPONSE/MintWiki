<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\DatabaseSetupHandler(`POST /install/database` 처리, 태스크 0679)의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 검증 대상:
 * (1) 잘못된 CSRF 토큰은 403으로 거부되고, 폼으로 되돌아가며, 아무것도 기록하지 않는다.
 * (2) 유효한 CSRF 토큰이지만 접속 시험이 실패하면 폼으로 되돌아가 오류를 표시하고,
 *     아무것도 기록하지 않는다. 오류 응답에는 비밀번호 값이 노출되지 않는다.
 * (3) 유효한 CSRF 토큰 + 접속 성공 시 local-config.php가 기록되고, 응답에
 *     다음 단계(스키마 적용, `/install/schema`)로 가는 링크가 포함된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\DatabaseConfigWriter;
use MintWiki\Installer\DatabaseSetupHandler;
use MintWiki\Persistence\ConnectionConfig;
use MintWiki\Security\CsrfTokenService;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];
$tmpDir = sys_get_temp_dir() . '/mintwiki_db_setup_handler_' . getmypid();

if (!mkdir($tmpDir, 0777, true) && !is_dir($tmpDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$tmpDir}\n");
    exit(1);
}

$submittedFields = [
    'host' => 'db.example.com',
    'port' => '3306',
    'dbname' => 'wiki_engine',
    'username' => 'wiki_user',
    'password' => 'sup3r-secret',
];

try {
    // (1) 잘못된 CSRF 토큰은 403으로 거부되고, 아무것도 기록하지 않아야 한다.
    $_SESSION = [];
    $csrfService = new CsrfTokenService();
    $csrfService->generate(); // 세션에 유효한 토큰을 하나 심어 두되, 실제 제출에는 사용하지 않는다.

    $failingConnectionWriter = new DatabaseConfigWriter($tmpDir, function () {
        throw new RuntimeException('이 경로에서는 접속을 시도하면 안 된다.');
    });

    $handler = new DatabaseSetupHandler($csrfService, $failingConnectionWriter);
    $response = $handler->handle($submittedFields + ['csrf_token' => 'not-a-real-token']);

    if ($response->status() !== 403) {
        $failures[] = '잘못된 CSRF 토큰은 403을 반환해야 하는데 ' . $response->status() . '이었다.';
    }
    if (!str_contains($response->body(), '<h1>데이터베이스 설정</h1>')) {
        $failures[] = '잘못된 CSRF 토큰이면 DB 설정 폼으로 되돌아가야 한다.';
    }
    if (is_file($failingConnectionWriter->path())) {
        $failures[] = '잘못된 CSRF 토큰이면 local-config.php가 기록되어 있으면 안 된다.';
    }

    // (2) 유효한 CSRF 토큰 + 접속 실패 → 폼으로 되돌아가고, 아무것도 기록하지 않으며,
    //     응답 본문에 비밀번호 값이 노출되지 않아야 한다.
    $_SESSION = [];
    $csrfService2 = new CsrfTokenService();
    $validToken = $csrfService2->generate();

    $failingWriter = new DatabaseConfigWriter($tmpDir, function () {
        throw new RuntimeException('접속 거부됨(테스트용)');
    });

    $handler2 = new DatabaseSetupHandler($csrfService2, $failingWriter);
    $response2 = $handler2->handle($submittedFields + ['csrf_token' => $validToken]);

    if ($response2->status() !== 422) {
        $failures[] = '접속 실패는 422를 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
    if (str_contains($response2->body(), $submittedFields['password'])) {
        $failures[] = '접속 실패 응답 본문에 제출한 비밀번호 값이 노출되면 안 된다.';
    }
    if (is_file($failingWriter->path())) {
        $failures[] = '접속 시험이 실패했으면 local-config.php가 기록되어 있으면 안 된다.';
    }

    // (3) 유효한 CSRF 토큰 + 접속 성공 → local-config.php가 기록되고, 다음 단계 링크를 보여준다.
    $_SESSION = [];
    $csrfService3 = new CsrfTokenService();
    $validToken3 = $csrfService3->generate();

    $fakePdo = new PDO('sqlite::memory:');
    $succeedingWriter = new DatabaseConfigWriter($tmpDir, function () use ($fakePdo): PDO {
        return $fakePdo;
    });

    $handler3 = new DatabaseSetupHandler($csrfService3, $succeedingWriter);
    $response3 = $handler3->handle($submittedFields + ['csrf_token' => $validToken3]);

    if ($response3->status() !== 200) {
        $failures[] = '접속 성공은 200을 반환해야 하는데 ' . $response3->status() . '이었다.';
    }
    if (!str_contains($response3->body(), 'href="/install/schema"')) {
        $failures[] = '접속 성공 응답에 다음 단계(/install/schema)로 가는 링크가 있어야 한다.';
    }
    if (str_contains($response3->body(), $submittedFields['password'])) {
        $failures[] = '성공 응답 본문에 비밀번호 값이 노출되면 안 된다.';
    }

    if (!is_file($succeedingWriter->path())) {
        $failures[] = '접속 성공 후 local-config.php가 기록되어 있어야 한다.';
    } else {
        $config = @include $succeedingWriter->path();
        if (!is_array($config) || ($config['user'] ?? null) !== 'wiki_user') {
            $failures[] = '기록된 설정의 user가 제출한 username과 같아야 한다.';
        }
        if (!is_array($config) || ($config['password'] ?? null) !== 'sup3r-secret') {
            $failures[] = '기록된 설정의 password가 제출한 password와 같아야 한다.';
        }
    }

    // 같은 CSRF 토큰을 재사용하면 실패해야 한다(1회용).
    $reuseResponse = $handler3->handle($submittedFields + ['csrf_token' => $validToken3]);
    if ($reuseResponse->status() !== 403) {
        $failures[] = '이미 사용한 CSRF 토큰은 재사용할 수 없어야 한다.';
    }

    // 필수 필드가 비어 있으면 422로 거부되고 아무것도 기록하지 않아야 한다.
    $_SESSION = [];
    $csrfService4 = new CsrfTokenService();
    $validToken4 = $csrfService4->generate();
    $missingFieldWriter = new DatabaseConfigWriter($tmpDir, function () {
        throw new RuntimeException('검증 실패 흐름에서는 접속을 시도하면 안 된다.');
    });
    $handler4 = new DatabaseSetupHandler($csrfService4, $missingFieldWriter);
    @unlink($missingFieldWriter->path());
    $response4 = $handler4->handle(['csrf_token' => $validToken4, 'host' => '', 'port' => '', 'dbname' => '', 'username' => '', 'password' => '']);
    if ($response4->status() !== 422) {
        $failures[] = '필수 필드가 비어 있으면 422를 반환해야 하는데 ' . $response4->status() . '이었다.';
    }
    if (is_file($missingFieldWriter->path())) {
        $failures[] = '필수 필드 검증에 실패했으면 local-config.php가 기록되어 있으면 안 된다.';
    }
} finally {
    @unlink($tmpDir . '/local-config.php');
    @rmdir($tmpDir);
}

if ($failures !== []) {
    fwrite(STDERR, "DatabaseSetupHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DatabaseSetupHandler 테스트 통과.\n");
exit(0);
