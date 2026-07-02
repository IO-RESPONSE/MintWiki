<?php

declare(strict_types=1);

namespace MintWiki\Modules\Revision;

/**
 * Revision 도메인 모델 (태스크 0488).
 *
 * 문서 리비전 저장소가 다루는 Revision 엔티티를 표현한다. id는 애플리케이션이
 * 생성해서 주입하고, 저장소는 그 id를 그대로 사용한다.
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
