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
     * 네임스페이스 범위 규칙을 하나 추가한다 (태스크 0696, 최초 관리자 권한
     * 부여용).
     *
     * 같은 namespace/subject_type/subject_id/permission 조합의 규칙이 이미
     * 있으면 아무 것도 하지 않는다 — 중복 삽입을 막는다. sort_order는 해당
     * namespace에 등록된 규칙 중 가장 큰 값 + 1로 이어붙인다.
     */
    public function grantNamespacePermission(
        string $namespace,
        SubjectType $subjectType,
        Permission $permission,
        Effect $effect,
        ?string $subjectId = null
    ): void {
        if ($this->namespaceRuleExists($namespace, $subjectType, $permission, $subjectId)) {
            return;
        }

        $statement = $this->connection->prepare(
            'INSERT INTO acl_namespace_rule (id, namespace, subject_type, subject_id, permission, effect, expires_at, sort_order) '
            . 'VALUES (:id, :namespace, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
        );
        $statement->execute([
            'id' => self::generateId(),
            'namespace' => $namespace,
            'subject_type' => $subjectType->value,
            'subject_id' => $subjectId,
            'permission' => $permission->value,
            'effect' => $effect->value,
            'sort_order' => $this->nextSortOrder($namespace),
        ]);
    }

    private function namespaceRuleExists(
        string $namespace,
        SubjectType $subjectType,
        Permission $permission,
        ?string $subjectId
    ): bool {
        $statement = $this->connection->prepare(
            'SELECT 1 FROM acl_namespace_rule '
            . 'WHERE namespace = :namespace AND subject_type = :subject_type AND permission = :permission '
            . 'AND (subject_id = :subject_id_eq OR (subject_id IS NULL AND :subject_id_null IS NULL))'
        );
        $statement->execute([
            'namespace' => $namespace,
            'subject_type' => $subjectType->value,
            'permission' => $permission->value,
            'subject_id_eq' => $subjectId,
            'subject_id_null' => $subjectId,
        ]);

        return $statement->fetchColumn() !== false;
    }

    private function nextSortOrder(string $namespace): int
    {
        $statement = $this->connection->prepare(
            'SELECT MAX(sort_order) FROM acl_namespace_rule WHERE namespace = :namespace'
        );
        $statement->execute(['namespace' => $namespace]);
        $maxSortOrder = $statement->fetchColumn();

        return $maxSortOrder === false || $maxSortOrder === null ? 0 : ((int) $maxSortOrder) + 1;
    }

    /**
     * UUID v4 문자열을 생성한다 (규칙 id 발급용, `AccountRepository`/
     * `Document\Service`와 동일한 방식).
     */
    private static function generateId(): string
    {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
        $hex = bin2hex($bytes);

        return sprintf(
            '%s-%s-%s-%s-%s',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 12, 4),
            substr($hex, 16, 4),
            substr($hex, 20, 12)
        );
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
