<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;

/**
 * 문서 편집 page의 서버 렌더링 (태스크 0532).
 *
 * 기존 문서를 편집하는 form을 표시한다. title과 source 입력 필드에
 * 기존 값이 채워져 있다. 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class DocumentEditPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 편집 form을 렌더링한다.
     *
     * @param Document $document 편집할 문서
     * @param string|null $source 문서의 현재 source 내용
     */
    public function render(Document $document, ?string $source = null): string
    {
        $title = $this->escaper->html($document->title());
        $sourceContent = $this->escaper->html($source ?? '');
        $id = $this->escaper->html($document->id());

        $body = '<main>'
            . '<h1>문서 편집</h1>'
            . '<form method="post" action="/documents/' . $id . '">'
            . '<label for="title">제목</label>'
            . '<input type="text" id="title" name="title" value="' . $title . '" required>'
            . '<label for="source">내용</label>'
            . '<textarea id="source" name="source" required>' . $sourceContent . '</textarea>'
            . '<button type="submit">저장</button>'
            . '</form>'
            . '</main>';

        return $this->layout->render('문서 편집', $body);
    }
}
