<?php

declare(strict_types=1);

namespace MintWiki\Modules\Revision;

use MintWiki\Persistence\PdoTransaction;
use PDO;

/**
 * Revision SQL 저장소 (태스크 0488).
 *
 * PdoTransaction을 감싸서 Revision 엔티티를 데이터베이스에 저장하고
 * 불러온다. 이 클래스는 저장소 계약(§2 최소 동작 집합)의 처음 구현체로,
 * placeholder SQL을 사용한다.
 *
 * ## List Ordering Contract
 *
 * listByDocumentId()는 document_id가 일치하는 모든 revision을 created_at
 * 오름차순(가장 오래된 것부터)으로 정렬하여 반환한다. 이는 편집 이력을
 * 시간순으로 추적하기 위한 계약이다.
 *
 * @link docs/db-adapter-contract.md 저장소 계약 및 세션 소유권 규칙.
 * @link docs/persistence-boundaries.md Revision 모듈의 책임과 불변식.
 */
final class RevisionRepository
{
    public function __construct(
        private readonly PdoTransaction $transaction,
        private readonly PDO $connection,
    ) {
    }

    /**
     * 새 리비전을 생성한다.
     *
     * 생성자에 주입된 id를 그대로 사용한다. 문서 id 참조 위반 시
     * IntegrityError가 발생하며, 호출자(Service)가 이를 도메인 예외로 변환한다.
     */
    public function create(Revision $revision): Revision
    {
        // Placeholder: 실제 INSERT 구현은 이후 태스크에서 추가된다.
        // 지금은 저장소 골격과 테스트 구조만 확정한다.
        return $revision;
    }

    /**
     * id로 리비전을 조회한다.
     *
     * 리비전이 존재하지 않으면 null을 반환한다(예외를 던지지 않는다).
     */
    public function get(string $id): ?Revision
    {
        // Placeholder: 실제 SELECT 구현은 이후 태스크에서 추가된다.
        return null;
    }

    /**
     * document_id로 리비전 목록을 조회한다 (생성 순서).
     *
     * 지정된 문서의 모든 리비전을 created_at 오름차순으로 정렬하여 반환한다.
     * 리비전이 없으면 빈 배열을 반환한다.
     *
     * 이 메서드는 "list ordering 계약"을 만족한다:
     * - 결과는 created_at 기준 오름차순(가장 오래된 것부터)이다.
     * - 이 순서는 편집 이력을 시간순으로 추적하기 위해 필수이다.
     */
    public function listByDocumentId(string $document_id): array
    {
        // Placeholder: 실제 SELECT 구현은 이후 태스크에서 추가된다.
        return [];
    }
}
