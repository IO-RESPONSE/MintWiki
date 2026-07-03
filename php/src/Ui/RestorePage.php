<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 복구 경고 page의 서버 렌더링 (태스크 0599).
 *
 * 관리자가 백업에서 데이터를 복구할 때 나타나는 page이다.
 * 위험 작업 확인을 통해 사용자의 명시적 동의를 요구한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 * CSRF 토큰은 form에 포함되며, 폼 제출 시 검증된다.
 */
final class RestorePage
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
     * 복구 경고 page를 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     */
    public function render(array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $dangerWarning = $this->dangerConfirmation->render(
            '데이터 복구',
            '이 작업은 현재 데이터베이스의 모든 데이터를 백업에서 로드된 데이터로 덮어쓰게 됩니다. '
            . '복구 후 현재 데이터는 손실됩니다. 이 작업은 되돌릴 수 없습니다.',
            '네, 이 작업을 수행하겠습니다.',
            'confirm_restore'
        );

        $body = '<main>'
            . '<h1>데이터 복구</h1>'
            . $errorSummary
            . '<form method="post" action="/admin/restore" enctype="multipart/form-data">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="backup_file">백업 파일</label>'
            . '<input type="file" id="backup_file" name="backup_file" accept=".json,.sql" required>'
            . $dangerWarning
            . '<button type="submit">복구</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('데이터 복구', $body);
    }
}
