<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 검색 page의 서버 렌더링 (태스크 0536).
 *
 * 검색 adapter가 연결되지 않은 상태를 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class SearchPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 검색 page를 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>검색</h1>'
            . '<p>검색 adapter가 연결되지 않았습니다.</p>'
            . '</main>';

        return $this->layout->render('검색', $body);
    }
}
