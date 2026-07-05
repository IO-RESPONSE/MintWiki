<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서 저장소의 메모리 기반 구현 (태스크 0435).
 *
 * Python `InMemoryDocumentRepository`(src/modules/document/repository.py)와
 * 동작을 맞춘 `Repository` 구현체. DB 연동 전 단계의 테스트/개발용으로
 * id -> Document 맵과 normalizedTitle -> id 맵을 함께 유지해 중복 제목을
 * 막는다.
 */
final class InMemoryRepository implements Repository
{
    /** @var array<string, Document> */
    private array $documents = [];

    /** @var array<string, string> */
    private array $normalizedTitleToId = [];

    /**
     * @throws DuplicateNormalizedTitleError normalizedTitle이 이미 존재하는 경우
     */
    public function create(Document $document): Document
    {
        if (isset($this->normalizedTitleToId[$document->normalizedTitle()])) {
            throw new DuplicateNormalizedTitleError();
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

    /**
     * @throws NotFoundError document의 id가 저장소에 없는 경우
     */
    public function update(Document $document): Document
    {
        if (!isset($this->documents[$document->id()])) {
            throw new NotFoundError();
        }

        $this->documents[$document->id()] = $document;

        return $document;
    }

    /**
     * @throws NotFoundError document의 id가 저장소에 없는 경우
     */
    public function delete(string $id): void
    {
        if (!isset($this->documents[$id])) {
            throw new NotFoundError();
        }

        $normalizedTitle = $this->documents[$id]->normalizedTitle();
        unset($this->documents[$id]);
        unset($this->normalizedTitleToId[$normalizedTitle]);
    }
}
