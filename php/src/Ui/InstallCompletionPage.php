<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 설치 완료 page의 서버 렌더링 (태스크 0625).
 *
 * 설치 프로세스가 끝났음을 알리고, 관리자가 이어서 확인해야 할 보안 조치와
 * 다음 이동 경로를 안내한다.
 */
final class InstallCompletionPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 설치 완료 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>설치 완료</h1>'
            . '<p>MintWiki 설치가 완료되었습니다.</p>'
            . '<p>보안을 위해 설치 도구 접근을 비활성화하고 관리자 계정으로 로그인하세요.</p>'
            . '<section aria-labelledby="next-steps-title">'
            . '<h2 id="next-steps-title">다음 조치</h2>'
            . '<ul>'
            . '<li>설치 파일과 설정 파일 권한을 운영 환경에 맞게 제한하세요.</li>'
            . '<li>관리자 계정으로 로그인한 뒤 사이트 기본 설정을 확인하세요.</li>'
            . '<li>첫 문서를 작성해 설치 상태를 확인하세요.</li>'
            . '</ul>'
            . '</section>'
            . '<p><a href="/login">관리자 로그인</a></p>'
            . '<p><a href="/">사이트로 이동</a></p>'
            . '</main>';

        return $this->layout->render('설치 완료', $body);
    }
}
