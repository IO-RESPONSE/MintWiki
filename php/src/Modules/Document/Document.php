<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서를 표현하는 불변 value object (태스크 0400).
 *
 * id, title, normalizedTitle, currentRevisionId 네 필드를 두어 Python
 * `Document`(src/modules/document/model.py)와 계약을 맞춘다.
 * normalizedTitle은 `Title::normalize()`(태스크 0401)가 계산한다 — 공백
 * 트림/축소를 수행하고, 결과가 빈 문자열이면 EmptyTitleError를 던진다.
 */
final class Document
{
    private readonly string $normalizedTitle;

    /**
     * @throws EmptyTitleError title이 비어있거나 공백만 있는 경우
     */
    public function __construct(
        private readonly string $id,
        private readonly string $title,
        private readonly ?string $currentRevisionId = null
    ) {
        $this->normalizedTitle = Title::normalize($this->title);
    }

    public function id(): string
    {
        return $this->id;
    }

    public function title(): string
    {
        return $this->title;
    }

    public function normalizedTitle(): string
    {
        return $this->normalizedTitle;
    }

    public function currentRevisionId(): ?string
    {
        return $this->currentRevisionId;
    }
}

namespace MintWiki\Modules\Document;

/**
 * DB 트랙의 SQL repository smoke test가 사용하는 간단한 DTO.
 *
 * PHP 런타임 트랙은 `MintWiki\Document\Document` value object를 먼저
 * 정의했으므로, 같은 파일 안에 DB 트랙의 기존 네임스페이스 계약을
 * 보존해 두 트랙의 테스트가 함께 autoload될 수 있게 한다.
 */
final class Document
{
    public function __construct(
        public readonly string $id,
        public readonly string $title,
        public readonly string $normalized_title,
        public readonly ?string $current_revision_id = null,
    ) {
    }
}
