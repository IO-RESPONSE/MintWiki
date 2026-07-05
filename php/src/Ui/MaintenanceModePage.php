<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 유지보수 모드 page의 서버 렌더링 (태스크 0589).
 *
 * 마이그레이션 중이거나 유지보수 작업이 진행 중일 때 표시되는 안내 page이다.
 * 시스템이 일시적으로 이용 불가능함을 사용자에게 알린다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class MaintenanceModePage
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
    )
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
        $this->formErrorSummary = $formErrorSummary ?? new FormErrorSummary($this->escaper);
    }

    /**
     * 유지보수 모드 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>유지보수 중</h1>'
            . '<p>시스템이 마이그레이션 중입니다.</p>'
            . '<p>잠시 후 다시 시도해주세요.</p>'
            . '</main>';

        return $this->layout->render('유지보수 중', $body);
    }

    /**
     * 관리자 유지보수 모드 토글 page를 렌더링한다 (태스크 0700).
     *
     * @param array<string, string|array<string>> $errors
     */
    public function renderAdmin(bool $enabled, array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $escapedCsrfToken = $this->escaper->html($csrfToken);
        $checked = $enabled ? ' checked' : '';
        $status = $enabled ? '켜짐' : '꺼짐';

        $body = '<main>'
            . '<h1>유지보수 모드</h1>'
            . $this->formErrorSummary->render($errors)
            . '<p>현재 상태: <strong>' . $this->escaper->html($status) . '</strong></p>'
            . '<form method="post" action="/admin/maintenance">'
            . '<input type="hidden" name="csrf_token" value="' . $escapedCsrfToken . '">'
            . '<label><input type="checkbox" name="enabled" value="1"' . $checked . '> 유지보수 모드 사용</label>'
            . '<button type="submit">저장</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('유지보수 모드', $body);
    }
}
