<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서를 표현하는 불변 value object (태스크 0400).
 *
 * id, title, normalizedTitle, currentRevisionId 네 필드를 두어 Python
 * `Document`(src/modules/document/model.py)와 계약을 맞춘다.
 * normalizedTitle은 현재 title을 그대로 복사하는 임시 동작이다 — 실제
 * 정규화 규칙(공백 트림/축소, 빈 제목 거부)은 0401(PHP 제목 정규화기
 * 추가)에서 이 클래스에 연결된다.
 */
final class Document
{
    private readonly string $normalizedTitle;

    public function __construct(
        private readonly string $id,
        private readonly string $title,
        private readonly ?string $currentRevisionId = null
    ) {
        $this->normalizedTitle = $this->title;
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
