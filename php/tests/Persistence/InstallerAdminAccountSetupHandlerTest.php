<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\AdminAccountSetupHandler(`POST /install/admin` 처리, 태스크 0681)의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다. 실제 DB 없이
 * `AppBootstrap`의 connector(sqlite in-memory)에 `db/schema/account.sql`을 적용해
 * 성공/실패 흐름을 검증한다.
 *
 * 검증 대상:
 * (1) 잘못된 CSRF 토큰은 403으로 거부되고, 폼으로 되돌아간다(계정 생성 시도 없음).
 * (2) `AppBootstrap`이 PDO를 만들지 못하면(미설정) 422로 거부되고 계정이 생성되지 않는다.
 * (3) 필수 입력값이 비어있으면 422로 거부되고 폼에 오류가 표시된다(계정 생성 없음).
 * (4) 비밀번호와 비밀번호 확인이 다르면 422로 거부된다(계정 생성 없음).
 * (5) 이미 존재하는 username이면 422로 거부된다(중복 계정 생성 없음).
 * (6) 모든 검증을 통과하면 200으로 성공 화면을 보여주고, `account` 테이블에 해시된
 *     비밀번호로 행이 생성되며, 응답 본문에 평문 비밀번호가 노출되지 않는다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\AppBootstrap;
