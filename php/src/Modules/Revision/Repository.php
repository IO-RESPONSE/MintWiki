<?php

declare(strict_types=1);

namespace MintWiki\Revision;

/**
 * 리비전 저장소 포트 (태스크 0405).
 *
 * Python `RevisionRepository`(src/modules/revision/repository.py)와 메서드
 * 이름/입력/출력/예외 계약을 맞춘 인터페이스. `docs/repository-port-contracts.md`
 * 의 revision 섹션이 정본이다. 구현 없이 시그니처만 고정하며 — 이 포트를
 * 구현하는 InMemory/Database 구현체는 이후 태스크(0435 등)에서 추가된다.
 *
 * 리비전은 append-only이므로 Document::Repository와 달리 `update`/`delete`
 * 메서드가 없다 — `docs/persistence-boundaries.md`가 고정한 불변성 규칙과
 * 일치하는 의도된 설계다.
 *
 * 클래스 이름은 Document\Repository와 같은 이유로 `docs/php-namespace-mapping.md`
 * 가 고정한 규칙대로 `MintWiki\Revision` namespace 안의 중복 `Revision`
 * 접두어를 뺀다.
 */
interface Repository
{
    public function create(Revision $revision): Revision;

    public function get(string $id): ?Revision;

    /**
     * @return Revision[] 생성 순서로 정렬된 리비전 목록
     */
    public function listByDocumentId(string $documentId): array;
}
