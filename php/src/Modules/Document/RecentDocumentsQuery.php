<?php

declare(strict_types=1);

namespace MintWiki\Document;

use PDO;

/**
 * 대문(프론트페이지)의 "최근 편집된 문서" 목록 조회 (태스크 0693).
 *
 * `document` 테이블의 updated_at 내림차순 상위 N개를 읽기 전용으로
 * 조회한다. `Repository` 계약(create/get/getByNormalizedTitle/update)과는
 * 별도의 read-only 조회로 분리했다 — `Repository` 인터페이스에 메서드를
 * 추가하면 그 인터페이스를 구현하는 다른 테스트 더블(익명 클래스)들이
 * 모두 깨지므로, 이 태스크 범위(대문 개편)에 필요한 조회만 여기에 둔다.
 */
final class RecentDocumentsQuery
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * @return Document[] updated_at 내림차순으로 정렬된 문서 목록
     */
    public function listRecentlyUpdated(int $limit = 10): array
    {
        $statement = $this->connection->prepare(
            'SELECT id, title, current_revision_id FROM document ORDER BY updated_at DESC LIMIT :limit'
        );
        $statement->bindValue('limit', $limit, PDO::PARAM_INT);
        $statement->execute();

        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);

        return array_map(
            static fn (array $row): Document => new Document(
                (string) $row['id'],
                (string) $row['title'],
                $row['current_revision_id'] === null ? null : (string) $row['current_revision_id']
            ),
            $rows
        );
    }
}
