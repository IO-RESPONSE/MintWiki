<?php

declare(strict_types=1);

/**
 * `MintWiki\Http\DocumentEditHandler`의 동작을 확인하는 smoke test (태스크 0533, 0569).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 편집 핸들러가 DocumentService를
 * 호출하고, 성공/실패 응답을 올바르게 반환하는지 확인한다. 새 리비전을 생성하고
 * 문서를 업데이트한다.
 * Idempotency key 검증도 확인한다 (태스크 0569).
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
use MintWiki\Document\NotFoundError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;
use MintWiki\Http\DocumentEditHandler;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\IdempotencyKeyService;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

// 세션 초기화
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];

// 테스트용 repository 구현
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
        if (!isset($this->documents[$document->id()])) {
            throw new NotFoundError();
        }
        $this->documents[$document->id()] = $document;
        return $document;
    }

    public function addDocument(Document $document): void
    {
        $this->documents[$document->id()] = $document;
        $this->normalizedTitleToId[$document->normalizedTitle()] = $document->id();
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
$handler = new DocumentEditHandler($documentService, $revisionRepository, $idempotencyKeyService, $viewPage);

$expectedHtmlHeaders = [
    'Content-Type' => 'text/html; charset=utf-8',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
];

// 테스트용 문서 생성
$document1 = new Document('doc-1', 'Original Title', 'rev-1');
$documentRepository->addDocument($document1);

// (1) 정상적인 문서 편집 (제목과 내용 변경)
$_SESSION = [];
$key1 = $idempotencyKeyService->generate();
$response = $handler->handle('doc-1', 'Updated Title', 'New source content', $key1);
if ($response->status() !== 200) {
    $failures[] = '성공한 편집의 status는 200이어야 한다.';
}
if ($response->headers() !== $expectedHtmlHeaders) {
    $failures[] = '성공한 편집의 Content-Type은 text/html; charset=utf-8이어야 한다.';
}
if (!str_contains($response->body(), 'Updated Title')) {
    $failures[] = '성공한 편집의 응답이 업데이트된 문서 제목을 포함해야 한다.';
}

// (2) 존재하지 않는 문서 편집
$_SESSION = [];
$key2 = $idempotencyKeyService->generate();
$response = $handler->handle('nonexistent', 'Title', 'Source', $key2);
if ($response->status() !== 404) {
    $failures[] = '존재하지 않는 문서의 편집은 404 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), '문서를 찾을 수 없습니다')) {
    $failures[] = '존재하지 않는 문서의 응답이 적절한 에러 메시지를 포함해야 한다.';
}

// (3) 빈 제목으로 편집
$_SESSION = [];
$key3 = $idempotencyKeyService->generate();
$response = $handler->handle('doc-1', '   ', 'New source', $key3);
if ($response->status() !== 400) {
    $failures[] = '빈 제목의 편집은 400 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), '제목이 비어있습니다')) {
    $failures[] = '빈 제목의 응답이 적절한 에러 메시지를 포함해야 한다.';
}

// (4) 제목만 변경 (내용은 그대로)
$document2 = new Document('doc-2', 'Second Doc');
$documentRepository->addDocument($document2);
$_SESSION = [];
$key4 = $idempotencyKeyService->generate();
$response = $handler->handle('doc-2', 'Second Doc Updated', 'Old source', $key4);
if ($response->status() !== 200) {
    $failures[] = '제목만 변경한 편집은 200 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), 'Second Doc Updated')) {
    $failures[] = '제목만 변경한 편집의 응답이 업데이트된 제목을 포함해야 한다.';
}

// (5) 내용만 변경 (제목은 그대로)
$document3 = new Document('doc-3', 'Third Doc');
$documentRepository->addDocument($document3);
$_SESSION = [];
$key5 = $idempotencyKeyService->generate();
$response = $handler->handle('doc-3', 'Third Doc', 'Updated source content', $key5);
if ($response->status() !== 200) {
    $failures[] = '내용만 변경한 편집은 200 상태코드를 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentEditHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentEditHandler 테스트 통과.\n");
exit(0);
