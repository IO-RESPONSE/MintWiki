<?php

declare(strict_types=1);

namespace MintWiki\Discussion;

/**
 * 문서에 대한 토론 스레드를 표현하는 도메인 모델 (태스크 0410).
 *
 * Python `DiscussionThread`(src/modules/discussion/thread.py)에 대응한다.
 * id/documentId/title/createdBy/createdAt은 생성 후 바뀌지 않지만,
 * status/closedAt/pausedAt은 close()/reopen()/pause()로 바뀌므로 이
 * 모델 전체를 불변으로 두지 않는다 — User/Decision과 달리 mutable 하다.
 *
 * status는 "open"(기본값)/"closed"/"paused" 값을 갖는 평범한 문자열이며,
 * ThreadState enum으로 검증되지 않는다 — thread.py도 ThreadState를
 * 참조하지 않는다(src/modules/discussion/manifest.json 계약 노트).
 * close()/reopen()/pause()는 현재 상태와 무관하게 항상 성공하는 무조건
 * 전이이며, 잘못된 전이라는 개념이 없다. closedAt/pausedAt은 서로
 * 배타적이지 않다 — close()는 pausedAt을 리셋하지 않고, pause()도
 * closedAt을 리셋하지 않는다. reopen()만 closedAt을 null로 지운다.
 * isClosed()는 없다 — closed 여부는 "!isOpen() && !isPaused()"로
 * 판단해야 한다(같은 계약 노트).
 */
final class Thread
{
    private readonly string $title;
    private string $status;
    private ?\DateTimeImmutable $closedAt;
    private ?\DateTimeImmutable $pausedAt;

    public function __construct(
        private readonly string $id,
        private readonly string $documentId,
        string $title,
        private readonly string $createdBy,
        private readonly \DateTimeImmutable $createdAt,
        string $status = 'open',
        ?\DateTimeImmutable $closedAt = null,
        ?\DateTimeImmutable $pausedAt = null
    ) {
        if (trim($id) === '') {
            throw new EmptyThreadIdError('스레드 id는 비어있을 수 없습니다');
        }
        if (trim($documentId) === '') {
            throw new EmptyThreadDocumentIdError('문서 id는 비어있을 수 없습니다');
        }
        if (trim($title) === '') {
            throw new EmptyThreadTitleError('스레드 제목은 비어있을 수 없습니다');
        }
        if (trim($createdBy) === '') {
            throw new EmptyThreadCreatedByError('작성자 id는 비어있을 수 없습니다');
        }

        $this->title = trim(preg_replace('/\s+/u', ' ', $title));
        $this->status = $status;
        $this->closedAt = $closedAt;
        $this->pausedAt = $pausedAt;
    }

    public function id(): string
    {
        return $this->id;
    }

    public function documentId(): string
    {
        return $this->documentId;
    }

    public function title(): string
    {
        return $this->title;
    }

    public function createdBy(): string
    {
        return $this->createdBy;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function status(): string
    {
        return $this->status;
    }

    public function closedAt(): ?\DateTimeImmutable
    {
        return $this->closedAt;
    }

    public function pausedAt(): ?\DateTimeImmutable
    {
        return $this->pausedAt;
    }

    public function isOpen(): bool
    {
        return $this->status === 'open';
    }

    public function isPaused(): bool
    {
        return $this->status === 'paused';
    }

    public function close(\DateTimeImmutable $now): void
    {
        $this->status = 'closed';
        $this->closedAt = $now;
    }

    public function reopen(): void
    {
        $this->status = 'open';
        $this->closedAt = null;
    }

    public function pause(\DateTimeImmutable $now): void
    {
        $this->status = 'paused';
        $this->pausedAt = $now;
    }
}
