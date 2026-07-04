<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0682에서 등록하는 `GET /install/complete` route
 * 핸들러와, 설치 완료 후 `InstallerRouteGate`가 모든 `/install*` 접근을 차단하는
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다(0680/0681의
 * *RouteTest.php와 동일한 방식) — index.php는 재사용 가능한 모듈이 아니므로,
 * 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) `GET /install/complete`는 200과 함께 `InstallCompletionPage`를 렌더링하고,
 *     `InstallerLock`으로 완료를 기록한다.
 * (2) 등록되지 않은 method(예: POST)는 매칭되지 않는다.
 * (3) lock 파일만 있고 `schema_version`은 없는 상태에서도 `InstallerRouteGate`는
 *     `/install/complete`를 포함한 모든 `/install*` 접근을 403으로 차단한다
 *     (lock과 schema_version 중 하나만 있어도 재설치를 막는다는 계약).
 * (4) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 `GET /install/complete`가
 *     200을 반환하고(완료 화면), 실제 `config/install.lock`을 기록하는지(0677 이후의
 *     라이브 wiring 확인 방식과 동일).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\InstallCompletionHandler;
use MintWiki\Installer\InstallerLock;
use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;

$failures = [];
$tmpDir = sys_get_temp_dir() . '/mintwiki_install_complete_route_' . getmypid();

if (!mkdir($tmpDir, 0777, true) && !is_dir($tmpDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$tmpDir}\n");
    exit(1);
}

$lockPath = $tmpDir . '/' . InstallerLock::DEFAULT_FILENAME;

try {
    // (1)/(2) route 등록과 완료 화면/lock 기록 확인.
    $lock = new InstallerLock($lockPath);

    $router = new Router();
    $router->register('GET', '/install/complete', static function () use ($lock): Response {
        $handler = new InstallCompletionHandler($lock);

        return $handler->handle();
    });

    $getHandler = $router->match(new Request('GET', '/install/complete'));
    if ($getHandler === null) {
        $failures[] = 'GET /install/complete route는 등록되어 있어야 한다.';
    } else {
        $getResponse = $getHandler();
        if ($getResponse->status() !== 200) {
            $failures[] = 'GET /install/complete는 200을 반환해야 하는데 ' . $getResponse->status() . '이었다.';
        }
        if (!str_contains($getResponse->body(), '<h1>설치 완료</h1>')) {
            $failures[] = 'GET /install/complete 응답은 InstallCompletionPage 화면이어야 한다.';
        }
        if (!$lock->isLocked()) {
            $failures[] = 'GET /install/complete 호출 후 InstallerLock이 완료를 기록해야 한다.';
        }
    }

    if ($router->match(new Request('POST', '/install/complete')) !== null) {
        $failures[] = 'POST /install/complete는 등록되어 있지 않아야 한다.';
    }

    // (3) lock만 있고 schema_version은 없는 상태에서도 모든 /install* 접근이 차단되어야 한다.
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $gate = new InstallerRouteGate($connection, null, $lock);

    foreach (['/install', '/install/database', '/install/schema', '/install/admin', '/install/complete'] as $installPath) {
        $blockedResponse = $gate->resolveFrontControllerResponse($installPath, false);
        if ($blockedResponse === null || $blockedResponse->status() !== 403) {
            $failures[] = "lock만 있는 설치완료 상태에서 {$installPath}는 InstallerRouteGate로 403 차단되어야 한다.";
        }
    }

    $homeResponse = $gate->resolveFrontControllerResponse('/', false);
    if ($homeResponse !== null) {
        $failures[] = 'lock만 있는 설치완료 상태에서 GET /는 게이트가 개입하지 않아야 한다(null).';
    }
} catch (Exception $e) {
    $failures[] = '(1)-(3) in-process 테스트 실패: ' . $e->getMessage();
}

if (is_file($lockPath)) {
    @unlink($lockPath);
}
if (is_dir($tmpDir)) {
    @rmdir($tmpDir);
}

// (4) DB 미설정 상태로 실제 index.php를 띄워도 라우팅이 동일하게 동작해야 한다.
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_install_complete_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_install_complete_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_install_complete_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
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
    $realLockPath = $configDir . '/install.lock';
    $lockExistedBefore = is_file($realLockPath);

    $port = mintwiki_install_complete_route_free_port();
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
        mintwiki_install_complete_route_wait_for_server($port);

        [$getStatus, $getBody] = mintwiki_install_complete_route_http_get($port, '/install/complete');
        if ($getStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /install/complete는 200을 반환해야 하는데 ' . $getStatus . '이었다.';
        }
        if (!str_contains($getBody, '<h1>설치 완료</h1>')) {
            $failures[] = 'DB 미설정 상태에서 GET /install/complete 응답은 완료 화면이어야 한다.';
        }
        if (!is_file($realLockPath)) {
            $failures[] = 'GET /install/complete 호출 후 실제 config/install.lock이 기록되어야 한다.';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DB_ENV_KEYS as $key) {
            putenv($key);
        }
        if (!$lockExistedBefore) {
            @unlink($realLockPath);
        }
    }
} catch (Exception $e) {
    $failures[] = '(4) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /install/complete route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /install/complete route 테스트 통과.\n");
exit(0);
