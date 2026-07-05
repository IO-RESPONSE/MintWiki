<?php

declare(strict_types=1);

/**
 * 편집 요약(변경 이유) 필드 smoke test (태스크 0707).
 *
 * `public/index.php`가 등록하는 `POST /wiki/{title}/edit` 핸들러와 동일한
 * 요약 처리 로직(정규화·길이 검증)을 이 파일 안에 재구성해 검증한다
 * (0685 DocumentEditRouteTest.php와 동일한 방식 — index.php는 재사용 가능한
 * 모듈이 아니므로 등록 로직을 그대로 복제한다).
 *
 * 검증 대상:
 * (1) 편집/새 문서 폼 모두 "편집 요약" 입력 필드를 노출하고, 검증 실패 시
 *     입력했던 요약 값이 그대로 유지되는지.
 * (2) 유효한 요약으로 저장하면 새 Revision의 summary에 그대로 반영되는지.
 * (3) 빈 요약으로 저장하면 기본 문자열로 대체되고, 정확히 500자는
 *     허용되지만 501자는 422로 거부되는지(경계값).
 * (4) 요약에 포함된 script 태그 등이 폼 렌더링에서 escape되는지(XSS).
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
 * `mintwiki_normalize_edit_summary()`(index.php)와 동일한 정규화 로직.
 */
function mintwiki_edit_summary_test_normalize(string $summaryInput): string
{
    $trimmed = trim($summaryInput);

    return $trimmed === '' ? '편집 요약 없음' : $trimmed;
}

