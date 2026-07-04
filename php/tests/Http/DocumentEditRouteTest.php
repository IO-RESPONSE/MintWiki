<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0685에서 등록하는 `GET/POST /wiki/{title}/edit`
 * route를 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다(0684
 * DocumentViewRouteTest.php와 동일한 방식) — index.php는 재사용 가능한
 * 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 존재하지 않는 제목으로 GET하면 새 문서 작성 폼(제목/본문/CSRF 토큰)이
 *     200으로 렌더링되는지.
 * (2) 존재하는 문서로 GET하면 현재 리비전의 source로 채워진 편집 폼이
 *     렌더링되는지.
 * (3) 유효한 CSRF 토큰으로 POST하면 새 문서와 첫 리비전이 생성되고,
 *     `/wiki/{title}`로 302 리다이렉트되는지.
 * (4) 기존 문서를 유효한 CSRF 토큰으로 POST하면 새 리비전이 추가되어
 *     리비전 수가 늘어나고, 문서의 currentRevisionId가 갱신되는지.
 * (5) CSRF 토큰이 없거나 틀리면 403을 반환하고 아무것도 저장되지 않는지.
 * (6) 제목/본문이 비어있으면 422로 폼에 오류를 담아 되돌리고 아무것도
 *     저장되지 않는지.
 * (7) 저장소가 주입되지 않으면(DB 미설정/오류) GET은 빈 새 문서 폼을,
 *     POST는 503을 반환하고 앱이 죽지 않는지.
 * (8) DB 미설정 상태로 실제 `index.php`를 `php -S`로 띄워도
 *     `GET /wiki/{title}/edit`이 200(새 문서 폼)을 반환하고, 이어지는
 *     `GET /health`도 여전히 200을 반환하는지(라이브 wiring이 프로세스를
 *     죽이지 않는지).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\InMemoryRepository as DocumentInMemoryRepository;
use MintWiki\Document\Repository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Revision\InMemoryRepository as RevisionInMemoryRepository;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Ui\DocumentEditorPage;

$failures = [];

