<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;

/**
 * 단일 문서 view page의 서버 렌더링 (태스크 0529).
 *
 * 존재하는 문서를 표시하거나, 없는 경우 "문서를 찾을 수 없음" 메시지를 보여준다.
 * 모든 사용자 입력(문서 title 등)은 escaping되어 XSS를 방지한다.
 */
final class DocumentViewPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 view page를 렌더링한다.
     *
     * @param Document|null $document 조회한 문서, 없으면 null
     */
    public function render(?Document $document): string
    {
        if ($document === null) {
            return $this->renderNotFound();
        }

        return $this->renderDocument($document);
    }

    /**
     * 존재하는 문서를 렌더링한다.
     */
    private function renderDocument(Document $document): string
    {
        $title = $this->escaper->html($document->title());

        $body = '<main>'
            . '<h1>' . $title . '</h1>'
            . '<p>문서 내용이 여기에 표시됩니다.</p>'
            . '</main>';

        return $this->layout->render($document->title(), $body);
    }

    /**
     * 문서를 찾을 수 없을 때의 page를 렌더링한다.
     */
    private function renderNotFound(): string
    {
        $body = '<main>'
            . '<h1>문서를 찾을 수 없습니다</h1>'
            . '<p>요청하신 문서가 존재하지 않습니다.</p>'
            . '</main>';

        return $this->layout->render('문서를 찾을 수 없습니다', $body);
    }
}
