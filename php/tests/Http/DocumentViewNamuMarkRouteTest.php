<?php

declare(strict_types=1);

/**
 * `GET /wiki/{title}`가 태스크 0706에서 저장된 NamuMark 문법을 실제 HTML로
 * 렌더링하는지 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0684 `DocumentViewRouteTest.php`와 동일한 방식) — index.php는 재사용 가능한
 * 모듈이 아니므로, `public/index.php`가 등록하는 것과 같은 route 등록 로직을
 * `NamuMarkDocumentRenderer`까지 포함해 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 현재 리비전 source에 저장된 NamuMark 문법('''굵게'''/[[링크]]/제목)이
 *     실제 HTML로 렌더링되는지(escape된 원문 그대로가 아니라).
 * (2) 제목이 2개 이상인 문서는 목차(TOC)가 함께 렌더링되는지.
 * (3) 원본 source에 포함된 HTML 태그는 escape되어 XSS로 이어지지 않는지.
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
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

/**
 * `public/index.php`의 `GET /wiki/{title}` 핸들러 중 렌더러 조립 부분을
 * 재구성한다(위 파일 docblock 참고) — ACL/세션 등 이 태스크와 무관한
 * 관심사는 생략하고, source->NamuMarkDocumentRenderer->HTML 연결만 검증한다.
 */
function mintwiki_register_namumark_view_route(
    Router $router,
    ?Repository $documentRepository,
    ?RevisionRepository $revisionRepository
): void {
    $router->register('GET', '/wiki/{title}', static function (array $params) use (
        $documentRepository,
        $revisionRepository
    ): Response {
        $documentViewPage = new DocumentViewPage(null, null, new NamuMarkDocumentRenderer());
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

        $source = null;
        if ($revisionRepository !== null && $document->currentRevisionId() !== null) {
            $source = $revisionRepository->get($document->currentRevisionId())?->source();
        }

        return Response::html($documentViewPage->render($document, $source));
    });
}

$revisionRepository = new class implements RevisionRepository {
    /** @var array<string, Revision> */
    private array $revisions = [];

    public function create(Revision $revision): Revision
    {
        $this->revisions[$revision->id()] = $revision;

        return $revision;
    }

    public function get(string $id): ?Revision
    {
        return $this->revisions[$id] ?? null;
    }

    public function listByDocumentId(string $documentId): array
    {
        return array_values(array_filter(
            $this->revisions,
            static fn (Revision $revision): bool => $revision->documentId() === $documentId
        ));
    }
};

$documentRepository = new InMemoryRepository();

// (1)/(3) 굵게 + 내부 링크 + HTML 태그가 섞인 문서 하나짜리 리비전.
$mixedRevision = $revisionRepository->create(new Revision(
    'rev-mixed',
    'doc-mixed',
    "'''중요한''' 문단이며 [[다른 문서]]로 이어진다. <script>alert(1)</script>",
    '',
    ''
));
$documentRepository->create(new Document('doc-mixed', '혼합 문서', $mixedRevision->id()));

// (2) 제목이 2개인 문서(목차 노출 경계 확인).
$tocSource = <<<'NAMUMARK'
== 첫째 ==
내용 1

== 둘째 ==
내용 2
NAMUMARK;
$tocRevision = $revisionRepository->create(new Revision('rev-toc', 'doc-toc', $tocSource, '', ''));
$documentRepository->create(new Document('doc-toc', '목차 문서', $tocRevision->id()));

$router = new Router();
mintwiki_register_namumark_view_route($router, $documentRepository, $revisionRepository);

// (1) 저장된 NamuMark 문법이 실제 HTML로 렌더링되어야 한다(escape된 원문이 아니라).
$mixedResponse = $router->match(new Request('GET', '/wiki/' . rawurlencode('혼합 문서')))();
if ($mixedResponse->status() !== 200) {
    $failures[] = '(1) 저장된 문서 조회는 200을 반환해야 하는데 ' . $mixedResponse->status() . '이었다.';
}
if (!str_contains($mixedResponse->body(), '<strong>중요한</strong>')) {
    $failures[] = "(1) 저장된 '''중요한'''이 <strong>으로 렌더링되어야 한다.";
}
if (!str_contains($mixedResponse->body(), '<a href="/wiki/' . rawurlencode('다른 문서') . '">다른 문서</a>')) {
    $failures[] = '(1) 저장된 [[다른 문서]]가 내부 링크로 렌더링되어야 한다.';
}

// (3) 원본 source의 HTML 태그는 escape되어야 한다(그대로 실행되면 안 된다).
if (str_contains($mixedResponse->body(), '<script>alert(1)</script>')) {
    $failures[] = '(3) source에 포함된 script 태그가 escape되지 않고 그대로 렌더링되었다.';
}
if (!str_contains($mixedResponse->body(), '&lt;script&gt;alert(1)&lt;/script&gt;')) {
    $failures[] = '(3) source에 포함된 script 태그는 escape된 형태로 표시되어야 한다.';
}

// (2) 제목이 2개인 문서는 목차(TOC)가 함께 렌더링되어야 한다.
$tocResponse = $router->match(new Request('GET', '/wiki/' . rawurlencode('목차 문서')))();
if ($tocResponse->status() !== 200) {
    $failures[] = '(2) 목차 문서 조회는 200을 반환해야 하는데 ' . $tocResponse->status() . '이었다.';
}
if (!str_contains($tocResponse->body(), '<nav class="toc"')) {
    $failures[] = '(2) 제목이 2개인 문서는 응답 HTML에 목차(<nav class="toc">)가 있어야 한다.';
}
if (!str_contains($tocResponse->body(), 'href="#첫째"') || !str_contains($tocResponse->body(), 'href="#둘째"')) {
    $failures[] = '(2) 목차 항목이 각 제목 앵커로 점프해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "GET /wiki/{title} NamuMark 렌더링 route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /wiki/{title} NamuMark 렌더링 route 테스트 통과.\n");
exit(0);
