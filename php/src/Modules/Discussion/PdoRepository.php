<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

use DateTimeImmutable;
use DateTimeZone;
use PDO;

/**
 * `Repository` 포트의 PDO 구현체 (태스크 0711).
 *
 * `db/schema/discussion_thread.sql`/`db/schema/discussion_comment.sql`
 * 테이블을 그대로 사용한다. `Revision\PdoRepository`의 관례를 그대로
 * 따른다 — INSERT는 컬럼을 명시적으로 나열하고, 목록 조회는
 * `created_at` 오름차순(생성 순서) + `id` 2차 정렬(tiebreaker)로 정렬한다.
 * 이 정렬 키는 각 테이블의 복합 인덱스(`(document_id, created_at, id)`,
 * `(thread_id, created_at, id)`)와 일치해 SQLite/MariaDB 양쪽에서 동일한
 * 순서를 보장한다.
 *
 * `created_at`/`closed_at`/`paused_at`/`hidden_at`은 [Portable Timestamp
 * Column Policy]에 따라 애플리케이션이 UTC로 정규화한 문자열을 그대로
 * 저장/조회한다 — `Acl\PdoRepository`가 `expires_at`에 쓰는 것과 동일한
 * 변환 방식이다.
 */
final class PdoRepository implements Repository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    public function createThread(Thread $thread): Thread
    {
        $statement = $this->connection->prepare(
            'INSERT INTO discussion_thread (id, document_id, title, created_by, status, created_at, closed_at, paused_at) '
            . 'VALUES (:id, :document_id, :title, :created_by, :status, :created_at, :closed_at, :paused_at)'
        );

        $statement->execute([
            'id' => $thread->id(),
            'document_id' => $thread->documentId(),
            'title' => $thread->title(),
            'created_by' => $thread->createdBy(),
            'status' => $thread->status(),
            'created_at' => self::formatDateTime($thread->createdAt()),
            'closed_at' => self::formatNullableDateTime($thread->closedAt()),
            'paused_at' => self::formatNullableDateTime($thread->pausedAt()),
        ]);

        return $thread;
    }

    public function getThread(string $id): ?Thread
    {
        $statement = $this->connection->prepare(
            'SELECT id, document_id, title, created_by, status, created_at, closed_at, paused_at '
            . 'FROM discussion_thread WHERE id = :id'
        );
        $statement->execute(['id' => $id]);

        $row = $statement->fetch(PDO::FETCH_ASSOC);

        return $row === false ? null : self::threadFromRow($row);
    }

    /**
     * @return Thread[] 생성 순서로 정렬된 스레드 목록
     */
    public function listThreadsByDocumentId(string $documentId): array
    {
        $statement = $this->connection->prepare(
            'SELECT id, document_id, title, created_by, status, created_at, closed_at, paused_at '
            . 'FROM discussion_thread WHERE document_id = :document_id ORDER BY created_at ASC, id ASC'
        );
        $statement->execute(['document_id' => $documentId]);

        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);

        return array_map(self::threadFromRow(...), $rows);
    }

    public function createComment(Comment $comment): Comment
    {
        $statement = $this->connection->prepare(
            'INSERT INTO discussion_comment (id, thread_id, body, created_by, is_hidden, created_at, hidden_at) '
            . 'VALUES (:id, :thread_id, :body, :created_by, :is_hidden, :created_at, :hidden_at)'
        );

        $statement->execute([
            'id' => $comment->id(),
            'thread_id' => $comment->threadId(),
            'body' => $comment->body(),
            'created_by' => $comment->createdBy(),
            'is_hidden' => $comment->isHidden() ? 1 : 0,
            'created_at' => self::formatDateTime($comment->createdAt()),
            'hidden_at' => self::formatNullableDateTime($comment->hiddenAt()),
        ]);

        return $comment;
    }

    /**
     * @return Comment[] 생성 순서로 정렬된 댓글 목록
     */
    public function listCommentsByThreadId(string $threadId): array
    {
        $statement = $this->connection->prepare(
            'SELECT id, thread_id, body, created_by, is_hidden, created_at, hidden_at '
            . 'FROM discussion_comment WHERE thread_id = :thread_id ORDER BY created_at ASC, id ASC'
        );
        $statement->execute(['thread_id' => $threadId]);

        $rows = $statement->fetchAll(PDO::FETCH_ASSOC);

        return array_map(self::commentFromRow(...), $rows);
    }

    /**
     * @param array<string, mixed> $row
     */
    private static function threadFromRow(array $row): Thread
    {
        return new Thread(
            (string) $row['id'],
            (string) $row['document_id'],
            (string) $row['title'],
            (string) $row['created_by'],
            self::toDateTime((string) $row['created_at']),
            (string) $row['status'],
            $row['closed_at'] === null ? null : self::toDateTime((string) $row['closed_at']),
            $row['paused_at'] === null ? null : self::toDateTime((string) $row['paused_at'])
        );
    }

    /**
     * @param array<string, mixed> $row
     */
    private static function commentFromRow(array $row): Comment
    {
        return new Comment(
            (string) $row['id'],
            (string) $row['thread_id'],
            (string) $row['body'],
            (string) $row['created_by'],
            self::toDateTime((string) $row['created_at']),
            (bool) $row['is_hidden'],
            $row['hidden_at'] === null ? null : self::toDateTime((string) $row['hidden_at'])
        );
    }

    private static function toDateTime(string $value): DateTimeImmutable
    {
        return new DateTimeImmutable($value, new DateTimeZone('UTC'));
    }

    private static function formatDateTime(DateTimeImmutable $value): string
    {
        return $value->format('Y-m-d H:i:s');
    }

    private static function formatNullableDateTime(?DateTimeImmutable $value): ?string
    {
        return $value === null ? null : self::formatDateTime($value);
    }
}
