<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\SchemaApplyHandler(`POST /install/schema` 처리, 태스크 0680)의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다. 실제 DB 없이
 * `AppBootstrap`의 connector(sqlite in-memory)와 fixture 스키마 디렉터리를 가리키는
 * `SchemaApply`를 주입해 성공/실패 흐름을 검증한다.
 *
 * 검증 대상:
 * (1) 잘못된 CSRF 토큰은 403으로 거부되고, 진행 화면으로 되돌아간다(적용 시도 없음).
 * (2) `AppBootstrap`이 PDO를 만들지 못하면(미설정) 422로 거부된다.
 * (3) PDO는 얻었지만 스키마 파일 중 하나의 SQL 실행이 실패하면 500으로 오류 화면을
 *     보여주고 다음 단계 링크를 포함하지 않는다.
 * (4) CSRF 검증과 PDO 확보, 스키마 적용이 모두 성공하면 200으로 다음 단계
 *     (`/install/admin-account`) 링크를 보여주고 `schema_version`이 채워진다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\AppBootstrap;
use MintWiki\Installer\SchemaApply;
use MintWiki\Installer\SchemaApplyHandler;
use MintWiki\Security\CsrfTokenService;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];
$realSchemaDir = dirname(__DIR__, 3) . '/db/schema';

/**
 * 접속 정보가 있는 것처럼 보이는 `local-config.php`를 담은 임시 설정 디렉터리를 만든다.
 * 실제 접속은 열지 않는다 — `AppBootstrap`에 주입하는 connector가 항상 가짜 PDO를 반환한다.
 */
function mintwiki_schema_apply_handler_test_config_dir(): string
{
    $dir = sys_get_temp_dir() . '/mintwiki_schema_apply_handler_' . getmypid() . '_' . bin2hex(random_bytes(4));
    mkdir($dir, 0777, true);
    file_put_contents(
        $dir . '/local-config.php',
        "<?php\nreturn ['driver' => 'mysql', 'dsn' => 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4', 'user' => 'wiki_user', 'password' => 'sup3r-secret'];\n"
    );

    return $dir;
}

/**
 * 스키마 파일 하나가 실패하도록 조작한 fixture 디렉터리를 만든다
 * (schema_migration.sql/schema_version.sql은 실제 파일 그대로, account.sql은 깨진 SQL).
 */
function mintwiki_schema_apply_handler_test_failing_schema_dir(string $realSchemaDir): string
{
    $dir = sys_get_temp_dir() . '/mintwiki_schema_apply_handler_bad_schema_' . getmypid() . '_' . bin2hex(random_bytes(4));
    mkdir($dir, 0777, true);
    copy($realSchemaDir . '/schema_migration.sql', $dir . '/schema_migration.sql');
    copy($realSchemaDir . '/schema_version.sql', $dir . '/schema_version.sql');
    file_put_contents($dir . '/account.sql', 'THIS IS NOT VALID SQL;');

    return $dir;
}

