<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 댓글 form의 서버 렌더링 (태스크 0549, 라우트 연결·조각 렌더링 분리는 0712).
 *
 * 토론 스레드에 댓글을 작성하는 form을 표시한다. 댓글 본문 입력 필드를
 * 제공한다. 모든 사용자 입력은 escaping되어 XSS를 방지한다. CSRF 토큰은
 * form에 포함되며, 폼 제출 시 검증된다. 로그인하지 않은 사용자의 경우
 * 로그인 필요 상태를 표시한다.
 *
 * 0712에서 `render()`가 만들던 form 마크업을 `renderForm()`으로 분리했다 —
 * `render()`는 여전히 단독 page(Layout으로 감싼 전체 HTML 문서)를 만들지만,
 * `DiscussionPage`(0712 GET /wiki/{title}/discussion)는 문서 하나에 스레드
 * 여러 개를 나열하며 각 스레드마다 이 댓글 form을 끼워 넣어야 하므로
 * Layout으로 다시 감싸지 않은 조각만 필요하다. form의 action도 실제로
 * 등록된 `POST /wiki/{title}/discussion/{threadId}/comment`(0712)를
 * 가리키도록 documentTitle 인자를 추가했다 — 기존 `/threads/{id}/comments`는
 * 등록된 적 없는 자리표시자 경로였다.
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
     * 댓글 form을 담은 단독 page를 렌더링한다.
     *
     * @param string $documentTitle 댓글이 달릴 스레드가 속한 문서의 title
     * @param string $threadId 토론 스레드 ID
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     * @param bool $isAuthorized 사용자가 로그인했는지 여부 (선택사항, 기본값: true)
     */
    public function render(string $documentTitle, string $threadId, array $errors = [], bool $isAuthorized = true): string
    {
        if (!$isAuthorized) {
            return $this->renderLoginRequired();
        }

        $body = '<main>'
            . '<h1>댓글 작성</h1>'
            . $this->renderForm($documentTitle, $threadId, $errors, $isAuthorized)
            . '</main>';

        return $this->layout->render('댓글 작성', $body);
    }

    /**
     * 댓글 form 조각(fragment)을 렌더링한다. `DiscussionPage`가 스레드마다
     * 이 조각을 그대로 끼워 넣어 쓴다 — Layout으로 감싸지 않은 채 반환한다.
     *
     * @param string $documentTitle 댓글이 달릴 스레드가 속한 문서의 title
     * @param string $threadId 토론 스레드 ID
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     * @param bool $isAuthorized 사용자가 로그인했는지 여부 (선택사항, 기본값: true)
     */
    public function renderForm(string $documentTitle, string $threadId, array $errors = [], bool $isAuthorized = true): string
    {
        if (!$isAuthorized) {
            return $this->renderLoginRequiredNotice();
        }

        $actionEscaped = $this->escaper->attribute(
            '/wiki/' . rawurlencode($documentTitle) . '/discussion/' . rawurlencode($threadId) . '/comment'
        );
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        return $errorSummary
            . '<form method="post" action="' . $actionEscaped . '">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="body">댓글 본문</label>'
            . '<textarea id="body" name="body" required></textarea>'
            . '<button type="submit">댓글 작성</button>'
            . '</form>';
    }

    /**
     * 로그인 필요 안내 조각을 렌더링한다(`renderLoginRequired()`의 본문 부분만).
     */
    private function renderLoginRequiredNotice(): string
    {
        return '<p>댓글을 작성하려면 로그인이 필요합니다.</p>'
            . '<a href="/login">로그인</a>';
    }

    /**
     * 로그인 필요 상태를 렌더링한다.
     */
    private function renderLoginRequired(): string
    {
        $body = '<main>'
            . '<h1>댓글 작성</h1>'
            . $this->renderLoginRequiredNotice()
            . '</main>';

        return $this->layout->render('댓글 작성', $body);
    }
}
