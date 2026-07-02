<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 최근 변경 page의 서버 렌더링 (태스크 0537).
 *
 * 빈 상태와 필터 영역을 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class RecentChangesPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 최근 변경 page를 렌더링한다.
     */
    public function render(): string
    {
        $filterArea = $this->renderFilterArea();
        $emptyState = $this->renderEmptyState();

        $body = '<main>'
            . '<h1>최근 변경</h1>'
            . $filterArea
            . $emptyState
            . '</main>';

        return $this->layout->render('최근 변경', $body);
    }

    /**
     * 필터 영역을 렌더링한다.
     */
    private function renderFilterArea(): string
    {
        return '<section aria-label="필터">'
            . '<p>필터</p>'
            . '</section>';
    }

    /**
     * 빈 상태 메시지를 렌더링한다.
     */
    private function renderEmptyState(): string
    {
        return '<section aria-label="최근 변경 목록">'
            . '<p>최근 변경이 없습니다.</p>'
            . '</section>';
    }
}
