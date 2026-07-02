<?php

declare(strict_types=1);

namespace MintWiki\Revision;

/**
 * 문서 리비전을 표현하는 불변 value object (태스크 0404).
 *
 * id, documentId, source, authorId, summary, parentRevisionId 여섯 필드를
 * 두어 Python `Revision`(src/modules/revision/model.py)과 필드를 맞춘다.
 * parentRevisionId는 선택 필드로, 첫 리비전은 null이다. Document와 달리
 * 정규화 로직은 없다 — source/summary를 그대로 저장한다.
 */
final class Revision
{
    public function __construct(
        private readonly string $id,
        private readonly string $documentId,
        private readonly string $source,
        private readonly string $authorId,
        private readonly string $summary,
        private readonly ?string $parentRevisionId = null
    ) {
    }

    public function id(): string
    {
        return $this->id;
    }

    public function documentId(): string
    {
        return $this->documentId;
    }

    public function source(): string
    {
        return $this->source;
    }

    public function authorId(): string
    {
        return $this->authorId;
    }

    public function summary(): string
    {
        return $this->summary;
    }

    public function parentRevisionId(): ?string
    {
        return $this->parentRevisionId;
    }
}

namespace MintWiki\Modules\Revision;

/**
 * DB 트랙의 SQL repository smoke test가 사용하는 간단한 DTO.
 *
 * PHP 런타임 트랙의 `MintWiki\Revision\Revision`과 별도 네임스페이스로
 * 유지해 두 트랙의 산출물을 한 브랜치에서 같이 검증한다.
 */
final class Revision
{
    public function __construct(
        public readonly string $id,
        public readonly string $document_id,
        public readonly string $source,
        public readonly string $author_id,
        public readonly string $summary,
        public readonly ?string $parent_revision_id = null,
    ) {
    }
}
