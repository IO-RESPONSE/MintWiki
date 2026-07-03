<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Discussion\Thread;
use MintWiki\Document\Document;

/**
 * 문서의 토론 page 서버 렌더링 (태스크 0548).
 *
 * 문서의 모든 토론 스레드 목록을 시간순으로 표시한다.
 * thread가 없는 경우 "thread 없음" 상태를 표시한다.
 * 모든 사용자 입력(문서 title, 스레드 제목, 작성자 id 등)은 escaping되어 XSS를 방지한다.
 */
final class DiscussionPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 토론 page를 렌더링한다.
     *
     * @param Document $document 조회한 문서
     * @param Thread[] $threads 문서의 토론 스레드 목록
     */
    public function render(Document $document, array $threads = []): string
    {
        $title = $this->escaper->html($document->title());

        $threadList = $this->renderThreadList($threads);

        $body = '<main>'
            . '<h1>' . $title . ' - 토론</h1>'
            . $threadList
            . '</main>';

        return $this->layout->render('문서 토론', $body);
    }

    /**
     * 스레드 목록을 렌더링한다.
     *
     * @param Thread[] $threads 스레드 배열
     */
    private function renderThreadList(array $threads): string
    {
        if (empty($threads)) {
            return '<p>thread 없음</p>';
        }

        $html = '<ul>';
        foreach ($threads as $thread) {
            $html .= $this->renderThreadItem($thread);
        }
        $html .= '</ul>';

        return $html;
    }

    /**
     * 단일 스레드 항목을 렌더링한다.
     */
    private function renderThreadItem(Thread $thread): string
    {
        $threadId = $this->escaper->html($thread->id());
        $threadTitle = $this->escaper->html($thread->title());
        $createdBy = $this->escaper->html($thread->createdBy());
        $status = $this->escaper->html($thread->status());

        return '<li>'
            . 'ID: ' . $threadId
            . ' | 제목: ' . $threadTitle
            . ' | 작성자: ' . $createdBy
            . ' | 상태: ' . $status
            . '</li>';
    }
}
