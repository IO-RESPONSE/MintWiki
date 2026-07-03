<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 설치 DB form page의 서버 렌더링 (태스크 0621).
 *
 * 설치 프로세스에서 MariaDB 데이터베이스 설정을 받는 form을 표시한다.
 * 사용자는 DSN(호스트명:포트), 사용자명, 비밀번호를 입력한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 * CSRF 토큰은 form에 포함되며, 폼 제출 시 검증된다.
 */
final class InstallDBFormPage
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
     * 데이터베이스 설정 form을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 폼 검증 오류 (선택사항)
     */
    public function render(array $errors = []): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);
        $errorSummary = $this->formErrorSummary->render($errors);

        $body = '<main>'
            . '<h1>데이터베이스 설정</h1>'
            . '<p>MariaDB 데이터베이스 연결 정보를 입력하세요.</p>'
            . $errorSummary
            . '<form method="post" action="/install/db">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<label for="dsn">호스트명:포트</label>'
            . '<input type="text" id="dsn" name="dsn" placeholder="localhost:3306" required>'
            . '<label for="username">사용자명</label>'
            . '<input type="text" id="username" name="username" placeholder="root" required>'
            . '<label for="password">비밀번호</label>'
            . '<input type="password" id="password" name="password" required>'
            . '<button type="submit">데이터베이스 연결</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('데이터베이스 설정', $body);
    }
}
