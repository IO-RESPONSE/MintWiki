<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 토론 저장소의 메모리 기반 구현 (태스크 0711).
 *
 * `Revision\InMemoryRepository`와 동일한 패턴으로, id -> 엔티티 맵과
 * 부모 id -> 자식 id 목록 맵을 함께 유지해 문서별 스레드/스레드별 댓글을
 * 생성 순서대로 조회한다.
 */
final class InMemoryRepository implements Repository
{
    /** @var array<string, Thread> */
    private array $threads = [];

    /** @var array<string, string[]> */
    private array $threadIdsByDocumentId = [];

    /** @var array<string, Comment> */
    private array $comments = [];

    /** @var array<string, string[]> */
    private array $commentIdsByThreadId = [];

    public function createThread(Thread $thread): Thread
    {
        $this->threads[$thread->id()] = $thread;
        $this->threadIdsByDocumentId[$thread->documentId()][] = $thread->id();

        return $thread;
    }

    public function getThread(string $id): ?Thread
    {
        return $this->threads[$id] ?? null;
    }

    /**
     * @return Thread[] 생성 순서로 정렬된 스레드 목록
     */
    public function listThreadsByDocumentId(string $documentId): array
    {
        $ids = $this->threadIdsByDocumentId[$documentId] ?? [];

        return array_map(fn (string $id): Thread => $this->threads[$id], $ids);
    }

    public function createComment(Comment $comment): Comment
    {
        $this->comments[$comment->id()] = $comment;
        $this->commentIdsByThreadId[$comment->threadId()][] = $comment->id();

        return $comment;
    }

    /**
     * @return Comment[] 생성 순서로 정렬된 댓글 목록
     */
    public function listCommentsByThreadId(string $threadId): array
    {
        $ids = $this->commentIdsByThreadId[$threadId] ?? [];

        return array_map(fn (string $id): Comment => $this->comments[$id], $ids);
    }
}
