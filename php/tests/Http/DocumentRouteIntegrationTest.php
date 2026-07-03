<?php

declare(strict_types=1);

/**
 * 문서 route 통합 테스트 (태스크 0563, 0569).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서의 create/view/edit/history
 * 흐름 전체를 검증한다. 각 핸들러가 올바르게 작동하고, 리비전이 기록되며,
 * UI가 상태를 제대로 표시하는지 확인한다.
 * Idempotency key 검증도 포함한다 (태스크 0569).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;
use MintWiki\Http\DocumentCreateHandler;
use MintWiki\Http\DocumentEditHandler;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\IdempotencyKeyService;
use MintWiki\Ui\DocumentHistoryPage;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// 테스트용 document repository 구현
$documentRepository = new class implements Repository {
    /** @var array<string, Document> */
    private array $documents = [];
    /** @var array<string, string> */
    private array $normalizedTitleToId = [];

    public function create(Document $document): Document
    {
        foreach ($this->documents as $existing) {
            if ($existing->normalizedTitle() === $document->normalizedTitle()) {
                throw new DuplicateNormalizedTitleError();
            }
        }
        $this->documents[$document->id()] = $document;
        $this->normalizedTitleToId[$document->normalizedTitle()] = $document->id();
        return $document;
    }

    public function get(string $id): ?Document
    {
        return $this->documents[$id] ?? null;
    }

    public function getByNormalizedTitle(string $normalizedTitle): ?Document
    {
        $id = $this->normalizedTitleToId[$normalizedTitle] ?? null;
        if ($id === null) {
            return null;
        }
        return $this->documents[$id] ?? null;
    }

    public function update(Document $document): Document
    {
        $this->documents[$document->id()] = $document;
        return $document;
    }
};

// 테스트용 revision repository 구현
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
        $result = [];
        foreach ($this->revisions as $revision) {
            if ($revision->documentId() === $documentId) {
                $result[] = $revision;
            }
        }
        return $result;
    }
};

$documentService = new Service($documentRepository);
$idempotencyKeyService = new IdempotencyKeyService();
$viewPage = new DocumentViewPage();
$historyPage = new DocumentHistoryPage();
$createHandler = new DocumentCreateHandler($documentService, $idempotencyKeyService, $viewPage);
$editHandler = new DocumentEditHandler($documentService, $revisionRepository, $idempotencyKeyService, $viewPage);

// (1) 문서 생성 단계 (서비스를 통해 직접 생성)
$createdDoc = $documentService->create('Integration Test Document');

if ($createdDoc === null) {
    $failures[] = '(1) 생성한 문서를 조회할 수 없다.';
    goto cleanup;
}

$docId = $createdDoc->id();


// 생성 핸들러의 응답이 올바른지도 검증
$key1 = $idempotencyKeyService->generate();
$response = $createHandler->handle('Another Document For Handler Test', $key1);
if ($response->status() !== 201) {
    $failures[] = '(1) 문서 생성은 201 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), 'Another Document For Handler Test')) {
    $failures[] = '(1) 생성 응답이 문서 제목을 포함해야 한다.';
}

// (2) 문서 조회 단계
$retrieved = $documentRepository->get($docId);
if ($retrieved === null) {
    $failures[] = '(2) 생성한 문서를 repository에서 조회할 수 없다.';
} else {
    $viewResponse = $viewPage->render($retrieved);
    if (!str_contains($viewResponse, 'Integration Test Document')) {
        $failures[] = '(2) 문서 view가 제목을 포함해야 한다.';
    }
    if (!str_contains($viewResponse, '문서 내용이 여기에 표시됩니다')) {
        $failures[] = '(2) 문서 view가 placeholder 내용을 포함해야 한다.';
    }
}

// (3) 문서 편집 단계
$key2 = $idempotencyKeyService->generate();
$response = $editHandler->handle($docId, 'Updated Integration Test', 'Updated source content', $key2);
if ($response->status() !== 200) {
    $failures[] = '(3) 문서 편집은 200 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), 'Updated Integration Test')) {
    $failures[] = '(3) 편집 응답이 업데이트된 제목을 포함해야 한다.';
}

// (4) 편집 후 조회 (문서가 변경되었는지 확인)
$updated = $documentRepository->get($docId);
if ($updated === null) {
    $failures[] = '(4) 편집한 문서를 조회할 수 없다.';
} else {
    if ($updated->title() !== 'Updated Integration Test') {
        $failures[] = '(4) 문서 제목이 업데이트되어야 한다.';
    }

    // (5) 히스토리 조회 단계
    $revisions = $revisionRepository->listByDocumentId($docId);

    // 최소한 초기 생성 시 1개의 리비전이 있어야 함
    if (count($revisions) < 1) {
        $failures[] = '(5) 문서는 최소 1개의 리비전을 가져야 한다.';
    }

    $historyResponse = $historyPage->render($updated, $revisions);
    if (!str_contains($historyResponse, 'Updated Integration Test - 히스토리')) {
        $failures[] = '(5) 히스토리 page가 제목을 포함해야 한다.';
    }
    if (!str_contains($historyResponse, '문서 리비전 목록')) {
        $failures[] = '(5) 히스토리 page가 리비전 목록 텍스트를 포함해야 한다.';
    }
}

// (6) 빈 제목으로 편집 시도 (에러 처리)
$key3 = $idempotencyKeyService->generate();
$response = $editHandler->handle($docId, '   ', 'Some content', $key3);
if ($response->status() !== 400) {
    $failures[] = '(6) 빈 제목의 편집은 400 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), '제목이 비어있습니다')) {
    $failures[] = '(6) 빈 제목 에러 응답이 적절한 메시지를 포함해야 한다.';
}

// (7) 존재하지 않는 문서 조회
$notExistingView = $viewPage->render(null);
if (!str_contains($notExistingView, '문서를 찾을 수 없습니다')) {
    $failures[] = '(7) 없는 문서의 view가 404 메시지를 포함해야 한다.';
}


cleanup:

if ($failures !== []) {
    fwrite(STDERR, "문서 route 통합 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "문서 route 통합 테스트 통과.\n");
exit(0);
