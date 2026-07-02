<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서 저장소 포트 (태스크 0402).
 *
 * Python `DocumentRepository`(src/modules/document/repository.py)와 메서드
 * 이름/입력/출력/예외 계약을 맞춘 인터페이스. `docs/repository-port-contracts.md`
 * 의 document 섹션이 정본이다. 구현 없이 시그니처만 고정하며 — 이 포트를
 * 구현하는 InMemory/Database 구현체는 이후 태스크(0435 등)에서 추가된다.
 *
 * 클래스 이름은 `docs/php-namespace-mapping.md`가 고정한 규칙대로 이미
 * `MintWiki\Document` namespace 안에 있으므로 중복되는 `Document` 접두어를
 * 뺀다 (Python `DocumentService` -> PHP `MintWiki\Document\Service`와 동일한
 * 패턴).
 */
interface Repository
{
    /**
     * @throws DuplicateNormalizedTitleError normalizedTitle이 이미 존재하는 경우
     */
    public function create(Document $document): Document;

    public function get(string $id): ?Document;

    public function getByNormalizedTitle(string $normalizedTitle): ?Document;

    /**
     * @throws NotFoundError document의 id가 저장소에 없는 경우
     */
    public function update(Document $document): Document;
}
