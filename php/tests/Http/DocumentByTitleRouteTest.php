<?php

declare(strict_types=1);

/**
 * `GET /api/documents/by-title`가 태스크 0683에서 `Document\Service`(+ 주입된
 * `Repository`)로 연결된 동작을 확인하는 smoke test. phpunit 없이 `php`
 * CLI만으로 실행된다(0682 InstallCompleteRouteTest.php와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직을 Router에
 * 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 저장소에 존재하는 제목으로 조회하면 200과 문서 JSON을 반환하는지.
 * (2) 저장소에 없는 제목으로 조회하면 404 JSON을 반환하는지.
 * (3) 빈 검색어(q)로 조회하면 400 JSON을 반환하는지(EmptyTitleError).
 * (4) 저장소가 주입되지 않으면(DB 미설정/오류 상태) 503 JSON을 반환하고
 *     앱이 죽지 않는지.
 * (5) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 `GET
 *     /api/documents/by-title`이 503을 반환하고, 이어지는 `GET /health`도
 *     여전히 200을 반환하는지(라이브 wiring이 프로세스를 죽이지 않는지).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\InMemoryRepository;
use MintWiki\Http\DocumentApiRoutes;
use MintWiki\Http\Request;
use MintWiki\Http\Router;

$failures = [];

// (1)-(3) InMemoryRepository를 주입해 조회 성공/미존재/빈 검색어 경로를 확인한다.
$repository = new InMemoryRepository();
$repository->create(new Document('doc-1', 'Existing Document'));

$router = new Router();
DocumentApiRoutes::register($router, $repository);

$_GET['q'] = 'Existing Document';
$handler = $router->match(new Request('GET', '/api/documents/by-title'));
if ($handler === null) {
    $failures[] = 'GET /api/documents/by-title route는 등록되어 있어야 한다.';
} else {
    $response = $handler();
    if ($response->status() !== 200) {
        $failures[] = '존재하는 제목 조회는 200을 반환해야 하는데 ' . $response->status() . '이었다.';
    }
    $payload = json_decode($response->body(), true);
    if (!is_array($payload) || ($payload['id'] ?? null) !== 'doc-1') {
        $failures[] = '존재하는 제목 조회 응답의 id는 "doc-1"이어야 한다.';
    }
    if (!is_array($payload) || ($payload['title'] ?? null) !== 'Existing Document') {
        $failures[] = '존재하는 제목 조회 응답의 title은 원래 제목과 같아야 한다.';
    }
    if (!is_array($payload) || ($payload['normalizedTitle'] ?? null) !== 'Existing Document') {
        $failures[] = '존재하는 제목 조회 응답의 normalizedTitle이 올바르지 않다.';
    }
}

$_GET['q'] = 'Nonexistent Document';
$notFoundResponse = $router->match(new Request('GET', '/api/documents/by-title'))();
if ($notFoundResponse->status() !== 404) {
    $failures[] = '존재하지 않는 제목 조회는 404를 반환해야 하는데 ' . $notFoundResponse->status() . '이었다.';
}
$notFoundPayload = json_decode($notFoundResponse->body(), true);
if (!is_array($notFoundPayload) || ($notFoundPayload['error'] ?? null) !== 'not_found') {
    $failures[] = '존재하지 않는 제목 조회 응답의 error는 "not_found"여야 한다.';
}

$_GET['q'] = '';
$emptyQueryResponse = $router->match(new Request('GET', '/api/documents/by-title'))();
if ($emptyQueryResponse->status() !== 400) {
    $failures[] = '빈 검색어 조회는 400을 반환해야 하는데 ' . $emptyQueryResponse->status() . '이었다.';
}

unset($_GET['q']);

// (4) 저장소가 주입되지 않으면(DB 미설정/오류) 503을 반환하고 죽지 않는다.
$unconfiguredRouter = new Router();
DocumentApiRoutes::register($unconfiguredRouter, null);

$_GET['q'] = 'Existing Document';
$unconfiguredResponse = $unconfiguredRouter->match(new Request('GET', '/api/documents/by-title'))();
if ($unconfiguredResponse->status() !== 503) {
    $failures[] = 'DB 미설정 상태의 조회는 503을 반환해야 하는데 ' . $unconfiguredResponse->status() . '이었다.';
}
$unconfiguredPayload = json_decode($unconfiguredResponse->body(), true);
if (!is_array($unconfiguredPayload) || ($unconfiguredPayload['error'] ?? null) !== 'db_unavailable') {
    $failures[] = 'DB 미설정 상태의 조회 응답의 error는 "db_unavailable"이어야 한다.';
}
unset($_GET['q']);

// (5) DB 미설정 상태로 실제 index.php를 띄워도 by-title이 503이고, 이후
// 요청(GET /health)도 여전히 200이어야 한다(프로세스가 죽지 않았다는 증거).
const DOCUMENT_BY_TITLE_ROUTE_DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_document_by_title_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_document_by_title_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_document_by_title_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

try {
    foreach (DOCUMENT_BY_TITLE_ROUTE_DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';

    $port = mintwiki_document_by_title_route_free_port();
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
        mintwiki_document_by_title_route_wait_for_server($port);

        [$byTitleStatus] = mintwiki_document_by_title_route_http_get($port, '/api/documents/by-title?q=Test');
        if ($byTitleStatus !== 503) {
            $failures[] = 'DB 미설정 상태에서 GET /api/documents/by-title은 503을 반환해야 하는데 ' . $byTitleStatus . '이었다.';
        }

        [$healthStatus] = mintwiki_document_by_title_route_http_get($port, '/health');
        if ($healthStatus !== 200) {
            $failures[] = 'by-title 요청 이후에도 GET /health는 200을 반환해야 하는데 ' . $healthStatus . '이었다(프로세스가 죽지 않았어야 한다).';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DOCUMENT_BY_TITLE_ROUTE_DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(5) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /api/documents/by-title route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /api/documents/by-title route 테스트 통과.\n");
exit(0);
