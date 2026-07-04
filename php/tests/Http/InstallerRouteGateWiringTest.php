<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0676에서 연결하는
 * `MintWiki\Installer\InstallerRouteGate::resolveFrontControllerResponse()`
 * 프론트 컨트롤러 wiring을 확인하는 smoke test. phpunit 없이 `php` CLI만으로
 * 실행된다.
 *
 * (1)/(2)는 `resolveFrontControllerResponse()`를 직접 호출해 검증한다 —
 * in-memory SQLite로 schema_version 유무를 흉내내면 실제 MariaDB/PostgreSQL
 * 접속 없이도 태스크 0673 `AppBootstrap`이 만드는 것과 동일한 PDO 인터페이스로
 * 게이트 로직을 검증할 수 있다(태스크 0618 InstallerRouteGateTest.php와
 * 동일한 방식).
 * (3)은 DB 설정이 전혀 없는 상태로 실제 `index.php`를 `php -S`로 띄워, 게이트가
 * 개입하지 않고 0674 계약(GET /, GET /health 계속 동작)이 유지되는지 확인한다
 * (FrontControllerDbWiringTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\InstallerRouteGate;

$failures = [];

// (1) 미설치 상태 → 일반 UI 요청은 /install로 유도(302 리다이렉트)한다.
// installer 라우트 자체는 접근을 허용(null)해야 한다. API 요청은 리다이렉트
// 대상에서 제외한다.
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $gate = new InstallerRouteGate($connection);

    $homeResponse = $gate->resolveFrontControllerResponse('/', false);
    if ($homeResponse === null || $homeResponse->status() !== 302) {
        $failures[] = '미설치 상태에서 GET /는 302 리다이렉트 응답이어야 한다.';
    } elseif (($homeResponse->headers()['Location'] ?? null) !== '/install') {
        $failures[] = '미설치 상태의 리다이렉트 응답은 Location: /install 이어야 한다.';
    }

    $installResponse = $gate->resolveFrontControllerResponse('/install', false);
    if ($installResponse !== null) {
        $failures[] = '미설치 상태에서 GET /install은 게이트가 막지 않아야 한다(null).';
    }

    $apiResponse = $gate->resolveFrontControllerResponse('/api/documents', true);
    if ($apiResponse !== null) {
        $failures[] = '미설치 상태에서도 API 요청(/api/...)은 리다이렉트 대상에서 제외되어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '(1) 미설치 → 설치유도 테스트 실패: ' . $e->getMessage();
}

// (2) 설치완료 상태 → installer 라우트 접근은 게이트로 차단(403)되고,
// 일반 UI 요청은 더 이상 리다이렉트되지 않는다.
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

    $installResponse = $gate->resolveFrontControllerResponse('/install', false);
    if ($installResponse === null || $installResponse->status() !== 403) {
        $failures[] = '설치완료 상태에서 GET /install은 403으로 차단되어야 한다.';
    }

    $installSubResponse = $gate->resolveFrontControllerResponse('/install/step-1', false);
    if ($installSubResponse === null || $installSubResponse->status() !== 403) {
        $failures[] = '설치완료 상태에서 /install/ 하위 경로도 403으로 차단되어야 한다.';
    }

    $homeResponse = $gate->resolveFrontControllerResponse('/', false);
    if ($homeResponse !== null) {
        $failures[] = '설치완료 상태에서 GET /는 게이트가 개입하지 않아야 한다(null).';
    }
} catch (Exception $e) {
    $failures[] = '(2) 설치완료 → 설치라우트 차단 테스트 실패: ' . $e->getMessage();
}

// (3) DB 미설정 상태 → index.php 실행 시 게이트 자체가 비활성화되어 홈/헬스체크가
// 계속 동작하고, /install도 게이트 없이 평범한 404로 응답한다.
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_gate_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_gate_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_gate_http_get(int $port, string $path): array
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
    $port = mintwiki_gate_free_port();
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
        mintwiki_gate_wait_for_server($port);

        [$homeStatus] = mintwiki_gate_http_get($port, '/');
        if ($homeStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /는 설치 게이트와 무관하게 200을 반환해야 한다.';
        }

        [$healthStatus] = mintwiki_gate_http_get($port, '/health');
        if ($healthStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /health는 설치 게이트와 무관하게 200을 반환해야 한다.';
        }

        [$installStatus] = mintwiki_gate_http_get($port, '/install');
        if ($installStatus !== 404) {
            $failures[] = 'DB 미설정 상태에서 설치 게이트는 비활성화되어야 하므로 GET /install은 평범한 404여야 한다.';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(3) 미설정 → 게이트 비활성 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "InstallerRouteGate 프론트 컨트롤러 wiring 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InstallerRouteGate 프론트 컨트롤러 wiring 테스트 통과.\n");
exit(0);
