<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 댓글 form의 서버 렌더링 (태스크 0549).
 *
 * 토론 스레드에 댓글을 작성하는 form을 표시한다. 댓글 본문 입력 필드를
 * 제공한다. 모든 사용자 입력은 escaping되어 XSS를 방지한다. CSRF 토큰은
 * form에 포함되며, 폼 제출 시 검증된다. 로그인하지 않은 사용자의 경우
 * 로그인 필요 상태를 표시한다.
 */
final class CommentFormPage
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
     * 댓글 form을 렌더링한다.
     *
     * @param string $threadId 토론 스레드 ID
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     * @param bool $isAuthorized 사용자가 로그인했는지 여부 (선택사항, 기본값: true)
     */
    public function render(string $threadId, array $errors = [], bool $isAuthorized = true): string
    {
        if (!$isAuthorized) {
            return $this->renderLoginRequired();
        }

        $threadIdEscaped = $this->escaper->html($threadId);
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $body = '<main>'
            . '<h1>댓글 작성</h1>'
            . $errorSummary
            . '<form method="post" action="/threads/' . $threadIdEscaped . '/comments">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="body">댓글 본문</label>'
            . '<textarea id="body" name="body" required></textarea>'
            . '<button type="submit">댓글 작성</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('댓글 작성', $body);
    }

    /**
     * 로그인 필요 상태를 렌더링한다.
     */
    private function renderLoginRequired(): string
    {
        $body = '<main>'
            . '<h1>댓글 작성</h1>'
            . '<p>댓글을 작성하려면 로그인이 필요합니다.</p>'
            . '<a href="/login">로그인</a>'
            . '</main>';

        return $this->layout->render('댓글 작성', $body);
    }
}
