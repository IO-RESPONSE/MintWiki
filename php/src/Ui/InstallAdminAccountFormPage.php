<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 설치 관리자 계정 form page의 서버 렌더링 (태스크 0624).
 *
 * 설치 프로세스에서 최초 관리자 계정 생성에 필요한 정보를 입력받는 form을
 * 표시한다. 모든 동적 값은 escaping되어 XSS를 방지하고, CSRF 토큰을 포함한다.
 */
final class InstallAdminAccountFormPage
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
     * 최초 관리자 계정 form을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 폼 검증 오류
     */
    public function render(array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $body = '<main>'
            . '<h1>관리자 계정 생성</h1>'
            . '<p>MintWiki 최초 관리자 계정 정보를 입력하세요.</p>'
            . $errorSummary
            . '<form method="post" action="/install/admin-account">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="username">관리자 ID</label>'
            . '<input type="text" id="username" name="username" autocomplete="username" required>'
            . '<label for="email">이메일</label>'
            . '<input type="email" id="email" name="email" autocomplete="email" required>'
            . '<label for="password">비밀번호</label>'
            . '<input type="password" id="password" name="password" autocomplete="new-password" required>'
            . '<label for="password_confirm">비밀번호 확인</label>'
            . '<input type="password" id="password_confirm" name="password_confirm" autocomplete="new-password" required>'
            . '<button type="submit">관리자 계정 생성</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('관리자 계정 생성', $body);
    }
}
