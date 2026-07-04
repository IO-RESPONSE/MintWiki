<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0674에서 연결하는 0673 `AppBootstrap` DB
 * wiring의 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로
 * 실행된다(0419 HealthRouteTest.php와 동일한 방식) — 다만 다른 Http 테스트와
 * 달리 route 로직을 재구성하지 않고, `php -S` 내장 서버로 index.php를 직접
 * 띄워 실제 요청을 보낸다. DB 설정 부재/접속 실패를 삼키는 동작은
 * index.php의 전역 스코프 절차 코드라서, 그 파일을 실제로 실행해야만
 * 검증할 수 있다.
 *
 * 검증 대상:
 * (1) DB 설정이 전혀 없어도(WIKI_MARIADB_DSN/WIKI_DATABASE_URL 미설정)
 *     GET /와 GET /health가 여전히 200을 반환하는지
 * (2) GET /health 응답의 db 필드가 미설정 상태에서는 "unconfigured",
 *     접속할 수 없는 DB 설정이 있을 때는 "error"를 보고하는지
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

$publicDir = __DIR__ . '/../../public';
$failures = [];

// AppBootstrap이 읽는 DB 관련 환경변수 전체 — 서버를 띄우기 전에 항상
// 초기화해서, 실행 환경에 남아있을 수 있는 값이 테스트에 새어들지 않게 한다.
const DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

/**
 * 임시로 사용할 수 있는 로컬 포트를 찾는다.
 */
function mintwiki_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

/**
 * `php -S` 내장 서버가 요청을 받을 준비가 될 때까지 기다린다.
 */
function mintwiki_wait_for_server(int $port, float $timeout = 5.0): void
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
 * 주어진 경로로 GET 요청을 보내고 [status, body]를 반환한다.
 *
 * @return array{0: int, 1: string}
 */
function mintwiki_http_get(int $port, string $path): array
{
    $context = stream_context_create([
        'http' => ['method' => 'GET', 'ignore_errors' => true, 'timeout' => 5],
    ]);
    $body = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $body === false ? '' : $body];
}

/**
 * `-t $publicDir`로 index.php를 서비스하는 `php -S` 서버를 띄운다. DB
 * 관련 환경변수는 매번 초기화한 뒤 $envOverrides만 적용한다.
 *
 * @param array<string, string> $envOverrides
 * @return array{0: resource, 1: int}
 */
function mintwiki_start_server(string $publicDir, array $envOverrides): array
{
    foreach (DB_ENV_KEYS as $key) {
        putenv($key);
    }
    foreach ($envOverrides as $key => $value) {
        putenv("{$key}={$value}");
    }

    $port = mintwiki_free_port();
    $process = proc_open(
        ['php', '-S', "127.0.0.1:{$port}", '-t', $publicDir],
        [1 => ['pipe', 'w'], 2 => ['pipe', 'w']],
        $pipes,
        $publicDir
    );

    if ($process === false) {
        throw new RuntimeException('php -S 서버를 시작하지 못했습니다.');
    }

    mintwiki_wait_for_server($port);

    return [$process, $port];
}

function mintwiki_stop_server($process): void
{
    proc_terminate($process);
    proc_close($process);
    foreach (DB_ENV_KEYS as $key) {
        putenv($key);
    }
}

// (1) DB 설정이 전혀 없으면 GET /, GET /health가 200이고 db는 "unconfigured".
[$process, $port] = mintwiki_start_server($publicDir, []);
try {
    [$homeStatus] = mintwiki_http_get($port, '/');
    if ($homeStatus !== 200) {
        $failures[] = 'DB 미설정 상태에서 GET /는 200을 반환해야 한다.';
    }

    [$healthStatus, $healthBody] = mintwiki_http_get($port, '/health');
    if ($healthStatus !== 200) {
        $failures[] = 'DB 미설정 상태에서 GET /health는 200을 반환해야 한다.';
    }

    $healthPayload = json_decode($healthBody, true);
    if (!is_array($healthPayload) || ($healthPayload['db'] ?? null) !== 'unconfigured') {
        $failures[] = 'DB 미설정 상태에서 GET /health의 db 필드는 "unconfigured"여야 한다.';
    }
    if (($healthPayload['status'] ?? null) !== 'ok') {
        $failures[] = 'GET /health의 status 필드는 DB 상태와 무관하게 "ok"여야 한다.';
    }
} finally {
    mintwiki_stop_server($process);
}

// (2) DB 설정은 있지만 접속에 실패하면(127.0.0.1:1에는 아무 서버도 없음)
// 여전히 200을 반환하고 db는 "error"를 보고해야 한다.
[$process, $port] = mintwiki_start_server($publicDir, [
    'WIKI_DATABASE_URL' => 'mysql://user:pass@127.0.0.1:1/mintwiki_test',
]);
try {
    [$homeStatus] = mintwiki_http_get($port, '/');
    if ($homeStatus !== 200) {
        $failures[] = 'DB 접속 실패 상태에서도 GET /는 200을 반환해야 한다.';
    }

    [$healthStatus, $healthBody] = mintwiki_http_get($port, '/health');
    if ($healthStatus !== 200) {
        $failures[] = 'DB 접속 실패 상태에서도 GET /health는 200을 반환해야 한다.';
    }

    $healthPayload = json_decode($healthBody, true);
    if (!is_array($healthPayload) || ($healthPayload['db'] ?? null) !== 'error') {
        $failures[] = 'DB 접속에 실패하면 GET /health의 db 필드는 "error"여야 한다.';
    }
} finally {
    mintwiki_stop_server($process);
}

if ($failures !== []) {
    fwrite(STDERR, "index.php DB wiring 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "index.php DB wiring 테스트 통과.\n");
exit(0);
