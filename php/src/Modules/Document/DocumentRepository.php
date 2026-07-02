<?php

declare(strict_types=1);

namespace MintWiki\Modules\Document;

use MintWiki\Persistence\PdoTransaction;
use PDO;

/**
 * Document SQL 저장소 (태스크 0487).
 *
 * PdoTransaction을 감싸서 Document 엔티티를 데이터베이스에 저장하고
 * 불러온다. 이 클래스는 저장소 계약(§2 최소 동작 집합)의 처음 구현체로,
 * placeholder SQL을 사용한다.
 *
 * @link docs/db-adapter-contract.md 저장소 계약 및 세션 소유권 규칙.
 * @link docs/persistence-boundaries.md Document 모듈의 책임과 불변식.
 */
final class DocumentRepository
{
    public function __construct(
        private readonly PdoTransaction $transaction,
        private readonly PDO $connection,
    ) {
    }

    /**
     * 새 문서를 생성한다.
     *
     * 생성자에 주입된 id를 그대로 사용한다. normalized_title 유일성 위반 시
     * IntegrityError가 발생하며, 호출자(Service)가 이를 도메인 예외로 변환한다.
     */
    public function create(Document $document): Document
    {
        // Placeholder: 실제 INSERT 구현은 0488 이후에 추가된다.
        // 지금은 저장소 골격과 테스트 구조만 확정한다.
        return $document;
    }

    /**
     * id로 문서를 조회한다.
     *
     * 문서가 존재하지 않으면 null을 반환한다(예외를 던지지 않는다).
     */
    public function get(string $id): ?Document
    {
        // Placeholder: 실제 SELECT 구현은 0488 이후에 추가된다.
        return null;
    }

    /**
     * normalized_title로 문서를 조회한다.
     *
     * 문서가 존재하지 않으면 null을 반환한다(예외를 던지지 않는다).
     */
    public function getByNormalizedTitle(string $normalized_title): ?Document
    {
        // Placeholder: 실제 SELECT 구현은 0488 이후에 추가된다.
        return null;
    }

    /**
     * 기존 문서를 업데이트한다.
     *
     * 문서가 존재하지 않으면 호출자(Service)가 처리해야 한다.
     */
    public function update(Document $document): Document
    {
        // Placeholder: 실제 UPDATE 구현은 0488 이후에 추가된다.
        return $document;
    }
}