/**
 * `public/index.php`가 등록하는 `GET/POST /wiki/{title}/edit` 핸들러 중
 * 편집 요약과 관련된 부분을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_edit_summary_routes(
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
        $summaryInput = is_string($_POST['summary'] ?? null) ? $_POST['summary'] : '';
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

        if ($documentRepository === null || $revisionRepository === null) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, true, [
                    '_form' => '데이터베이스가 설정되지 않아 저장할 수 없습니다.',
                ], $summaryInput),
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
                ], $summaryInput),
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
        if (mb_strlen(trim($summaryInput)) > 500) {
            $validationErrors['summary'] = '편집 요약은 500자 이하로 입력하세요.';
        }

        if ($validationErrors !== []) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, $validationErrors, $summaryInput),
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
                bin2hex(random_bytes(8)),
                $document->id(),
                $sourceInput,
                '',
                mintwiki_edit_summary_test_normalize($summaryInput),
                $parentRevisionId
            ));

            $document = $documentService->update(new Document($document->id(), $document->title(), $revision->id()));
        } catch (EmptyTitleError) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                    'title' => '제목을 입력하세요.',
                ], $summaryInput),
                422
            );
        } catch (DuplicateNormalizedTitleError) {
            return Response::html(
                $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                    'title' => '이미 존재하는 제목입니다.',
                ], $summaryInput),
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

$documentRepository = new DocumentInMemoryRepository();
$revisionRepository = new RevisionInMemoryRepository();

$router = new Router();
mintwiki_register_edit_summary_routes($router, $documentRepository, $revisionRepository);

// (1a) 새 문서 폼에 편집 요약 입력 필드가 노출되어야 한다.
$newFormResponse = $router->match(new Request('GET', '/wiki/New Document/edit'))();
if (!str_contains($newFormResponse->body(), '<label for="summary">편집 요약</label>')) {
    $failures[] = '새 문서 폼에 편집 요약 label이 노출되어야 한다.';
}
if (!str_contains($newFormResponse->body(), 'id="summary" name="summary"')) {
    $failures[] = '새 문서 폼에 편집 요약 입력 필드(name="summary")가 노출되어야 한다.';
}

// (1b) 기존 문서 편집 폼에도 편집 요약 입력 필드가 노출되어야 한다.
$existingDoc = $documentRepository->create(new Document('doc-1', 'Existing Document'));
$firstRevision = $revisionRepository->create(new Revision('rev-1', 'doc-1', 'Original body text', '', '최초 작성'));
$documentRepository->update(new Document('doc-1', 'Existing Document', 'rev-1'));

$editFormResponse = $router->match(new Request('GET', '/wiki/Existing Document/edit'))();
if (!str_contains($editFormResponse->body(), 'id="summary" name="summary"')) {
    $failures[] = '기존 문서 편집 폼에도 편집 요약 입력 필드가 노출되어야 한다.';
}
if (!str_contains($editFormResponse->body(), 'value=""')) {
    $failures[] = '편집 폼을 새로 열면 편집 요약은 비어 있어야 한다(리비전마다 새로 입력).';
}

// (1c) 검증 실패(빈 제목) 시 입력했던 편집 요약 값이 폼에 그대로 유지되어야 한다.
$csrfTokenService = new CsrfTokenService();
$tokenForInvalidTitle = $csrfTokenService->generate();
$_POST = [
    'title' => '',
    'source' => '내용은 있음',
    'summary' => '오타 수정',
    'csrf_token' => $tokenForInvalidTitle,
];
$invalidTitleResponse = $router->match(new Request('POST', '/wiki/Untitled/edit'))();
if ($invalidTitleResponse->status() !== 422) {
    $failures[] = '빈 제목으로 POST하면 422를 반환해야 하는데 ' . $invalidTitleResponse->status() . '이었다.';
}
if (!str_contains($invalidTitleResponse->body(), 'value="오타 수정"')) {
    $failures[] = '검증 실패 시 입력했던 편집 요약 값이 폼에 유지되어야 한다.';
}

// (2) 유효한 요약으로 저장하면 새 Revision의 summary에 그대로 반영되어야 한다.
$tokenForCreate = $csrfTokenService->generate();
$_POST = [
    'title' => 'Brand New Document',
    'source' => 'Brand new content',
    'summary' => '문서 최초 작성',
    'csrf_token' => $tokenForCreate,
];
$createResponse = $router->match(new Request('POST', '/wiki/Brand New Document/edit'))();
if ($createResponse->status() !== 302) {
    $failures[] = '유효한 새 문서 POST는 302를 반환해야 하는데 ' . $createResponse->status() . '이었다.';
}
$createdDocument = $documentRepository->getByNormalizedTitle('Brand New Document');
if ($createdDocument === null) {
    $failures[] = '새 문서 POST 이후 저장소에 문서가 생성되어 있어야 한다.';
} else {
    $createdRevisions = $revisionRepository->listByDocumentId($createdDocument->id());
    if (count($createdRevisions) !== 1) {
        $failures[] = '새로 생성된 문서는 리비전이 정확히 1개여야 한다.';
    } elseif ($createdRevisions[0]->summary() !== '문서 최초 작성') {
        $failures[] = '새 리비전의 summary는 제출한 편집 요약과 같아야 하는데 "' . $createdRevisions[0]->summary() . '"였다.';
    }
}

// (3a) 빈 요약으로 저장하면 기본 문자열로 대체되어야 한다.
$tokenForEmptySummary = $csrfTokenService->generate();
$_POST = [
    'title' => 'No Summary Document',
    'source' => 'Content without summary',
    'summary' => '   ',
    'csrf_token' => $tokenForEmptySummary,
];
$noSummaryResponse = $router->match(new Request('POST', '/wiki/No Summary Document/edit'))();
if ($noSummaryResponse->status() !== 302) {
    $failures[] = '빈 편집 요약도 저장을 막으면 안 되는데 상태 코드가 ' . $noSummaryResponse->status() . '이었다.';
}
$noSummaryDocument = $documentRepository->getByNormalizedTitle('No Summary Document');
if ($noSummaryDocument !== null) {
    $noSummaryRevisions = $revisionRepository->listByDocumentId($noSummaryDocument->id());
    if (($noSummaryRevisions[0]->summary() ?? '') === '') {
        $failures[] = '빈 편집 요약은 기본 문자열로 대체되어야 하는데 빈 문자열로 저장되었다.';
    }
}

// (3b) 정확히 500자인 편집 요약은 허용되어야 한다.
$summary500 = str_repeat('가', 500);
$tokenFor500 = $csrfTokenService->generate();
$_POST = [
    'title' => 'Summary Exactly 500',
    'source' => 'Content',
    'summary' => $summary500,
    'csrf_token' => $tokenFor500,
];
$exactly500Response = $router->match(new Request('POST', '/wiki/Summary Exactly 500/edit'))();
if ($exactly500Response->status() !== 302) {
    $failures[] = '500자인 편집 요약은 허용되어야 하는데 상태 코드가 ' . $exactly500Response->status() . '이었다.';
}

// (3c) 501자인 편집 요약은 422로 거부되어야 한다.
$summary501 = str_repeat('가', 501);
$tokenFor501 = $csrfTokenService->generate();
$_POST = [
    'title' => 'Summary 501',
    'source' => 'Content',
    'summary' => $summary501,
    'csrf_token' => $tokenFor501,
];
$tooLongResponse = $router->match(new Request('POST', '/wiki/Summary 501/edit'))();
if ($tooLongResponse->status() !== 422) {
    $failures[] = '501자인 편집 요약은 422로 거부되어야 하는데 상태 코드가 ' . $tooLongResponse->status() . '이었다.';
}
if ($documentRepository->getByNormalizedTitle('Summary 501') !== null) {
    $failures[] = '편집 요약 길이 검증에 실패하면 문서가 저장되면 안 된다.';
}

// (4) 편집 요약에 포함된 script 태그는 폼 렌더링에서 escape되어야 한다(XSS).
$xssSummary = '<script>alert("xss")</script>';
$tokenForXss = $csrfTokenService->generate();
$_POST = [
    'title' => '',
    'source' => 'content',
    'summary' => $xssSummary,
    'csrf_token' => $tokenForXss,
];
$xssResponse = $router->match(new Request('POST', '/wiki/Xss Document/edit'))();
if (str_contains($xssResponse->body(), '<script>alert("xss")</script>')) {
    $failures[] = '편집 요약의 script 태그가 escape되지 않은 채로 폼에 노출되었다.';
}
if (!str_contains($xssResponse->body(), '&lt;script&gt;')) {
    $failures[] = '편집 요약이 escape된 형태(&lt;script&gt;)로 폼에 나타나야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "편집 요약 필드 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "편집 요약 필드 테스트 통과.\n");
exit(0);
