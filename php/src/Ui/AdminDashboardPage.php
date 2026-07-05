<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 관리자 대시보드 page의 서버 렌더링 (태스크 0544, `GET /admin` 배선과
 * 관리 하위 화면 링크 정리는 0697).
 *
 * 관리 하위 화면(감사 로그, 신고, 사용자 차단, 유지보수, 백업/복원, 진단)으로
 * 가는 링크 허브 역할만 하며, 실데이터 위젯은 담지 않는다(0698-0702에서
 * 각 하위 화면이 실데이터를 채운다). 링크 대상 경로는 0698-0702가 등록할
 * route와 일치한다. 모든 출력은 escaping되어 XSS를 방지한다.
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
     * 관리자 링크 navigation 영역을 렌더링한다 (0698-0702가 등록할
     * 하위 화면 route와 href를 일치시킨다).
     */
    private function renderNavigationArea(): string
    {
        return '<nav aria-label="관리 기능">'
            . '<ul>'
            . '<li><a href="/admin/audit">감사 로그</a></li>'
            . '<li><a href="/admin/reports">신고</a></li>'
            . '<li><a href="/admin/users/block">사용자 차단</a></li>'
            . '<li><a href="/admin/maintenance">유지보수</a></li>'
            . '<li><a href="/admin/backup">백업</a></li>'
            . '<li><a href="/admin/restore">복원</a></li>'
            . '<li><a href="/admin/diagnostics">진단</a></li>'
            . '</ul>'
            . '</nav>';
    }
}
