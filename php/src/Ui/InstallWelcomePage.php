<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 설치 환영 page의 서버 렌더링 (태스크 0619).
 *
 * 설치 프로세스의 첫 번째 page로, 사용자를 환영하고 설치 절차를 시작한다.
 * 이 page는 시스템 요구사항 체크의 진입점이며, 설치 프로세스 전개에 필요한
 * 안내 메시지를 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class InstallWelcomePage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 설치 환영 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>설치 환영</h1>'
            . '<p>MintWiki 설치를 시작합니다.</p>'
            . '<p>다음 단계에서 시스템 요구사항을 확인하고 데이터베이스 설정을 진행합니다.</p>'
            . '</main>';

        return $this->layout->render('설치 환영', $body);
    }
}
