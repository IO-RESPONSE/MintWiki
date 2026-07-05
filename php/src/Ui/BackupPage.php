<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 백업 page의 서버 렌더링 (태스크 0598).
 *
 * 시스템 백업 및 복구 기능을 관리하는 page이다.
 * shared hosting 환경에서의 안정적인 백업 운영을 고려한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class BackupPage
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
     * 백업 page를 렌더링한다.
     */
    /**
     * @param string[] $backups
     * @param array<string, string|array<string>> $errors
     */
    public function render(array $backups = [], ?string $message = null, array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $escapedCsrfToken = $this->escaper->html($csrfToken);
        $backupItems = '';
        foreach ($backups as $backup) {
            $backupItems .= '<li>' . $this->escaper->html($backup) . '</li>';
        }
        $backupList = $backupItems === ''
            ? '<p>생성된 백업이 없습니다.</p>'
            : '<ul>' . $backupItems . '</ul>';
        $messageHtml = $message !== null
            ? '<p role="status">' . $this->escaper->html($message) . '</p>'
            : '';

        $body = '<main>'
            . '<h1>백업</h1>'
            . '<p>백업 및 복구 기능을 준비 중입니다.</p>'
            . $this->formErrorSummary->render($errors)
            . $messageHtml
            . '<form method="post" action="/admin/backup">'
            . '<input type="hidden" name="csrf_token" value="' . $escapedCsrfToken . '">'
            . '<button type="submit">백업 생성</button>'
            . '</form>'
            . '<section aria-label="백업 목록">'
            . '<h2>백업 목록</h2>'
            . $backupList
            . '</section>'
            . '</main>';

        return $this->layout->render('백업', $body);
    }
}
