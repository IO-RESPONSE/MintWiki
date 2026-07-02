<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 새 문서 생성 page의 서버 렌더링 (태스크 0530).
 *
 * title과 source 입력 필드를 가진 form을 표시한다.
 * 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class DocumentCreatePage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 생성 form을 렌더링한다.
     */
    public function render(): string
    {
        $body = '<main>'
            . '<h1>새 문서 만들기</h1>'
            . '<form method="post" action="/documents">'
            . '<label for="title">제목</label>'
            . '<input type="text" id="title" name="title" required>'
            . '<label for="source">내용</label>'
            . '<textarea id="source" name="source" required></textarea>'
            . '<button type="submit">저장</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('새 문서 만들기', $body);
    }
}