// (1) 잘못된 CSRF 토큰 → 403, 진행 화면으로 되돌아간다.
try {
    $_SESSION = [];
    $csrfService = new CsrfTokenService();
    $csrfService->generate();

    $handler = new SchemaApplyHandler($csrfService, new SchemaApply($realSchemaDir), new AppBootstrap());
    $response = $handler->handle(['csrf_token' => 'not-a-real-token']);

    if ($response->status() !== 403) {
        $failures[] = '잘못된 CSRF 토큰은 403을 반환해야 하는데 ' . $response->status() . '이었다.';
    }
    if (!str_contains($response->body(), '<h1>데이터베이스 스키마 적용</h1>')) {
        $failures[] = '잘못된 CSRF 토큰이면 스키마 적용 진행 화면으로 되돌아가야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1) CSRF 실패 테스트 중 예외: ' . $e->getMessage();
}

// (2) PDO를 만들지 못하면(미설정) 422을 반환해야 한다.
try {
    $_SESSION = [];
    $csrfService2 = new CsrfTokenService();
    $validToken2 = $csrfService2->generate();

    $unconfiguredBootstrap = new AppBootstrap(sys_get_temp_dir() . '/mintwiki_schema_apply_handler_missing_config_' . getmypid());

    $handler2 = new SchemaApplyHandler($csrfService2, new SchemaApply($realSchemaDir), $unconfiguredBootstrap);
    $response2 = $handler2->handle(['csrf_token' => $validToken2]);

    if ($response2->status() !== 422) {
        $failures[] = 'DB 미설정 상태는 422를 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(2) DB 미설정 테스트 중 예외: ' . $e->getMessage();
}

// (3) PDO는 얻었지만 스키마 적용이 실패하면 500, 다음 단계 링크가 없어야 한다.
$configDir3 = mintwiki_schema_apply_handler_test_config_dir();
$failingSchemaDir = mintwiki_schema_apply_handler_test_failing_schema_dir($realSchemaDir);
try {
    $_SESSION = [];
    $csrfService3 = new CsrfTokenService();
    $validToken3 = $csrfService3->generate();

    $fakePdo3 = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $bootstrap3 = new AppBootstrap($configDir3, static fn (): PDO => $fakePdo3);

    $handler3 = new SchemaApplyHandler($csrfService3, new SchemaApply($failingSchemaDir), $bootstrap3);
    $response3 = $handler3->handle(['csrf_token' => $validToken3]);

    if ($response3->status() !== 500) {
        $failures[] = 'SchemaApply 적용 실패는 500을 반환해야 하는데 ' . $response3->status() . '이었다.';
    }
    if (!str_contains($response3->body(), '스키마 적용에 실패했습니다')) {
        $failures[] = '적용 실패 응답에 오류 메시지가 표시되어야 한다.';
    }
    if (str_contains($response3->body(), 'href="/install/admin-account"')) {
        $failures[] = '적용 실패 응답에 다음 단계 링크가 있으면 안 된다.';
    }

    $versionCountAfterFailure = (int) $fakePdo3->query('SELECT COUNT(*) FROM schema_version')->fetchColumn();
    if ($versionCountAfterFailure !== 0) {
        $failures[] = '적용이 실패했으면 schema_version에 행이 기록되면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(3) 적용 실패 테스트 중 예외: ' . $e->getMessage();
} finally {
    @unlink($configDir3 . '/local-config.php');
    @rmdir($configDir3);
    @unlink($failingSchemaDir . '/schema_migration.sql');
    @unlink($failingSchemaDir . '/schema_version.sql');
    @unlink($failingSchemaDir . '/account.sql');
    @rmdir($failingSchemaDir);
}

// (4) CSRF 검증 + PDO 확보 + 스키마 적용 모두 성공 → 200, 다음 단계 링크 + schema_version 기록.
$configDir4 = mintwiki_schema_apply_handler_test_config_dir();
try {
    $_SESSION = [];
    $csrfService4 = new CsrfTokenService();
    $validToken4 = $csrfService4->generate();

    $fakePdo4 = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $fakePdo4->exec('PRAGMA foreign_keys = ON');
    $bootstrap4 = new AppBootstrap($configDir4, static fn (): PDO => $fakePdo4);

    $handler4 = new SchemaApplyHandler($csrfService4, new SchemaApply($realSchemaDir), $bootstrap4, null, null, 'v0.1.0-test');
    $response4 = $handler4->handle(['csrf_token' => $validToken4]);

    if ($response4->status() !== 200) {
        $failures[] = '적용 성공은 200을 반환해야 하는데 ' . $response4->status() . '이었다.';
    }
    if (!str_contains($response4->body(), 'href="/install/admin-account"')) {
        $failures[] = '적용 성공 응답에 다음 단계(/install/admin-account)로 가는 링크가 있어야 한다.';
    }

    $versionRow = $fakePdo4->query('SELECT version FROM schema_version')->fetch(PDO::FETCH_ASSOC);
    if (($versionRow['version'] ?? null) !== 'v0.1.0-test') {
        $failures[] = '적용 성공 후 schema_version에 지정한 버전 문자열이 기록되어 있어야 한다.';
    }

    // 같은 CSRF 토큰을 재사용하면 실패해야 한다(1회용).
    $reuseResponse = $handler4->handle(['csrf_token' => $validToken4]);
    if ($reuseResponse->status() !== 403) {
        $failures[] = '이미 사용한 CSRF 토큰은 재사용할 수 없어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(4) 적용 성공 테스트 중 예외: ' . $e->getMessage();
} finally {
    @unlink($configDir4 . '/local-config.php');
    @rmdir($configDir4);
}

if ($failures !== []) {
    fwrite(STDERR, "SchemaApplyHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "SchemaApplyHandler 테스트 통과.\n");
exit(0);
