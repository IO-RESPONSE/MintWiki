<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 문서 삭제 확인 page의 서버 렌더링 (태스크 0715).
 *
 * `POST /wiki/{title}/delete`로 문서를 삭제하기 전에 사용자의 명시적 동의를
 * 요구하는 화면이다. 되돌릴 수 없는 위험 작업이므로 `RestorePage`(태스크 0599)와
 * 동일하게 `AdminDangerConfirmation`(체크박스)을 재사용한다. 모든 사용자 입력은
 * escaping되어 XSS를 방지하며, CSRF 토큰은 form에 포함되어 제출 시 검증된다.
 */
final class DocumentDeletePage
{
    private Escaper $escaper;
    private Layout $layout;
    private CsrfTokenService $csrfTokenService;
    private FormErrorSummary $formErrorSummary;
    private AdminDangerConfirmation $dangerConfirmation;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?CsrfTokenService $csrfTokenService = null,
        ?FormErrorSummary $formErrorSummary = null,
        ?AdminDangerConfirmation $dangerConfirmation = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formErrorSummary = $formErrorSummary ?? new FormErrorSummary();
        $this->dangerConfirmation = $dangerConfirmation ?? new AdminDangerConfirmation();
    }

    /**
     * 문서 삭제 확인 page를 렌더링한다.
     *
     * @param string $title 삭제 대상 문서의 제목
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     */
    public function render(string $title, array $errors = []): string
    {
        $escapedTitle = $this->escaper->html($title);
        $encodedTitle = rawurlencode($title);
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $dangerWarning = $this->dangerConfirmation->render(
            '문서 삭제',
            '이 문서와 관련된 모든 리비전, 토론 스레드/댓글이 함께 삭제됩니다. 이 작업은 되돌릴 수 없습니다.',
            '네, 이 문서를 삭제하겠습니다.',
            'confirm_delete'
        );

        $body = '<main>'
            . '<h1>문서 삭제: ' . $escapedTitle . '</h1>'
            . $errorSummary
            . '<form method="post" action="/wiki/' . $encodedTitle . '/delete">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . $dangerWarning
            . '<button type="submit">삭제</button>'
            . ' <a href="/wiki/' . $encodedTitle . '">취소</a>'
            . '</form>'
            . '</main>';

        return $this->layout->render('문서 삭제: ' . $title, $body);
    }
}
