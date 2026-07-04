<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 로그인 page의 서버 렌더링 (태스크 0538, 실제 폼/제출 처리 연결은 0686).
 *
 * 아이디·비밀번호 입력 필드와 CSRF 토큰을 담은 로그인 form을 렌더링한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다. 비밀번호는 오류로 폼이
 * 다시 렌더링되더라도 절대 값으로 채우지 않는다.
 */
final class LoginPage
{
    private Escaper $escaper;
    private Layout $layout;
    private CsrfTokenService $csrfTokenService;
    private FormErrorSummary $formErrorSummary;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?CsrfTokenService $csrfTokenService = null,
        ?FormErrorSummary $formErrorSummary = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formErrorSummary = $formErrorSummary ?? new FormErrorSummary();
    }

    /**
     * 로그인 form을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 폼 검증 오류
     * @param string $username 오류로 되돌아왔을 때 다시 채울 아이디값
     */
    public function render(array $errors = [], string $username = ''): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $usernameEscaped = $this->escaper->attribute($username);
        $errorSummary = $this->formErrorSummary->render($errors);

        $body = '<main>'
            . '<h1>로그인</h1>'
            . $errorSummary
            . '<form method="post" action="/login">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="username">아이디</label>'
            . '<input type="text" id="username" name="username" autocomplete="username" value="' . $usernameEscaped . '" required>'
            . '<label for="password">비밀번호</label>'
            . '<input type="password" id="password" name="password" autocomplete="current-password" required>'
            . '<button type="submit">로그인</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('로그인', $body);
    }
}
