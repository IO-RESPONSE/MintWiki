<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 신고 목록 page의 서버 렌더링 (태스크 0546).
 *
 * 빈 상태와 필터 영역을 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class AdminReportListPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 신고 목록 page를 렌더링한다.
     */
    public function render(): string
    {
        $filterArea = $this->renderFilterArea();
        $emptyState = $this->renderEmptyState();

        $body = '<main>'
            . '<h1>신고</h1>'
            . $filterArea
            . $emptyState
            . '</main>';

        return $this->layout->render('신고', $body);
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
        return '<section aria-label="신고 목록">'
            . '<p>신고가 없습니다.</p>'
            . '</section>';
    }
}
