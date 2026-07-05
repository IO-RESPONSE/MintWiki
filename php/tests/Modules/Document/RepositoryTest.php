<?php

declare(strict_types=1);

/**
 * MintWiki\Document\Repository 포트의 시그니처와 예외 계약을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0400 DocumentTest.php와
 * 동일한 방식).
 *
 * 태스크 0402는 구현 없이 port만 추가하므로, 이 테스트는 실제 저장소
 * 동작이 아니라 (1) 인터페이스가 계약대로 구현 가능한지 — 익명 클래스로
 * 구현해 본다 — 와 (2) 예외 클래스가 고정된 error code를 노출하는지만
 * 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\NotFoundError;
use MintWiki\Document\Repository;

$failures = [];

if (!interface_exists(Repository::class)) {
    $failures[] = 'MintWiki\\Document\\Repository는 interface여야 한다.';
}

$repository = new class implements Repository {
    /** @var array<string, Document> */
    private array $documents = [];

    public function create(Document $document): Document
    {
        if (isset($this->documents[$document->id()])) {
            throw new DuplicateNormalizedTitleError();
        }
        $this->documents[$document->id()] = $document;
        return $document;
    }

    public function get(string $id): ?Document
    {
        return $this->documents[$id] ?? null;
    }

    public function getByNormalizedTitle(string $normalizedTitle): ?Document
    {
        foreach ($this->documents as $document) {
            if ($document->normalizedTitle() === $normalizedTitle) {
                return $document;
            }
        }
        return null;
    }

    public function update(Document $document): Document
    {
        if (!isset($this->documents[$document->id()])) {
            throw new NotFoundError();
        }
        $this->documents[$document->id()] = $document;
        return $document;
    }

    public function delete(string $id): void
    {
        if (!isset($this->documents[$id])) {
            throw new NotFoundError();
        }
        unset($this->documents[$id]);
    }
};

$created = $repository->create(new Document('doc-1', 'Title'));
if ($created->id() !== 'doc-1') {
    $failures[] = 'create()는 저장한 document를 반환해야 한다.';
}
if ($repository->get('doc-1') === null) {
    $failures[] = 'get()은 create()로 저장한 document를 조회해야 한다.';
}
if ($repository->get('missing') !== null) {
    $failures[] = 'get()은 없는 id에 대해 null을 반환해야 한다.';
}
if ($repository->getByNormalizedTitle('Title') === null) {
    $failures[] = 'getByNormalizedTitle()은 정규화된 제목으로 document를 조회해야 한다.';
}
if ($repository->getByNormalizedTitle('Missing') !== null) {
    $failures[] = 'getByNormalizedTitle()은 없는 제목에 대해 null을 반환해야 한다.';
}

$updated = $repository->update(new Document('doc-1', 'Updated Title'));
if ($updated->title() !== 'Updated Title') {
    $failures[] = 'update()는 갱신된 document를 반환해야 한다.';
}

try {
    $repository->update(new Document('doc-missing', 'Title'));
    $failures[] = 'update()는 없는 id에 대해 NotFoundError를 던져야 한다.';
} catch (NotFoundError $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

// delete() 계약 (태스크 0715): 존재하는 id는 조용히 지우고, 없는 id는
// NotFoundError를 던진다.
$repository->delete('doc-1');
if ($repository->get('doc-1') !== null) {
    $failures[] = 'delete()는 저장소에서 document를 제거해야 한다.';
}

try {
    $repository->delete('doc-missing');
    $failures[] = 'delete()는 없는 id에 대해 NotFoundError를 던져야 한다.';
} catch (NotFoundError $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

if (DuplicateNormalizedTitleError::CODE !== 'document.duplicate_title') {
    $failures[] = "DuplicateNormalizedTitleError::CODE는 'document.duplicate_title'이어야 한다.";
}
if (!(new DuplicateNormalizedTitleError()) instanceof \Exception) {
    $failures[] = 'DuplicateNormalizedTitleError는 \\Exception을 확장해야 한다.';
}

if (NotFoundError::CODE !== 'document.not_found') {
    $failures[] = "NotFoundError::CODE는 'document.not_found'이어야 한다.";
}
if (!(new NotFoundError()) instanceof \Exception) {
    $failures[] = 'NotFoundError는 \\Exception을 확장해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Repository 포트 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Repository 포트 테스트 통과.\n");
exit(0);