/**
 * `public/index.php`가 등록하는 `GET/POST /wiki/{title}/edit` 핸들러와
 * 동일한 등록 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_edit_route_generate_uuid_v4(): string
{
    $bytes = random_bytes(16);
    $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
    $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
    $hex = bin2hex($bytes);

    return sprintf(
        '%s-%s-%s-%s-%s',
        substr($hex, 0, 8),
        substr($hex, 8, 4),
        substr($hex, 12, 4),
        substr($hex, 16, 4),
        substr($hex, 20, 12)
    );
}

function mintwiki_register_document_edit_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?RevisionRepository $revisionRepository
): void {
    $router->register('GET', '/wiki/{title}/edit', static function (array $params) use ($documentRepository, $revisionRepository): Response {
        $documentEditorPage = new DocumentEditorPage();
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html($documentEditorPage->render($requestedTitle, $requestedTitle, '', true));
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html($documentEditorPage->render($requestedTitle, $requestedTitle, '', true));
        }

        $source = '';
        if ($revisionRepository !== null && $document->currentRevisionId() !== null) {
            $source = $revisionRepository->get($document->currentRevisionId())?->source() ?? '';
        }

        return Response::html($documentEditorPage->render($requestedTitle, $document->title(), $source, false));
    });

    $router->register('POST', '/wiki/{title}/edit', static function (array $params) use ($documentRepository, $revisionRepository): Response {
        $documentEditorPage = new DocumentEditorPage();
        $csrfTokenService = new CsrfTokenService();
        $requestedTitle = rawurldecode($params['title'] ?? '');

        $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
        $sourceInput = is_string($_POST['source'] ?? null) ? $_POST['source'] : '';
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

        if ($documentRepository === null || $revisionRepository === null) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, true, [
                    '_form' => '데이터베이스가 설정되지 않아 저장할 수 없습니다.',
                ]),
                503
            );
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $existingDocument = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $existingDocument = null;
        }
        $isNew = $existingDocument === null;

        if (!$csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                    '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
                ]),
                403
            );
        }

        $validationErrors = [];
        if (trim($titleInput) === '') {
            $validationErrors['title'] = '제목을 입력하세요.';
        }
        if (trim($sourceInput) === '') {
            $validationErrors['source'] = '내용을 입력하세요.';
        }

        if ($validationErrors !== []) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, $validationErrors),
                422
            );
        }

        try {
            if ($existingDocument === null) {
                $document = $documentService->create($titleInput);
                $parentRevisionId = null;
            } else {
                $document = $existingDocument;
                if ($document->title() !== $titleInput) {
                    $document = $documentService->update(new Document($document->id(), $titleInput, $document->currentRevisionId()));
                }
                $parentRevisionId = $document->currentRevisionId();
            }

            $revision = $revisionRepository->create(new Revision(
                mintwiki_edit_route_generate_uuid_v4(),
                $document->id(),
                $sourceInput,
                '',
                '',
                $parentRevisionId
            ));

            $document = $documentService->update(new Document($document->id(), $document->title(), $revision->id()));
        } catch (EmptyTitleError) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                    'title' => '제목을 입력하세요.',
                ]),
                422
            );
        } catch (DuplicateNormalizedTitleError) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                    'title' => '이미 존재하는 제목입니다.',
                ]),
                409
            );
        }

        return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title())]);
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// (1) 존재하지 않는 제목으로 GET하면 새 문서 작성 폼이 렌더링되어야 한다.
$documentRepository = new DocumentInMemoryRepository();
$revisionRepository = new RevisionInMemoryRepository();

$router = new Router();
mintwiki_register_document_edit_routes($router, $documentRepository, $revisionRepository);

$newFormHandler = $router->match(new Request('GET', '/wiki/New Document/edit'));
if ($newFormHandler === null) {
    $failures[] = 'GET /wiki/{title}/edit route는 등록되어 있어야 한다.';
} else {
    $newFormResponse = $newFormHandler();
    if ($newFormResponse->status() !== 200) {
        $failures[] = '존재하지 않는 제목의 GET은 200을 반환해야 하는데 ' . $newFormResponse->status() . '이었다.';
    }
    if (!str_contains($newFormResponse->body(), '<h1>새 문서 만들기</h1>')) {
        $failures[] = '존재하지 않는 제목의 GET은 "새 문서 만들기" 폼을 보여줘야 한다.';
    }
    if (!str_contains($newFormResponse->body(), 'action="/wiki/New%20Document/edit"')) {
        $failures[] = '새 문서 폼의 action은 요청한 title을 가리켜야 한다.';
    }
    if (!preg_match('/name="csrf_token" value="[a-f0-9]{64}"/', $newFormResponse->body())) {
        $failures[] = '새 문서 폼은 CSRF 토큰 hidden input을 포함해야 한다.';
    }
    if (!str_contains($newFormResponse->body(), 'value="New Document"')) {
        $failures[] = '새 문서 폼의 title 필드는 요청한 title로 미리 채워져야 한다.';
    }
}

// (2) 존재하는 문서로 GET하면 현재 리비전 source로 채워진 편집 폼을 보여줘야 한다.
$existingDoc = $documentRepository->create(new Document('doc-1', 'Existing Document'));
$firstRevision = $revisionRepository->create(new Revision('rev-1', 'doc-1', 'Original body text', '', ''));
$documentRepository->update(new Document('doc-1', 'Existing Document', 'rev-1'));

$editFormResponse = $router->match(new Request('GET', '/wiki/Existing Document/edit'))();
if ($editFormResponse->status() !== 200) {
    $failures[] = '존재하는 문서의 GET은 200을 반환해야 하는데 ' . $editFormResponse->status() . '이었다.';
}
if (!str_contains($editFormResponse->body(), '<h1>문서 편집</h1>')) {
    $failures[] = '존재하는 문서의 GET은 "문서 편집" 폼을 보여줘야 한다.';
}
if (!str_contains($editFormResponse->body(), 'value="Existing Document"')) {
    $failures[] = '편집 폼의 title 필드는 문서의 현재 title로 채워져야 한다.';
}
if (!str_contains($editFormResponse->body(), 'Original body text')) {
    $failures[] = '편집 폼의 source textarea는 현재 리비전의 source로 채워져야 한다.';
}

// (3) 유효한 CSRF 토큰으로 새 문서를 POST하면 문서와 첫 리비전이 생성되고 302로
// 리다이렉트되어야 한다.
$csrfTokenService = new CsrfTokenService();
$validToken = $csrfTokenService->generate();

$_POST = ['title' => 'Brand New Document', 'source' => 'Brand new content', 'csrf_token' => $validToken];
$createResponse = $router->match(new Request('POST', '/wiki/Brand New Document/edit'))();

if ($createResponse->status() !== 302) {
    $failures[] = '유효한 새 문서 POST는 302를 반환해야 하는데 ' . $createResponse->status() . '이었다.';
}
if (($createResponse->headers()['Location'] ?? null) !== '/wiki/Brand%20New%20Document') {
    $failures[] = '새 문서 POST 성공 시 Location은 /wiki/{title}이어야 한다.';
}

$createdDocument = $documentRepository->getByNormalizedTitle('Brand New Document');
if ($createdDocument === null) {
    $failures[] = '유효한 새 문서 POST 이후 저장소에 문서가 생성되어 있어야 한다.';
} else {
    if ($createdDocument->currentRevisionId() === null) {
        $failures[] = '새로 생성된 문서는 currentRevisionId가 채워져 있어야 한다.';
    }
    $createdRevisions = $revisionRepository->listByDocumentId($createdDocument->id());
    if (count($createdRevisions) !== 1) {
        $failures[] = '새로 생성된 문서는 리비전이 정확히 1개여야 한다.';
    } elseif ($createdRevisions[0]->parentRevisionId() !== null) {
        $failures[] = '새로 생성된 문서의 첫 리비전은 parentRevisionId가 null이어야 한다.';
    } elseif ($createdRevisions[0]->source() !== 'Brand new content') {
        $failures[] = '새로 생성된 문서의 첫 리비전 source가 제출한 값과 같아야 한다.';
    }
}

// (4) 기존 문서를 유효한 CSRF 토큰으로 POST하면 리비전이 추가되어야 한다(수).
$validToken2 = $csrfTokenService->generate();
$_POST = ['title' => 'Existing Document', 'source' => 'Edited body text', 'csrf_token' => $validToken2];
$editResponse = $router->match(new Request('POST', '/wiki/Existing Document/edit'))();

if ($editResponse->status() !== 302) {
    $failures[] = '유효한 편집 POST는 302를 반환해야 하는데 ' . $editResponse->status() . '이었다.';
}
$revisionsAfterEdit = $revisionRepository->listByDocumentId('doc-1');
if (count($revisionsAfterEdit) !== 2) {
    $failures[] = '기존 문서 편집 POST 이후 리비전 수는 2개여야 하는데 ' . count($revisionsAfterEdit) . '개였다.';
} elseif ($revisionsAfterEdit[1]->parentRevisionId() !== 'rev-1') {
    $failures[] = '두 번째 리비전의 parentRevisionId는 첫 리비전의 id를 가리켜야 한다.';
}
$documentAfterEdit = $documentRepository->get('doc-1');
if ($documentAfterEdit === null || $documentAfterEdit->currentRevisionId() === 'rev-1') {
    $failures[] = '기존 문서 편집 POST 이후 currentRevisionId는 새 리비전으로 갱신되어야 한다.';
}

// (5) CSRF 토큰이 없거나 틀리면 403을 반환하고 아무것도 저장되지 않아야 한다.
$_POST = ['title' => 'CSRF Rejected Document', 'source' => 'Should not be saved', 'csrf_token' => 'invalid-token'];
$csrfRejectedResponse = $router->match(new Request('POST', '/wiki/CSRF Rejected Document/edit'))();

if ($csrfRejectedResponse->status() !== 403) {
    $failures[] = 'CSRF 토큰이 유효하지 않으면 403을 반환해야 하는데 ' . $csrfRejectedResponse->status() . '이었다.';
}
if ($documentRepository->getByNormalizedTitle('CSRF Rejected Document') !== null) {
    $failures[] = 'CSRF 검증에 실패하면 문서가 저장되면 안 된다.';
}

// (6) 제목/본문이 비어있으면 422로 폼에 오류를 담아 되돌리고 아무것도 저장되지
// 않아야 한다.
$validToken3 = $csrfTokenService->generate();
$_POST = ['title' => '', 'source' => 'Has content but no title', 'csrf_token' => $validToken3];
$emptyTitleResponse = $router->match(new Request('POST', '/wiki/Untitled/edit'))();

if ($emptyTitleResponse->status() !== 422) {
    $failures[] = '빈 제목으로 POST하면 422를 반환해야 하는데 ' . $emptyTitleResponse->status() . '이었다.';
}
if (!str_contains($emptyTitleResponse->body(), '제목을 입력하세요')) {
    $failures[] = '빈 제목 오류 메시지가 폼에 표시되어야 한다.';
}
if ($documentRepository->getByNormalizedTitle('Untitled') !== null) {
    $failures[] = '검증에 실패하면 문서가 저장되면 안 된다.';
}

$validToken4 = $csrfTokenService->generate();
$_POST = ['title' => 'Has Title But No Source', 'source' => '   ', 'csrf_token' => $validToken4];
$emptySourceResponse = $router->match(new Request('POST', '/wiki/Has Title But No Source/edit'))();

if ($emptySourceResponse->status() !== 422) {
    $failures[] = '빈 본문(공백만)으로 POST하면 422를 반환해야 하는데 ' . $emptySourceResponse->status() . '이었다.';
}
if (!str_contains($emptySourceResponse->body(), '내용을 입력하세요')) {
    $failures[] = '빈 본문 오류 메시지가 폼에 표시되어야 한다.';
}
if ($documentRepository->getByNormalizedTitle('Has Title But No Source') !== null) {
    $failures[] = '본문 검증에 실패하면 문서가 저장되면 안 된다.';
}

// (7) 저장소가 주입되지 않으면(DB 미설정/오류) GET은 빈 새 문서 폼을, POST는
// 503을 반환하고 앱이 죽지 않아야 한다.
$unconfiguredRouter = new Router();
mintwiki_register_document_edit_routes($unconfiguredRouter, null, null);

$unconfiguredGetResponse = $unconfiguredRouter->match(new Request('GET', '/wiki/Anything/edit'))();
if ($unconfiguredGetResponse->status() !== 200) {
    $failures[] = 'DB 미설정 상태의 GET은 200을 반환해야 하는데 ' . $unconfiguredGetResponse->status() . '이었다.';
}
if (!str_contains($unconfiguredGetResponse->body(), '<h1>새 문서 만들기</h1>')) {
    $failures[] = 'DB 미설정 상태의 GET도 새 문서 작성 폼을 보여줘야 한다.';
}

$_POST = ['title' => 'Anything', 'source' => 'Anything', 'csrf_token' => 'irrelevant'];
$unconfiguredPostResponse = $unconfiguredRouter->match(new Request('POST', '/wiki/Anything/edit'))();
if ($unconfiguredPostResponse->status() !== 503) {
    $failures[] = 'DB 미설정 상태의 POST는 503을 반환해야 하는데 ' . $unconfiguredPostResponse->status() . '이었다.';
}

// (8) DB 미설정 상태로 실제 index.php를 띄워도 /wiki/{title}/edit이 200(새 문서
// 폼)이고, 이후 GET /health도 여전히 200이어야 한다(프로세스가 죽지 않았다는 증거).
const DOCUMENT_EDIT_ROUTE_DB_ENV_KEYS = [
    'WIKI_MARIADB_DSN',
    'WIKI_DATABASE_URL',
    'WIKI_MARIADB_USER',
    'WIKI_MARIADB_PASSWORD',
];

function mintwiki_document_edit_route_free_port(): int
{
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
        throw new RuntimeException("임시 포트를 찾을 수 없습니다: {$errstr}");
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr($name, strrpos($name, ':') + 1);
}

function mintwiki_document_edit_route_wait_for_server(int $port, float $timeout = 5.0): void
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
function mintwiki_document_edit_route_http_get(int $port, string $path): array
{
    $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
    $responseBody = file_get_contents("http://127.0.0.1:{$port}{$path}", false, $context);
    $statusLine = $http_response_header[0] ?? '';
    preg_match('#HTTP/\S+\s+(\d+)#', $statusLine, $matches);

    return [isset($matches[1]) ? (int) $matches[1] : 0, $responseBody === false ? '' : $responseBody];
}

try {
    foreach (DOCUMENT_EDIT_ROUTE_DB_ENV_KEYS as $key) {
        putenv($key);
    }

    $publicDir = __DIR__ . '/../../public';

    $port = mintwiki_document_edit_route_free_port();
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
        mintwiki_document_edit_route_wait_for_server($port);

        [$editStatus, $editBody] = mintwiki_document_edit_route_http_get($port, '/wiki/Test/edit');
        if ($editStatus !== 200) {
            $failures[] = 'DB 미설정 상태에서 GET /wiki/{title}/edit은 200을 반환해야 하는데 ' . $editStatus . '이었다.';
        }
        if (!str_contains($editBody, '새 문서 만들기')) {
            $failures[] = 'DB 미설정 상태에서 GET /wiki/{title}/edit 응답은 새 문서 작성 폼이어야 한다.';
        }

        [$healthStatus] = mintwiki_document_edit_route_http_get($port, '/health');
        if ($healthStatus !== 200) {
            $failures[] = '/wiki/{title}/edit 요청 이후에도 GET /health는 200을 반환해야 하는데 ' . $healthStatus . '이었다(프로세스가 죽지 않았어야 한다).';
        }
    } finally {
        proc_terminate($process);
        proc_close($process);
        foreach (DOCUMENT_EDIT_ROUTE_DB_ENV_KEYS as $key) {
            putenv($key);
        }
    }
} catch (Exception $e) {
    $failures[] = '(8) 실제 index.php 라이브 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /wiki/{title}/edit route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /wiki/{title}/edit route 테스트 통과.\n");
exit(0);
