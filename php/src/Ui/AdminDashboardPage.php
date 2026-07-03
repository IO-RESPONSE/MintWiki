<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 관리자 대시보드 page의 서버 렌더링 (태스크 0544).
 *
 * 시스템 상태, 신고, 감사 링크를 표시하는 shell을 제공한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class AdminDashboardPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 관리자 대시보드 page를 렌더링한다.
     */
    public function render(): string
    {
        $navigationArea = $this->renderNavigationArea();

        $body = '<main>'
            . '<h1>관리자 대시보드</h1>'
            . $navigationArea
            . '</main>';

        return $this->layout->render('관리자 대시보드', $body);
    }

    /**
     * 관리자 링크 navigation 영역을 렌더링한다.
     */
    private function renderNavigationArea(): string
    {
        return '<nav aria-label="관리 기능">'
            . '<ul>'
            . '<li><a href="/admin/status">시스템 상태</a></li>'
            . '<li><a href="/admin/reporting">신고</a></li>'
            . '<li><a href="/admin/audit">감사</a></li>'
            . '</ul>'
            . '</nav>';
    }
}
