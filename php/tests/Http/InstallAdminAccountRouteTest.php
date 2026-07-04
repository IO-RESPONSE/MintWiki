<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0681에서 등록하는 `GET`/`POST /install/admin` route
 * 핸들러의 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0680 InstallSchemaApplyRouteTest.php와 동일한 방식) — index.php는 재사용 가능한
 * 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 잘못된 CSRF 토큰으로 `POST /install/admin`을 제출하면 403을 반환하고,
 *     관리자 계정 생성 폼으로 되돌아가는지.
 * (2) 등록되지 않은 method(예: PUT)는 여전히 매칭되지 않는지.
 * (3) 설치가 이미 완료된 상태에서는 `InstallerRouteGate`가 `GET`/`POST
 *     /install/admin` 둘 다 403으로 차단하는지 — 0680 (3)과 동일한 방식.
 * (4) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 `GET /install/admin`이
 *     200을 반환하고(폼 화면, CSRF 토큰 포함), 잘못된 CSRF 토큰의 `POST /install/admin`은
 *     403을 반환하는지(0677/0678/0679/0680의 (4)와 동일한 라이브 wiring 확인 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\AdminAccountSetupHandler;
use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\InstallAdminAccountFormPage;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

try {
    // (1) 잘못된 CSRF 토큰 → 403, 폼으로 되돌아간다.
    $_SESSION = [];

    $router = new Router();
    $router->register('GET', '/install/admin', static function (): Response {
        $installAdminAccountFormPage = new InstallAdminAccountFormPage();

        return Response::html($installAdminAccountFormPage->render());
    });
    $router->register('POST', '/install/admin', static function (): Response {
        $handler = new AdminAccountSetupHandler(new CsrfTokenService());

        return $handler->handle(['csrf_token' => 'not-a-real-token']);
    });

    $postHandler = $router->match(new Request('POST', '/install/admin'));
    if ($postHandler === null) {
        $failures[] = 'POST /install/admin route는 등록되어 있어야 한다.';
    } else {
        $response = $postHandler();
        if ($response->status() !== 403) {
            $failures[] = '잘못된 CSRF 토큰 제출은 403을 반환해야 하는데 ' . $response->status() . '이었다.';
        }
        if (!str_contains($response->body(), '<h1>관리자 계정 생성</h1>')) {
            $failures[] = '잘못된 CSRF 토큰 제출은 관리자 계정 생성 폼으로 되돌아가야 한다.';
        }
    }

    $getHandler = $router->match(new Request('GET', '/install/admin'));
    if ($getHandler === null) {
        $failures[] = 'GET /install/admin route는 등록되어 있어야 한다.';
    } else {
        $getResponse = $getHandler();
        if ($getResponse->status() !== 200) {
            $failures[] = 'GET /install/admin은 200을 반환해야 하는데 ' . $getResponse->status() . '이었다.';
        }
        if (!str_contains($getResponse->body(), 'name="csrf_token"')) {
            $failures[] = 'GET /install/admin 응답은 CSRF 토큰 필드를 포함해야 한다.';
        }
    }

    // (2) 등록되지 않은 method는 매칭되지 않아야 한다.
    if ($router->match(new Request('PUT', '/install/admin')) !== null) {
        $failures[] = 'PUT /install/admin은 등록되어 있지 않아야 한다.';
    }

    // (3) 설치완료 상태에서는 InstallerRouteGate가 GET/POST /install/admin를 403으로 차단해야 한다.
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");

    $gate = new InstallerRouteGate($connection);

    $blockedGetResponse = $gate->resolveFrontControllerResponse('/install/admin', false);
    if ($blockedGetResponse === null || $blockedGetResponse->status() !== 403) {
        $failures[] = '설치완료 상태에서 GET /install/admin은 InstallerRouteGate로 403 차단되어야 한다.';
    }

    $blockedPostResponse = $gate->resolveFrontControllerResponse('/install/admin', false);
    if ($blockedPostResponse === null || $blockedPostResponse->status() !== 403) {
        $failures[] = '설치완료 상태에서 POST /install/admin은 InstallerRouteGate로 403 차단되어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(3) in-process 테스트 실패: ' . $e->getMessage();
}

// (4) DB 미설정 상태로 실제 index.php를 띄워도 라우팅이 동일하게 동작해야 한다.
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_install_admin_account_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_install_admin_account_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_install_admin_account_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

/**
 * @return array{0: int, 1: string}
 */
function mintwiki_install_admin_account_route_http_post(int $port, string $path, array $fields): array
{
    $body = http_build_query($fields);
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => $body,
            'ignore_errors' => true,
            'timeout' => 5,
        ],
    ]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

try {
    foreach (DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';
    $configDir = __DIR__ . '/../../config';
    $realLocalConfigPath = $configDir . '/local-config.php';
    $localConfigExistedBefore = is_file($realLocalConfigPath);

    $port = mintwiki_install_admin_account_route_free_port();
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
        mintwiki_install_admin_account_route_wait_for_server($port);

        [$getStatus, $getBody] = mintwiki_install_admin_account_route_http_get($port, '/install/admin');
        if ($getStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /install/admin은 200을 반환해야 하는데 ' . $getStatus . '이었다.';
        }
        if (!str_contains($getBody, 'name="csrf_token"')) {
            $failures[] = 'DB 미설정 상태에서 GET /install/admin 응답은 CSRF 토큰 필드를 포함해야 한다.';
        }

        [$postStatus] = mintwiki_install_admin_account_route_http_post($port, '/install/admin', [
            'csrf_token' => 'not-a-real-token',
        ]);
        if ($postStatus !== 403) {
            $failures[] = 'DB 미설정 상태에서 잘못된 CSRF 토큰의 POST /install/admin은 403을 반환해야 하는데 ' . $postStatus . '이었다.';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DB_ENV_KEYS as $key) {
            putenv($key);
        }
        if (!$localConfigExistedBefore) {
            @unlink($realLocalConfigPath);
        }
    }
} catch (Exception $e) {
    $failures[] = '(4) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /install/admin route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /install/admin route 테스트 통과.\n");
exit(0);
