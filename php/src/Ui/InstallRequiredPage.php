<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 데이터베이스 설치 필요 page의 서버 렌더링 (태스크 0588).
 *
 * 데이터베이스가 아직 설치되지 않았을 때 표시되는 안내 page이다.
 * 사용자에게 설치 절차가 필요함을 알리고 관리자가 할 수 있는 조치를 안내한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class InstallRequiredPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 설치 필요 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>설치 필요</h1>'
            . '<p>데이터베이스가 설치되지 않았습니다.</p>'
            . '<p>관리자는 데이터베이스를 설치하고 마이그레이션을 실행해야 합니다.</p>'
            . '</main>';

        return $this->layout->render('설치 필요', $body);
    }
}
