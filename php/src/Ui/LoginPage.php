<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 로그인 page의 서버 렌더링 (태스크 0538).
 *
 * 사용자가 인증 정보를 입력하는 준비 화면이다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class LoginPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 로그인 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>로그인</h1>'
            . '<p>인증 준비 중입니다.</p>'
            . '</main>';

        return $this->layout->render('로그인', $body);
    }
}
