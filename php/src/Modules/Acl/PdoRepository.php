<?php

declare(strict_types=1);

namespace MintWiki\Acl;

use DateTimeImmutable;
use DateTimeZone;
use PDO;

/**
 * `acl_rule`/`acl_namespace_rule` 테이블에 대한 최소 영속화 (태스크 0687).
 *
 * `db/schema/acl_rule.sql`(문서 범위 규칙)과
 * `db/schema/acl_namespace_rule.sql`(네임스페이스 기본값 범위 규칙)을
 * 그대로 사용한다. `Document\PdoRepository`/`Revision\PdoRepository`와
 * 같은 패턴으로, 두 테이블 모두 `sort_order` 오름차순으로 조회해
 * `AclService`의 first-match-wins 순서를 그대로 재현한다.
 *
 * 만료된 규칙(`expires_at`이 과거)은 여기서 걸러낸다 —
 * `AclService::check()`는 now 인자를 받지 않으므로 만료를 검사하지
 * 않는다(Rule.php 문서 참고). 이 필터링이 "규칙 목록을 구성하는
 * 호출자"의 책임을 이 클래스가 수행하는 지점이다.
 */
final class PdoRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * 주어진 문서 id에 등록된 ACL 규칙으로 `DocumentAcl`을 만든다. 규칙이
     * 없으면 빈 `DocumentAcl`을 반환한다(hasRules()가 false여서
     * `AclService`가 네임스페이스 기본값으로 대체한다).
     */
    public function documentAcl(string $documentId): DocumentAcl
    {
        $statement = $this->connection->prepare(
            'SELECT id, subject_type, subject_id, permission, effect, expires_at '
            . 'FROM acl_rule WHERE document_id = :document_id ORDER BY sort_order ASC'
        );
        $statement->execute(['document_id' => $documentId]);

        return new DocumentAcl($documentId, self::rowsToRules($statement->fetchAll(PDO::FETCH_ASSOC)));
    }

    /**
     * 주어진 네임스페이스에 등록된 기본 ACL 규칙을 조회한다.
     *
     * @return Rule[]
     */
    public function namespaceRules(string $namespace): array
    {
        $statement = $this->connection->prepare(
            'SELECT id, subject_type, subject_id, permission, effect, expires_at '
            . 'FROM acl_namespace_rule WHERE namespace = :namespace ORDER BY sort_order ASC'
        );
        $statement->execute(['namespace' => $namespace]);

        return self::rowsToRules($statement->fetchAll(PDO::FETCH_ASSOC));
    }

    /**
     * @param array<int, array<string, mixed>> $rows
     * @return Rule[]
     */
    private static function rowsToRules(array $rows): array
    {
        $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));
        $rules = [];

        foreach ($rows as $row) {
            $expiresAt = $row['expires_at'] !== null
                ? new DateTimeImmutable((string) $row['expires_at'], new DateTimeZone('UTC'))
                : null;

            $rule = new Rule(
                (string) $row['id'],
                SubjectType::from((string) $row['subject_type']),
                Permission::from((string) $row['permission']),
                Effect::from((string) $row['effect']),
                $row['subject_id'] === null ? null : (string) $row['subject_id'],
                $expiresAt
            );

            if ($rule->isExpired($now)) {
                continue;
            }

            $rules[] = $rule;
        }

        return $rules;
    }
}
