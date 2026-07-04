<?php

declare(strict_types=1);

namespace MintWiki\Revision;

use PDO;

/**
 * `Repository` 포트의 PDO 구현체 (태스크 0685).
 *
 * `db/schema/revision.sql`의 `revision` 테이블을 그대로 사용한다.
 * `Document\PdoRepository`(태스크 0683)와 같은 패턴으로, `GET/POST
 * /wiki/{title}/edit`가 실제 DB에 리비전을 기록/조회할 수 있도록
 * `Repository` 계약 전체(create/get/listByDocumentId)를 구현한다.
 *
 * 리비전은 append-only이므로(`docs/persistence-boundaries.md`) update/delete는
 * 없다. `listByDocumentId()`는 `created_at` 오름차순으로 정렬하며, 같은
 * 시각에 생성된 리비전이 있을 수 있어 `id`를 2차 정렬 기준으로 더한다.
 */
final class PdoRepository implements Repository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    public function create(Revision $revision): Revision
    {
        $statement = $this->connection->prepare(
            'INSERT INTO revision (id, document_id, source, author_id, summary, parent_revision_id, created_at) '
            . 'VALUES (:id, :document_id, :source, :author_id, :summary, :parent_revision_id, :created_at)'
        );

        $statement->execute([
            'id' => $revision->id(),
            'document_id' => $revision->documentId(),
            'source' => $revision->source(),
            'author_id' => $revision->authorId(),
            'summary' => $revision->summary(),
            'parent_revision_id' => $revision->parentRevisionId(),
            'created_at' => self::nowUtc(),
        ]);

        return $revision;
    }

    public function get(string $id): ?Revision
    {
        $statement = $this->connection->prepare(
            'SELECT id, document_id, source, author_id, summary, parent_revision_id '
            . 'FROM revision WHERE id = :id'
        );
        $statement->execute(['id' => $id]);

        $row = $statement->fetch(PDO::FETCH_ASSOC);

        return $row === false ? null : self::fromRow($row);
    }

    /**
     * @return Revision[] 생성 순서로 정렬된 리비전 목록
     */
    public function listByDocumentId(string $documentId): array
    {
        $statement = $this->connection->prepare(
            'SELECT id, document_id, source, author_id, summary, parent_revision_id '
            . 'FROM revision WHERE document_id = :document_id ORDER BY created_at ASC, id ASC'
        );
        $statement->execute(['document_id' => $documentId]);

        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);

        return array_map(self::fromRow(...), $rows);
    }

    /**
     * @param array<string, mixed> $row
     */
    private static function fromRow(array $row): Revision
    {
        return new Revision(
            (string) $row['id'],
            (string) $row['document_id'],
            (string) $row['source'],
            (string) $row['author_id'],
            (string) $row['summary'],
            $row['parent_revision_id'] === null ? null : (string) $row['parent_revision_id']
        );
    }

    private static function nowUtc(): string
    {
        return (new \DateTimeImmutable('now', new \DateTimeZone('UTC')))->format('Y-m-d H:i:s');
    }
}