use MintWiki\Installer\AdminAccountSetupHandler;
use MintWiki\Security\CsrfTokenService;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
if ($accountSql === false) {
    fwrite(STDERR, "db/schema/account.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$createdConfigDirs = [];

/**
 * 접속 정보가 있는 것처럼 보이는 `local-config.php`를 담은 임시 설정 디렉터리를 만든다.
 * 실제 접속은 열지 않는다 — `AppBootstrap`에 주입하는 connector가 항상 가짜 PDO를 반환한다.
 */
function mintwiki_admin_account_handler_test_config_dir(): string
{
    global $createdConfigDirs;

    $dir = sys_get_temp_dir() . '/mintwiki_admin_account_handler_' . getmypid() . '_' . bin2hex(random_bytes(4));
    mkdir($dir, 0777, true);
    file_put_contents(
        $dir . '/local-config.php',
        "<?php\nreturn ['driver' => 'mysql', 'dsn' => 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4', 'user' => 'wiki_user', 'password' => 'sup3r-secret'];\n"
    );
    $createdConfigDirs[] = $dir;

    return $dir;
}

function mintwiki_admin_account_handler_test_pdo(string $accountSql): PDO
{
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);

    return $pdo;
}

$validFormData = [
    'username' => 'admin',
    'email' => 'admin@example.com',
    'password' => 'correct horse battery staple',
    'password_confirm' => 'correct horse battery staple',
];

// (1) 잘못된 CSRF 토큰 → 403, 폼으로 되돌아간다.
try {
    $_SESSION = [];
    $csrfService = new CsrfTokenService();
    $csrfService->generate();

    $fakePdo1 = mintwiki_admin_account_handler_test_pdo($accountSql);
    $bootstrap1 = new AppBootstrap(mintwiki_admin_account_handler_test_config_dir(), static fn (): PDO => $fakePdo1);

    $handler1 = new AdminAccountSetupHandler($csrfService, $bootstrap1);
    $response1 = $handler1->handle(['csrf_token' => 'not-a-real-token'] + $validFormData);

    if ($response1->status() !== 403) {
        $failures[] = '잘못된 CSRF 토큰은 403을 반환해야 하는데 ' . $response1->status() . '이었다.';
    }
    if (!str_contains($response1->body(), '<h1>관리자 계정 생성</h1>')) {
        $failures[] = '잘못된 CSRF 토큰이면 관리자 계정 생성 폼으로 되돌아가야 한다.';
    }

    $count1 = (int) $fakePdo1->query('SELECT COUNT(*) FROM account')->fetchColumn();
    if ($count1 !== 0) {
        $failures[] = 'CSRF 검증 실패 시 계정이 생성되면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(1) CSRF 실패 테스트 중 예외: ' . $e->getMessage();
}

// (2) PDO를 만들지 못하면(미설정) 422를 반환해야 한다.
try {
    $_SESSION = [];
    $csrfService2 = new CsrfTokenService();
    $validToken2 = $csrfService2->generate();

    $unconfiguredBootstrap = new AppBootstrap(sys_get_temp_dir() . '/mintwiki_admin_account_handler_missing_config_' . getmypid());

    $handler2 = new AdminAccountSetupHandler($csrfService2, $unconfiguredBootstrap);
    $response2 = $handler2->handle(['csrf_token' => $validToken2] + $validFormData);

    if ($response2->status() !== 422) {
        $failures[] = 'DB 미설정 상태는 422를 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
} catch (Exception $e) {
    $failures[] = '(2) DB 미설정 테스트 중 예외: ' . $e->getMessage();
}

// (3) 필수 입력값이 비어있으면 422, 계정이 생성되지 않아야 한다.
try {
    $_SESSION = [];
    $csrfService3 = new CsrfTokenService();
    $validToken3 = $csrfService3->generate();

    $fakePdo3 = mintwiki_admin_account_handler_test_pdo($accountSql);
    $bootstrap3 = new AppBootstrap(mintwiki_admin_account_handler_test_config_dir(), static fn (): PDO => $fakePdo3);

    $handler3 = new AdminAccountSetupHandler($csrfService3, $bootstrap3);
    $response3 = $handler3->handle([
        'csrf_token' => $validToken3,
        'username' => '',
        'email' => '',
        'password' => '',
        'password_confirm' => '',
    ]);

    if ($response3->status() !== 422) {
        $failures[] = '빈 입력값 제출은 422를 반환해야 하는데 ' . $response3->status() . '이었다.';
    }
    if (!str_contains($response3->body(), '오류가 발생했습니다')) {
        $failures[] = '빈 입력값 제출 응답에 오류 요약이 표시되어야 한다.';
    }

    $count3 = (int) $fakePdo3->query('SELECT COUNT(*) FROM account')->fetchColumn();
    if ($count3 !== 0) {
        $failures[] = '입력 검증 실패 시 계정이 생성되면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(3) 빈 입력값 테스트 중 예외: ' . $e->getMessage();
}

// (4) 비밀번호 확인이 일치하지 않으면 422를 반환해야 한다.
try {
    $_SESSION = [];
    $csrfService4 = new CsrfTokenService();
    $validToken4 = $csrfService4->generate();

    $fakePdo4 = mintwiki_admin_account_handler_test_pdo($accountSql);
    $bootstrap4 = new AppBootstrap(mintwiki_admin_account_handler_test_config_dir(), static fn (): PDO => $fakePdo4);

    $handler4 = new AdminAccountSetupHandler($csrfService4, $bootstrap4);
    $response4 = $handler4->handle([
        'csrf_token' => $validToken4,
        'username' => 'admin',
        'email' => 'admin@example.com',
        'password' => 'correct horse battery staple',
        'password_confirm' => 'a-different-password',
    ]);

    if ($response4->status() !== 422) {
        $failures[] = '비밀번호 확인 불일치는 422를 반환해야 하는데 ' . $response4->status() . '이었다.';
    }

    $count4 = (int) $fakePdo4->query('SELECT COUNT(*) FROM account')->fetchColumn();
    if ($count4 !== 0) {
        $failures[] = '비밀번호 확인 불일치 시 계정이 생성되면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(4) 비밀번호 확인 불일치 테스트 중 예외: ' . $e->getMessage();
}

// (5) 이미 존재하는 username이면 422를 반환해야 한다(중복 계정 생성 없음).
try {
    $_SESSION = [];
    $csrfService5 = new CsrfTokenService();
    $validToken5 = $csrfService5->generate();

    $fakePdo5 = mintwiki_admin_account_handler_test_pdo($accountSql);
    $fakePdo5->exec(
        "INSERT INTO account (id, username, display_name, password_hash) "
        . "VALUES ('existing-id', 'admin', NULL, 'existing-hash')"
    );
    $bootstrap5 = new AppBootstrap(mintwiki_admin_account_handler_test_config_dir(), static fn (): PDO => $fakePdo5);

    $handler5 = new AdminAccountSetupHandler($csrfService5, $bootstrap5);
    $response5 = $handler5->handle(['csrf_token' => $validToken5] + $validFormData);

    if ($response5->status() !== 422) {
        $failures[] = '중복 username 제출은 422를 반환해야 하는데 ' . $response5->status() . '이었다.';
    }

    $count5 = (int) $fakePdo5->query('SELECT COUNT(*) FROM account')->fetchColumn();
    if ($count5 !== 1) {
        $failures[] = '중복 username 제출 시 계정이 추가로 생성되면 안 된다(기존 1건만 남아야 한다).';
    }
} catch (Exception $e) {
    $failures[] = '(5) 중복 username 테스트 중 예외: ' . $e->getMessage();
}

// (6) 모든 검증 통과 → 200, 계정 생성, 해시 저장, 평문 비밀번호 미노출.
try {
    $_SESSION = [];
    $csrfService6 = new CsrfTokenService();
    $validToken6 = $csrfService6->generate();

    $fakePdo6 = mintwiki_admin_account_handler_test_pdo($accountSql);
    $bootstrap6 = new AppBootstrap(mintwiki_admin_account_handler_test_config_dir(), static fn (): PDO => $fakePdo6);

    $handler6 = new AdminAccountSetupHandler($csrfService6, $bootstrap6);
    $response6 = $handler6->handle(['csrf_token' => $validToken6] + $validFormData);

    if ($response6->status() !== 200) {
        $failures[] = '정상 제출은 200을 반환해야 하는데 ' . $response6->status() . '이었다.';
    }
    if (str_contains($response6->body(), 'correct horse battery staple')) {
        $failures[] = '성공 응답 본문에 평문 비밀번호가 노출되면 안 된다.';
    }

    $row6 = $fakePdo6->query('SELECT username, password_hash FROM account WHERE username = ' . $fakePdo6->quote('admin'))
        ->fetch(PDO::FETCH_ASSOC);
    if ($row6 === false) {
        $failures[] = '정상 제출 후 account 테이블에 행이 생성되어야 한다.';
    } else {
        if ($row6['password_hash'] === 'correct horse battery staple') {
            $failures[] = '저장된 password_hash가 평문 비밀번호와 같으면 안 된다(해시되어야 한다).';
        }
        if (!password_verify('correct horse battery staple', (string) $row6['password_hash'])) {
            $failures[] = '저장된 password_hash는 원래 비밀번호로 검증되어야 한다.';
        }
    }

    // 같은 CSRF 토큰을 재사용하면 실패해야 한다(1회용).
    $reuseResponse = $handler6->handle(['csrf_token' => $validToken6] + $validFormData);
    if ($reuseResponse->status() !== 403) {
        $failures[] = '이미 사용한 CSRF 토큰은 재사용할 수 없어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(6) 정상 제출 테스트 중 예외: ' . $e->getMessage();
}

foreach ($createdConfigDirs as $dir) {
    @unlink($dir . '/local-config.php');
    @rmdir($dir);
}

if ($failures !== []) {
    fwrite(STDERR, "AdminAccountSetupHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AdminAccountSetupHandler 테스트 통과.\n");
exit(0);
