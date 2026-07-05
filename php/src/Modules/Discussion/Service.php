<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 토론 스레드/댓글 생성·조회 서비스 (태스크 0711).
 *
 * Python `DiscussionService`(src/modules/discussion/service.py)의
 * `create_thread`/`get_thread`/`list_threads_by_document_id`/`add_comment`/
 * `list_comments_by_thread_id` 다섯 흐름만 옮긴다. close/reopen/pause_thread,
 * hide_comment, audit_recorder 연동은 스레드 상태 전이·댓글 모더레이션이라
 * 이 태스크(저장/조회 왕복) 범위 밖이다.
 *
 * 빈 본문/작성자 검증은 새로 만들지 않는다 — `Thread`/`Comment` 생성자가
 * 이미 `Empty*Error`를 던지므로, 이 서비스는 id/생성 시각만 채워 생성자에
 * 위임한다. 스레드 생성 시 초기 상태는 `Thread`의 기본값 문자열 대신
 * `ThreadState::Open`을 명시적으로 전달해, 두 타입이 같은 값을 쓴다는
 * 사실을 코드로도 드러낸다 — `Thread`가 `ThreadState`를 검증에 쓰지
 * 않는다는 기존 설계(Thread.php docblock)는 그대로 유지된다.
 *
 * 클래스 이름은 `docs/php-namespace-mapping.md`가 고정한 규칙대로 이미
 * `MintWiki\Discussion` namespace 안에 있으므로 중복되는 `Discussion`
 * 접두어를 뺀다 (Document\Service와 동일한 패턴).
 */
final class Service
{
    public function __construct(private readonly Repository $repository)
    {
    }

    /**
     * 새로운 토론 스레드를 생성한다.
     *
     * @throws EmptyThreadDocumentIdError documentId가 비어있거나 공백만 있는 경우
     * @throws EmptyThreadTitleError title이 비어있거나 공백만 있는 경우
     * @throws EmptyThreadCreatedByError createdBy가 비어있거나 공백만 있는 경우
     */
    public function createThread(string $documentId, string $title, string $createdBy): Thread
    {
        $thread = new Thread(
            self::generateId(),
            $documentId,
            $title,
            $createdBy,
            self::nowUtc(),
            ThreadState::Open->value
        );

        return $this->repository->createThread($thread);
    }

    /**
     * 주어진 id로 토론 스레드를 조회한다. 없으면 null을 반환한다.
     */
    public function getThread(string $id): ?Thread
    {
        return $this->repository->getThread($id);
    }

    /**
     * 주어진 문서의 토론 스레드를 생성 순서대로 나열한다.
     *
     * @return Thread[]
     */
    public function listThreadsByDocumentId(string $documentId): array
    {
        return $this->repository->listThreadsByDocumentId($documentId);
    }

    /**
     * 토론 스레드에 새로운 댓글을 추가한다.
     *
     * @throws EmptyCommentThreadIdError threadId가 비어있거나 공백만 있는 경우
     * @throws EmptyCommentBodyError body가 비어있거나 공백만 있는 경우
     * @throws EmptyCommentCreatedByError createdBy가 비어있거나 공백만 있는 경우
     */
    public function addComment(string $threadId, string $body, string $createdBy): Comment
    {
        $comment = new Comment(self::generateId(), $threadId, $body, $createdBy, self::nowUtc());

        return $this->repository->createComment($comment);
    }

    /**
     * 주어진 스레드의 댓글을 생성 순서대로 나열한다.
     *
     * @return Comment[]
     */
    public function listCommentsByThreadId(string $threadId): array
    {
        return $this->repository->listCommentsByThreadId($threadId);
    }

    private static function nowUtc(): \DateTimeImmutable
    {
        return new \DateTimeImmutable('now', new \DateTimeZone('UTC'));
    }

    /**
     * UUID v4 문자열을 생성한다 (스레드/댓글 id 발급용, `Document\Service`와
     * 동일한 방식).
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
}
