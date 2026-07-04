<?php

declare(strict_types=1);

namespace MintWiki\Document;

use PDO;
use PDOException;

/**
 * `Repository` 포트의 PDO 구현체 (태스크 0683).
 *
 * `db/schema/document.sql`의 `document` 테이블을 그대로 사용한다.
 * `GET /api/documents/by-title`가 실제 DB로 제목 조회를 수행할 수 있도록
 * 우선 `Repository` 계약 전체(create/get/getByNormalizedTitle/update)를
 * 구현한다 — 이번 태스크가 실제로 호출하는 경로는 `getByNormalizedTitle()`
 * 뿐이지만, `Service`가 요구하는 `Repository` 인터페이스를 부분적으로만
 * 구현할 수는 없다.
 *
 * normalized_title UNIQUE 제약 위반은 SQLSTATE 23 클래스(정합성 위반)로
 * 나타난다 — MariaDB/SQLite는 '23000', PostgreSQL은 '23505'를 사용하므로
 * 앞자리 '23'만 확인해 두 DB 모두에서 이식되게 한다.
 */
final class PdoRepository implements Repository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /**
     * @throws DuplicateNormalizedTitleError normalizedTitle이 이미 존재하는 경우
     */
    public function create(Document $document): Document
    {
        $now = self::nowUtc();

        $statement = $this->connection->prepare(
            'INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at) '
            . 'VALUES (:id, :title, :normalized_title, :current_revision_id, :created_at, :updated_at)'
        );

        try {
            $statement->execute([
                'id' => $document->id(),
                'title' => $document->title(),
                'normalized_title' => $document->normalizedTitle(),
                'current_revision_id' => $document->currentRevisionId(),
                'created_at' => $now,
                'updated_at' => $now,
            ]);
        } catch (PDOException $exception) {
            if (self::isIntegrityViolation($exception)) {
                throw new DuplicateNormalizedTitleError();
            }

            throw $exception;
        }

        return $document;
    }

    public function get(string $id): ?Document
    {
        $statement = $this->connection->prepare(
            'SELECT id, title, current_revision_id FROM document WHERE id = :id'
        );
        $statement->execute(['id' => $id]);

        $row = $statement->fetch(PDO::FETCH_ASSOC);

        return $row === false ? null : self::fromRow($row);
    }

    public function getByNormalizedTitle(string $normalizedTitle): ?Document
    {
        $statement = $this->connection->prepare(
            'SELECT id, title, current_revision_id FROM document WHERE normalized_title = :normalized_title'
        );
        $statement->execute(['normalized_title' => $normalizedTitle]);

        $row = $statement->fetch(PDO::FETCH_ASSOC);

        return $row === false ? null : self::fromRow($row);
    }

    /**
     * @throws DuplicateNormalizedTitleError normalizedTitle이 이미 존재하는 경우
     * @throws NotFoundError document의 id가 저장소에 없는 경우
     */
    public function update(Document $document): Document
    {
        $existsStatement = $this->connection->prepare('SELECT 1 FROM document WHERE id = :id');
        $existsStatement->execute(['id' => $document->id()]);
        if ($existsStatement->fetchColumn() === false) {
            throw new NotFoundError();
        }

        $statement = $this->connection->prepare(
            'UPDATE document SET title = :title, normalized_title = :normalized_title, '
            . 'current_revision_id = :current_revision_id, updated_at = :updated_at WHERE id = :id'
        );

        try {
            $statement->execute([
                'id' => $document->id(),
                'title' => $document->title(),
                'normalized_title' => $document->normalizedTitle(),
                'current_revision_id' => $document->currentRevisionId(),
                'updated_at' => self::nowUtc(),
            ]);
        } catch (PDOException $exception) {
            if (self::isIntegrityViolation($exception)) {
                throw new DuplicateNormalizedTitleError();
            }

            throw $exception;
        }

        return $document;
    }

    /**
     * @param array<string, mixed> $row
     */
    private static function fromRow(array $row): Document
    {
        return new Document((string) $row['id'], (string) $row['title'], $row['current_revision_id']);
    }

    private static function nowUtc(): string
    {
        return (new \DateTimeImmutable('now', new \DateTimeZone('UTC')))->format('Y-m-d H:i:s');
    }

    private static function isIntegrityViolation(PDOException $exception): bool
    {
        return str_starts_with((string) $exception->getCode(), '23');
    }
}
