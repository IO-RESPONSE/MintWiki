<?php

declare(strict_types=1);

namespace MintWiki\Audit;

use PDO;

/**
 * 관리자 감사 로그 뷰어(`GET /admin/audit`)의 "최근 이벤트" 목록 조회 (태스크 0698).
 *
 * `audit_event` 테이블(db/schema/audit_event.sql)의 occurred_at 내림차순 상위
 * N개를 읽기 전용으로 조회한다. `RecentDocumentsQuery`(태스크 0693)와 동일하게
 * 도메인 프레임워크 없이 PDO를 직접 사용하는 단순 조회기다 — 감사 이벤트 기록
 * (record())은 기존 파이프라인의 책임이고 이 클래스는 조회만 담당한다.
 *
 * 페이지 크기 상한을 self::MAX_LIMIT로 두어, 호출자가 더 큰 값을 넘겨도
 * 한 번에 과도한 행을 읽어오지 않게 한다.
 */
final class RecentAuditEventsQuery
{
    private const MAX_LIMIT = 100;

    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * @return AuditEventRecord[] occurred_at 내림차순으로 정렬된 감사 이벤트 목록
     */
    public function listRecentEvents(int $limit = self::MAX_LIMIT): array
    {
        $cappedLimit = min($limit, self::MAX_LIMIT);

        $statement = $this->connection->prepare(
            'SELECT id, category, action, entity_id, related_entity_id, actor_id, occurred_at '
            . 'FROM audit_event ORDER BY occurred_at DESC LIMIT :limit'
        );
        $statement->bindValue('limit', $cappedLimit, PDO::PARAM_INT);
        $statement->execute();

        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);

        return array_map(
            static fn (array $row): AuditEventRecord => new AuditEventRecord(
                (string) $row['id'],
                (string) $row['category'],
                (string) $row['action'],
                (string) $row['entity_id'],
                $row['related_entity_id'] === null ? null : (string) $row['related_entity_id'],
                $row['actor_id'] === null ? null : (string) $row['actor_id'],
                (string) $row['occurred_at']
            ),
            $rows
        );
    }
}
