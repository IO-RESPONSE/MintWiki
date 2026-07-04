<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0684에서 등록하는 `GET /wiki/{title}` route를
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다(0683
 * DocumentByTitleRouteTest.php와 동일한 방식) — index.php는 재사용 가능한
 * 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 저장소에 존재하는 제목으로 조회하면 200과 함께 문서 view HTML을 반환하는지.
 * (2) 저장소에 없는 제목으로 조회하면 404와 함께 "문서 없음 + 만들기 링크" HTML을
 *     반환하는지.
 * (3) `{title}` 세그먼트가 URL 인코딩된 제목(공백 포함)을 올바르게 디코딩해
 *     전달하는지.
 * (4) 저장소가 주입되지 않으면(DB 미설정/오류 상태) 404 HTML을 반환하고
 *     앱이 죽지 않는지.
 * (5) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도 `GET /wiki/{title}`이
 *     404를 반환하고, 이어지는 `GET /health`도 여전히 200을 반환하는지(라이브
 *     wiring이 프로세스를 죽이지 않는지).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\InMemoryRepository;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET /wiki/{title}` 핸들러와 동일한 등록
 * 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_document_view_route(Router $router, ?Repository $documentRepository): void
{
    $router->register('GET', '/wiki/{title}', static function (array $params) use ($documentRepository): Response {
        $documentViewPage = new DocumentViewPage();
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html($documentViewPage->render(null, null, $requestedTitle), 404);
        }

        $documentService = new Service($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html($documentViewPage->render(null, null, $requestedTitle), 404);
        }

        return Response::html($documentViewPage->render($document));
    });
}

// (1)/(2)/(3) InMemoryRepository를 주입해 존재/미존재/title 파라미터 추출을 확인한다.
$repository = new InMemoryRepository();
$repository->create(new Document('doc-1', 'Existing Document'));
$repository->create(new Document('doc-2', 'Hello World'));

$router = new Router();
mintwiki_register_document_view_route($router, $repository);

$handler = $router->match(new Request('GET', '/wiki/Existing Document'));
if ($handler === null) {
    $failures[] = 'GET /wiki/{title} route는 등록되어 있어야 한다.';
} else {
    $response = $handler();
    if ($response->status() !== 200) {
        $failures[] = '존재하는 제목 조회는 200을 반환해야 하는데 ' . $response->status() . '이었다.';
    }
    if (!str_contains($response->body(), '<h1>Existing Document</h1>')) {
        $failures[] = '존재하는 제목 조회 응답은 문서 제목을 h1으로 포함해야 한다.';
    }
}

$notFoundResponse = $router->match(new Request('GET', '/wiki/Nonexistent Document'))();
if ($notFoundResponse->status() !== 404) {
    $failures[] = '존재하지 않는 제목 조회는 404를 반환해야 하는데 ' . $notFoundResponse->status() . '이었다.';
}
if (!str_contains($notFoundResponse->body(), '문서를 찾을 수 없습니다')) {
    $failures[] = '존재하지 않는 제목 조회 응답은 "문서를 찾을 수 없습니다" 메시지를 포함해야 한다.';
}
if (!str_contains($notFoundResponse->body(), '문서 만들기')) {
    $failures[] = '존재하지 않는 제목 조회 응답은 문서 만들기 링크를 포함해야 한다.';
}
if (!str_contains($notFoundResponse->body(), 'href="/documents/new?title=Nonexistent%20Document"')) {
    $failures[] = '문서 만들기 링크는 요청한 제목을 URL 인코딩해 포함해야 한다.';
}

// (3) title 세그먼트에 URL 인코딩된 공백이 포함된 경우도 올바르게 디코딩되어야 한다.
$encodedHandler = $router->match(new Request('GET', '/wiki/Hello%20World'));
if ($encodedHandler === null) {
    $failures[] = 'URL 인코딩된 title 세그먼트도 route에 매칭되어야 한다.';
} else {
    $encodedResponse = $encodedHandler();
    if ($encodedResponse->status() !== 200) {
        $failures[] = 'URL 인코딩된 title(공백 포함)은 디코딩되어 200을 반환해야 하는데 ' . $encodedResponse->status() . '이었다.';
    }
    if (!str_contains($encodedResponse->body(), '<h1>Hello World</h1>')) {
        $failures[] = 'URL 인코딩된 title이 디코딩되어 문서 제목으로 조회되어야 한다.';
    }
}

// (4) 저장소가 주입되지 않으면(DB 미설정/오류) 404를 반환하고 죽지 않는다.
$unconfiguredRouter = new Router();
mintwiki_register_document_view_route($unconfiguredRouter, null);

$unconfiguredResponse = $unconfiguredRouter->match(new Request('GET', '/wiki/Existing Document'))();
if ($unconfiguredResponse->status() !== 404) {
    $failures[] = 'DB 미설정 상태의 조회는 404를 반환해야 하는데 ' . $unconfiguredResponse->status() . '이었다.';
}
if (!str_contains($unconfiguredResponse->body(), '문서를 찾을 수 없습니다')) {
    $failures[] = 'DB 미설정 상태의 조회 응답도 "문서를 찾을 수 없습니다" 메시지를 포함해야 한다.';
}

// (5) DB 미설정 상태로 실제 index.php를 띄워도 /wiki/{title}이 404이고, 이후
// 요청(GET /health)도 여전히 200이어야 한다(프로세스가 죽지 않았다는 증거).
const DOCUMENT_VIEW_ROUTE_DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_document_view_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_document_view_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_document_view_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

try {
    foreach (DOCUMENT_VIEW_ROUTE_DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';

    $port = mintwiki_document_view_route_free_port();
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
        mintwiki_document_view_route_wait_for_server($port);

        [$viewStatus, $viewBody] = mintwiki_document_view_route_http_get($port, '/wiki/Test');
        if ($viewStatus !== 404) {
            $failures[] = 'DB 미설정 상태에서 GET /wiki/{title}은 404를 반환해야 하는데 ' . $viewStatus . '이었다.';
        }
        if (!str_contains($viewBody, '문서를 찾을 수 없습니다')) {
            $failures[] = 'DB 미설정 상태에서 GET /wiki/{title} 응답은 "문서를 찾을 수 없습니다" 메시지를 포함해야 한다.';
        }

        [$healthStatus] = mintwiki_document_view_route_http_get($port, '/health');
        if ($healthStatus !== 200) {
            $failures[] = '/wiki/{title} 요청 이후에도 GET /health는 200을 반환해야 하는데 ' . $healthStatus . '이었다(프로세스가 죽지 않았어야 한다).';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DOCUMENT_VIEW_ROUTE_DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(5) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET /wiki/{title} route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /wiki/{title} route 테스트 통과.\n");
exit(0);
