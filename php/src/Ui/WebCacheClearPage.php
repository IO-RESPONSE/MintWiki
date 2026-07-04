<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 웹 캐시 초기화 page의 서버 렌더링 (태스크 0648).
 *
 * 공유 호스팅 환경에서 CLI 접근이 어려운 관리자를 위한 web cache clear placeholder이다.
 * 실제 캐시 삭제 동작은 후속 작업에서 연결한다.
 */
final class WebCacheClearPage
{
    public const REQUIRED_PERMISSION = 'admin:read';

    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 웹 캐시 초기화 placeholder page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>웹 캐시 초기화</h1>'
            . '<section aria-label="웹 캐시 초기화 상태">'
            . '<h2>상태</h2>'
            . '<p>관리자 전용 웹 캐시 초기화 기능을 준비 중입니다.</p>'
            . '<p>placeholder</p>'
            . '</section>'
            . '<p><a href="/admin/status">운영 진단으로 돌아가기</a></p>'
            . '</main>';

        return $this->layout->render('웹 캐시 초기화', $body);
    }
}
