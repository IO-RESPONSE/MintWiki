<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 토론 저장소 포트 (태스크 0711).
 *
 * Python `DiscussionRepository`(src/modules/discussion/repository.py)의
 * 메서드 중 스레드 생성/조회, 댓글 생성/조회에 해당하는 최소 집합만 옮긴다.
 * Python 쪽은 update_thread/update_comment/get_comment/limit·offset
 * 페이지네이션도 갖지만, 이 태스크는 라우트 배선(0712) 전제인 저장/조회
 * 왕복만 필요하므로 댓글 수정·삭제·중첩 답글과 함께 범위 밖으로 둔다
 * (0711 태스크 노트).
 *
 * 클래스 이름은 `docs/php-namespace-mapping.md`가 고정한 규칙대로 이미
 * `MintWiki\Discussion` namespace 안에 있으므로 중복되는 `Discussion`
 * 접두어를 뺀다 (Revision\Repository와 동일한 패턴).
 */
interface Repository
{
    public function createThread(Thread $thread): Thread;

    public function getThread(string $id): ?Thread;

    /**
     * @return Thread[] 생성 순서로 정렬된 스레드 목록
     */
    public function listThreadsByDocumentId(string $documentId): array;

    public function createComment(Comment $comment): Comment;

    /**
     * @return Comment[] 생성 순서로 정렬된 댓글 목록
     */
    public function listCommentsByThreadId(string $threadId): array;
}
