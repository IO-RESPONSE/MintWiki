<?php

declare(strict_types=1);

namespace MintWiki\Revision;

/**
 * 리비전 저장소의 메모리 기반 구현 (태스크 0436).
 *
 * Python `InMemoryRevisionRepository`(src/modules/revision/repository.py)와
 * 동작을 맞춘 `Repository` 구현체. id -> Revision 맵과 documentId -> id 목록
 * 맵을 함께 유지해 문서별 리비전을 생성 순서대로 조회한다. 리비전은
 * append-only이므로 Document\InMemoryRepository와 달리 `update`가 없다.
 */
final class InMemoryRepository implements Repository
{
    /** @var array<string, Revision> */
    private array $revisions = [];

    /** @var array<string, string[]> */
    private array $revisionIdsByDocumentId = [];

    public function create(Revision $revision): Revision
    {
        $this->revisions[$revision->id()] = $revision;
        $this->revisionIdsByDocumentId[$revision->documentId()][] = $revision->id();

        return $revision;
    }

    public function get(string $id): ?Revision
    {
        return $this->revisions[$id] ?? null;
    }

    /**
     * @return Revision[] 생성 순서로 정렬된 리비전 목록
     */
    public function listByDocumentId(string $documentId): array
    {
        $ids = $this->revisionIdsByDocumentId[$documentId] ?? [];

        return array_map(fn (string $id): Revision => $this->revisions[$id], $ids);
    }
}
