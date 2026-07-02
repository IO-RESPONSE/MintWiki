<?php

declare(strict_types=1);

namespace MintWiki\Modules\Document;

/**
 * Document 도메인 모델 (태스크 0487).
 *
 * 문서 저장소가 다루는 Document 엔티티를 표현한다. id는 애플리케이션이
 * 생성해서 주입하고, 저장소는 그 id를 그대로 사용한다.
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
