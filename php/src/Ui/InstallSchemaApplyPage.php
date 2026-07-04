<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Security\CsrfTokenService;

/**
 * 설치 스키마 적용 진행 page의 서버 렌더링 (태스크 0680).
 *
 * `db/schema`의 SQL을 실제로 적용하기 전에 확인을 받는 화면이다. 버튼을 누르면
 * `POST /install/schema`로 제출되어 `SchemaApply`가 위키 테이블을 생성한다.
 * 적용이 실패하면 이 화면에 오류 메시지와 함께 다시 표시되고 다음 단계로
 * 넘어가지 않는다. 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class InstallSchemaApplyPage
{
    private Escaper $escaper;
    private Layout $layout;
    private CsrfTokenService $csrfTokenService;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?CsrfTokenService $csrfTokenService = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->csrfTokenService = $csrfTokenService ?? new CsrfTokenService();
    }

    /**
     * 스키마 적용 진행 page를 렌더링한다.
     *
     * @param string|null $error 직전 적용 시도가 실패했을 때의 오류 메시지.
     */
    public function render(?string $error = null): string
    {
        $csrfToken = $this->csrfTokenService->generate();
        $csrfTokenEscaped = $this->escaper->html($csrfToken);

        $errorHtml = '';
        if ($error !== null) {
            $errorHtml = '<div role="alert" aria-label="오류 요약">'
                . '<strong>스키마 적용에 실패했습니다</strong>'
                . '<p>' . $this->escaper->html($error) . '</p>'
                . '</div>';
        }

        $body = '<main>'
            . '<h1>데이터베이스 스키마 적용</h1>'
            . '<p>저장된 데이터베이스 접속 정보로 위키 테이블을 생성합니다.</p>'
            . $errorHtml
            . '<form method="post" action="/install/schema">'
            . '<input type="hidden" name="csrf_token" value="' . $csrfTokenEscaped . '">'
            . '<button type="submit">스키마 적용</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('데이터베이스 스키마 적용', $body);
    }
}
