<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0678에서 등록하는 `GET /install/database` route
 * 핸들러의 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0677 InstallWelcomeAndRequirementsRoutesTest.php와 동일한 방식) — index.php는
 * 재사용 가능한 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해
 * 검증한다.
 *
 * 검증 대상:
 * (1) GET /install/database가 `InstallDBFormPage`를 200으로 렌더하는지.
 * (2) 응답에 host/port/dbname/username/password 입력 필드가 모두 포함되는지.
 * (3) 응답에 `CsrfTokenService`가 심은 CSRF 토큰 hidden 필드가 포함되는지.
 * (4) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 route가 200으로
 *     응답하는지(InstallWelcomeAndRequirementsRoutesTest.php (4)와 동일한 방식).
 * (5) 설치가 이미 완료된 상태에서는 `InstallerRouteGate`가 이 route를 403으로
 *     차단하는지 — 0676 InstallerRouteGateWiringTest.php가 `/install/step-1`
 *     sub-path로 이미 검증한 접두사 규칙을 `/install/database`에도 그대로
 *     적용해 재확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Ui\InstallDBFormPage;

$failures = [];

$router = new Router();

$router->register('GET', '/install/database', static function (): Response {
    $installDBFormPage = new InstallDBFormPage();

    return Response::html($installDBFormPage->render());
});

// (1)/(2)/(3) GET /install/database가 200으로 InstallDBFormPage를 렌더하고,
// host/port/dbname/username/password 필드와 CSRF 토큰을 포함해야 한다.
$installDatabaseHandler = $router->match(new Request('GET', '/install/database'));
if ($installDatabaseHandler === null) {
    $failures[] = 'GET /install/database route는 등록되어 있어야 한다.';
} else {
    $response = $installDatabaseHandler();
    if ($response->status() !== 200) {
        $failures[] = 'GET /install/database 응답의 status는 200이어야 한다.';
    }

    $body = $response->body();
    if (!str_contains($body, '<h1>데이터베이스 설정</h1>')) {
        $failures[] = 'GET /install/database 응답이 DB form page의 h1을 포함해야 한다.';
    }
    if (!str_contains($body, '<form method="post" action="/install/database">')) {
        $failures[] = 'GET /install/database 응답이 POST /install/database로 제출하는 form을 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" id="host" name="host"')) {
        $failures[] = 'GET /install/database 응답이 host 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" id="port" name="port"')) {
        $failures[] = 'GET /install/database 응답이 port 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" id="dbname" name="dbname"')) {
        $failures[] = 'GET /install/database 응답이 dbname 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" id="username" name="username"')) {
        $failures[] = 'GET /install/database 응답이 username 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="password" id="password" name="password"')) {
        $failures[] = 'GET /install/database 응답이 password 입력 필드를 포함해야 한다.';
    }
    if (!preg_match('/<input type="hidden" name="csrf_token" value="[0-9a-f]+">/', $body)) {
        $failures[] = 'GET /install/database 응답이 CSRF 토큰 hidden 필드를 포함해야 한다.';
    }
}

// 등록되지 않은 method는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('POST', '/install/database')) !== null) {
    $failures[] = 'POST /install/database는 이 태스크(0678)의 범위 밖이므로 아직 등록되어 있지 않아야 한다.';
}

// (5) 설치완료 상태에서는 InstallerRouteGate가 /install/database를 403으로
// 차단해야 한다 — 0676 InstallerRouteGateWiringTest.php와 동일한 방식.
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
    $blockedResponse = $gate->resolveFrontControllerResponse('/install/database', false);

    if ($blockedResponse === null || $blockedResponse->status() !== 403) {
        $failures[] = '설치완료 상태에서 GET /install/database는 InstallerRouteGate로 403 차단되어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(5) 설치완료 → /install/database 차단 테스트 실패: ' . $e->getMessage();
}

// (4) DB 미설정 상태로 실제 index.php를 띄워도 route가 200으로 응답해야 한다
// (InstallWelcomeAndRequirementsRoutesTest.php (4)와 동일한 방식).
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_install_database_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_install_database_route_wait_for_server(int $port, float $timeout = 5.0): void
{
    $deadline = microtime(true) + $timeout;
    while (microtime(true) < $deadline) {
        $connection = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
        if ($connection !== false) {
            fclose($connection);

            return;
        }
        usleep(50000);
    }

    throw new RuntimeException("php -S 서버(포트 {$port})가 제한 시간 안에 준비되지 않았습니다.");
}

/**
 * @return array{0: int, 1: string}
 */
function mintwiki_install_database_route_http_get(int $port, string $path): array
{
    $context = stream_context_create([
        'http' => ['method' => 'GET', 'ignore_errors' => true, 'timeout' => 5],
    ]);
    $body = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $body === false ? '' : $body];
}

try {
    foreach (DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';
    $port = mintwiki_install_database_route_free_port();
    $process = proc_open(
        ['php', '-S', "127.0.0.1:{$port}", '-t', $publicDir],
        [1 => ['pipe', 'w'], 2 => ['pipe', 'w']],
        $pipes,
        $publicDir
    );

    if ($process === false) {
        throw new RuntimeException('php -S 서버를 시작하지 못했습니다.');
    }

    try {
        mintwiki_install_database_route_wait_for_server($port);

        [$status, $body] = mintwiki_install_database_route_http_get($port, '/install/database');
        if ($status !== 200) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install/database는 200을 반환해야 한다.';
        }
        if (!str_contains($body, '<h1>데이터베이스 설정</h1>')) {
            $failures[] = 'DB 미설정 상태에서 실제 index.php의 GET /install/database 응답이 DB form 화면이어야 한다.';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(4) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /install/database route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /install/database route 테스트 통과.\n");
exit(0);
