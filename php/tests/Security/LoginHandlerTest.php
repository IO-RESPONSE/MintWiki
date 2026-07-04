<?php

declare(strict_types=1);

/**
 * `MintWiki\Security\LoginHandler`(`POST /login` 처리, 태스크 0686)의 동작을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다. 실제 DB 없이
 * `AppBootstrap`의 connector(sqlite in-memory)에 `db/schema/account.sql`을
 * 적용해 성공/실패 흐름을 검증한다.
 *
 * 검증 대상:
 * (1) 잘못된 CSRF 토큰은 403으로 거부되고, 세션에 로그인 상태가 남지 않는다.
 * (2) `AppBootstrap`이 PDO를 만들지 못하면(미설정) 503으로 거부된다.
 * (3) 존재하지 않는 username은 401로 거부되고(계정 존재 여부를 노출하지
 *     않는 고정 문구), 세션에 로그인 상태가 남지 않는다.
 * (4) 존재하는 username이지만 비밀번호가 틀리면 401로 거부된다.
 * (5) 올바른 자격 증명이면 302로 홈으로 리다이렉트하고, 세션에 계정 id가
 *     저장되며(`SessionUserResolver::SESSION_KEY`), 세션 ID가 재발급된다
 *     (session fixation 방지). 응답 본문에 평문 비밀번호가 노출되지 않는다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\AppBootstrap;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\LoginHandler;
use MintWiki\Security\SessionUserResolver;
use MintWiki\User\AccountRepository;

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
function mintwiki_login_handler_test_config_dir(): string
{
    global $createdConfigDirs;

    $dir = sys_get_temp_dir() . '/mintwiki_login_handler_' . getmypid() . '_' . bin2hex(random_bytes(4));
    mkdir($dir, 0777, true);
    file_put_contents(
        $dir . '/local-config.php',
        "<?php\nreturn ['driver' => 'mysql', 'dsn' => 'mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4', 'user' => 'wiki_user', 'password' => 'sup3r-secret'];\n"
    );
    $createdConfigDirs[] = $dir;

    return $dir;
}

function mintwiki_login_handler_test_pdo(string $accountSql): PDO
{
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);

    return $pdo;
}

$plainPassword = 'correct horse battery staple';

// (1) 잘못된 CSRF 토큰 → 403, 세션에 로그인 상태가 남지 않는다.
try {
    $_SESSION = [];
    $csrfService1 = new CsrfTokenService();
    $csrfService1->generate();

    $fakePdo1 = mintwiki_login_handler_test_pdo($accountSql);
    $accountId1 = (new AccountRepository($fakePdo1))->create('admin', password_hash($plainPassword, PASSWORD_DEFAULT));
    $bootstrap1 = new AppBootstrap(mintwiki_login_handler_test_config_dir(), static fn (): PDO => $fakePdo1);

    $handler1 = new LoginHandler($csrfService1, $bootstrap1);
    $response1 = $handler1->handle([
        'csrf_token' => 'not-a-real-token',
        'username' => 'admin',
        'password' => $plainPassword,
    ]);

    if ($response1->status() !== 403) {
        $failures[] = '잘못된 CSRF 토큰은 403을 반환해야 하는데 ' . $response1->status() . '이었다.';
    }
    if (!str_contains($response1->body(), '<h1>로그인</h1>')) {
        $failures[] = '잘못된 CSRF 토큰이면 로그인 폼으로 되돌아가야 한다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = 'CSRF 검증 실패 시 세션에 로그인 상태가 남으면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(1) CSRF 실패 테스트 중 예외: ' . $e->getMessage();
}

// (2) PDO를 만들지 못하면(미설정) 503을 반환해야 한다.
try {
    $_SESSION = [];
    $csrfService2 = new CsrfTokenService();
    $validToken2 = $csrfService2->generate();

    $unconfiguredBootstrap = new AppBootstrap(sys_get_temp_dir() . '/mintwiki_login_handler_missing_config_' . getmypid());

    $handler2 = new LoginHandler($csrfService2, $unconfiguredBootstrap);
    $response2 = $handler2->handle([
        'csrf_token' => $validToken2,
        'username' => 'admin',
        'password' => $plainPassword,
    ]);

    if ($response2->status() !== 503) {
        $failures[] = 'DB 미설정 상태는 503을 반환해야 하는데 ' . $response2->status() . '이었다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = 'DB 미설정 상태에서 세션에 로그인 상태가 남으면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(2) DB 미설정 테스트 중 예외: ' . $e->getMessage();
}

// (3) 존재하지 않는 username은 401로 거부되어야 한다.
try {
    $_SESSION = [];
    $csrfService3 = new CsrfTokenService();
    $validToken3 = $csrfService3->generate();

    $fakePdo3 = mintwiki_login_handler_test_pdo($accountSql);
    $bootstrap3 = new AppBootstrap(mintwiki_login_handler_test_config_dir(), static fn (): PDO => $fakePdo3);

    $handler3 = new LoginHandler($csrfService3, $bootstrap3);
    $response3 = $handler3->handle([
        'csrf_token' => $validToken3,
        'username' => 'no-such-user',
        'password' => $plainPassword,
    ]);

    if ($response3->status() !== 401) {
        $failures[] = '존재하지 않는 username은 401을 반환해야 하는데 ' . $response3->status() . '이었다.';
    }
    if (!str_contains($response3->body(), '아이디 또는 비밀번호가 올바르지 않습니다.')) {
        $failures[] = '존재하지 않는 username 오류는 계정 존재 여부를 드러내지 않는 고정 문구를 보여줘야 한다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = '로그인 실패 시 세션에 로그인 상태가 남으면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(3) 존재하지 않는 username 테스트 중 예외: ' . $e->getMessage();
}

// (4) 존재하는 username이지만 비밀번호가 틀리면 401을 반환해야 한다.
try {
    $_SESSION = [];
    $csrfService4 = new CsrfTokenService();
    $validToken4 = $csrfService4->generate();

    $fakePdo4 = mintwiki_login_handler_test_pdo($accountSql);
    (new AccountRepository($fakePdo4))->create('admin', password_hash($plainPassword, PASSWORD_DEFAULT));
    $bootstrap4 = new AppBootstrap(mintwiki_login_handler_test_config_dir(), static fn (): PDO => $fakePdo4);

    $handler4 = new LoginHandler($csrfService4, $bootstrap4);
    $response4 = $handler4->handle([
        'csrf_token' => $validToken4,
        'username' => 'admin',
        'password' => 'a-completely-wrong-password',
    ]);

    if ($response4->status() !== 401) {
        $failures[] = '틀린 비밀번호는 401을 반환해야 하는데 ' . $response4->status() . '이었다.';
    }
    if (str_contains($response4->body(), 'a-completely-wrong-password')) {
        $failures[] = '틀린 비밀번호 제출 시 응답 본문에 제출한 비밀번호가 노출되면 안 된다.';
    }
    if (isset($_SESSION[SessionUserResolver::SESSION_KEY])) {
        $failures[] = '비밀번호 불일치 시 세션에 로그인 상태가 남으면 안 된다.';
    }
} catch (Exception $e) {
    $failures[] = '(4) 틀린 비밀번호 테스트 중 예외: ' . $e->getMessage();
}

// (5) 올바른 자격 증명 → 302, 세션에 계정 id 저장, 세션 ID 재발급.
try {
    $_SESSION = [];
    $csrfService5 = new CsrfTokenService();
    $validToken5 = $csrfService5->generate();

    $fakePdo5 = mintwiki_login_handler_test_pdo($accountSql);
    $accountId5 = (new AccountRepository($fakePdo5))->create('admin', password_hash($plainPassword, PASSWORD_DEFAULT));
    $bootstrap5 = new AppBootstrap(mintwiki_login_handler_test_config_dir(), static fn (): PDO => $fakePdo5);

    $sessionIdBefore = session_id();
    $handler5 = new LoginHandler($csrfService5, $bootstrap5);
    $response5 = $handler5->handle([
        'csrf_token' => $validToken5,
        'username' => 'admin',
        'password' => $plainPassword,
    ]);
    $sessionIdAfter = session_id();

    if ($response5->status() !== 302) {
        $failures[] = '올바른 자격 증명은 302를 반환해야 하는데 ' . $response5->status() . '이었다.';
    }
    if (($response5->headers()['Location'] ?? null) !== '/') {
        $failures[] = '로그인 성공 시 Location은 "/"이어야 한다.';
    }
    if (str_contains($response5->body(), $plainPassword)) {
        $failures[] = '로그인 성공 응답 본문에 평문 비밀번호가 노출되면 안 된다.';
    }
    if (($_SESSION[SessionUserResolver::SESSION_KEY] ?? null) !== $accountId5) {
        $failures[] = '로그인 성공 시 세션에 계정 id가 저장되어야 한다.';
    }
    if ($sessionIdBefore === $sessionIdAfter) {
        $failures[] = '로그인 성공 시 세션 ID가 재발급되어야 한다(session fixation 방지).';
    }
} catch (Exception $e) {
    $failures[] = '(5) 정상 로그인 테스트 중 예외: ' . $e->getMessage();
}

foreach ($createdConfigDirs as $dir) {
    @unlink($dir . '/local-config.php');
    @rmdir($dir);
}

if ($failures !== []) {
    fwrite(STDERR, "LoginHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "LoginHandler 테스트 통과.\n");
exit(0);
