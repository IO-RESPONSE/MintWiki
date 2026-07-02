<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 토론 스레드에 달린 댓글을 표현하는 도메인 모델 (태스크 0410).
 *
 * Python `DiscussionComment`(src/modules/discussion/comment.py)에
 * 대응한다. id/threadId/body/createdBy/createdAt은 생성 후 바뀌지 않지만,
 * isHidden/hiddenAt은 hide()로 바뀌므로 이 모델 전체를 불변으로 두지
 * 않는다. body는 Thread의 title과 달리 정규화하지 않고 그대로 저장한다
 * (Python도 trim/공백 축소 없이 검증만 한다).
 *
 * hide()는 유일한 모더레이션 동작이며 unhide/show는 없다 — 이미 숨겨진
 * 댓글에도 멱등하게 재적용되어 hiddenAt만 갱신된다. body 자체는 hide()로
 * 지워지거나 덮어써지지 않는다. toPublicView()/toModeratorView()는
 * id/threadId/createdBy/createdAt/isHidden/hiddenAt 다섯 필드를 동일하게
 * 포함하고 body 필드만 다르다 — toPublicView()는 isHidden이 true일 때
 * body를 null로 가리고, toModeratorView()는 isHidden과 무관하게 항상
 * 실제 body를 반환한다. 두 뷰 모두 Python dict 뷰(to_public_view/
 * to_moderator_view)와 1:1로 맞추기 위해 snake_case 키를 그대로 쓴다.
 */
final class Comment
{
    private bool $isHidden;
    private ?\DateTimeImmutable $hiddenAt;

    public function __construct(
        private readonly string $id,
        private readonly string $threadId,
        private readonly string $body,
        private readonly string $createdBy,
        private readonly \DateTimeImmutable $createdAt,
        bool $isHidden = false,
        ?\DateTimeImmutable $hiddenAt = null
    ) {
        if (trim($id) === '') {
            throw new EmptyCommentIdError('댓글 id는 비어있을 수 없습니다');
        }
        if (trim($threadId) === '') {
            throw new EmptyCommentThreadIdError('스레드 id는 비어있을 수 없습니다');
        }
        if (trim($body) === '') {
            throw new EmptyCommentBodyError('댓글 본문은 비어있을 수 없습니다');
        }
        if (trim($createdBy) === '') {
            throw new EmptyCommentCreatedByError('작성자 id는 비어있을 수 없습니다');
        }

        $this->isHidden = $isHidden;
        $this->hiddenAt = $hiddenAt;
    }

    public function id(): string
    {
        return $this->id;
    }

    public function threadId(): string
    {
        return $this->threadId;
    }

    public function body(): string
    {
        return $this->body;
    }

    public function createdBy(): string
    {
        return $this->createdBy;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function isHidden(): bool
    {
        return $this->isHidden;
    }

    public function hiddenAt(): ?\DateTimeImmutable
    {
        return $this->hiddenAt;
    }

    public function hide(\DateTimeImmutable $now): void
    {
        $this->isHidden = true;
        $this->hiddenAt = $now;
    }

    /**
     * @return array{id: string, thread_id: string, body: ?string, created_by: string, created_at: \DateTimeImmutable, is_hidden: bool, hidden_at: ?\DateTimeImmutable}
     */
    public function toPublicView(): array
    {
        return [
            'id' => $this->id,
            'thread_id' => $this->threadId,
            'body' => $this->isHidden ? null : $this->body,
            'created_by' => $this->createdBy,
            'created_at' => $this->createdAt,
            'is_hidden' => $this->isHidden,
            'hidden_at' => $this->hiddenAt,
        ];
    }

    /**
     * @return array{id: string, thread_id: string, body: string, created_by: string, created_at: \DateTimeImmutable, is_hidden: bool, hidden_at: ?\DateTimeImmutable}
     */
    public function toModeratorView(): array
    {
        return [
            'id' => $this->id,
            'thread_id' => $this->threadId,
            'body' => $this->body,
            'created_by' => $this->createdBy,
            'created_at' => $this->createdAt,
            'is_hidden' => $this->isHidden,
            'hidden_at' => $this->hiddenAt,
        ];
    }
}
