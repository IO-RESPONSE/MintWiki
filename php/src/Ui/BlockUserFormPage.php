<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 사용자 차단 form의 서버 렌더링 (태스크 0547).
 *
 * 관리자가 사용자를 차단하는 form을 표시한다. 사용자 ID 입력 필드와
 * 차단 사유 입력 필드를 제공한다. 모든 사용자 입력은 escaping되어
 * XSS를 방지한다. CSRF 토큰은 form에 포함되며, 폼 제출 시 검증된다.
 */
final class BlockUserFormPage
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
     * 사용자 차단 form을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     */
    public function render(array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $body = '<main>'
            . '<h1>사용자 차단</h1>'
            . $errorSummary
            . '<form method="post" action="/admin/block-user">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="user_id">사용자 ID</label>'
            . '<input type="text" id="user_id" name="user_id" required>'
            . '<label for="reason">차단 사유</label>'
            . '<textarea id="reason" name="reason" required></textarea>'
            . '<button type="submit">차단</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('사용자 차단', $body);
    }
}
