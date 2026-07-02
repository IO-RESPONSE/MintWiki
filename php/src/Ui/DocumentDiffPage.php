<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;

/**
 * 문서 diff page의 서버 렌더링 (태스크 0535).
 *
 * 두 리비전의 변경사항을 비교하는 placeholder page이다. 실제 diff 렌더링은
 * 후속 작업이다. 모든 사용자 입력은 escaping되어 XSS를 방지한다.
 */
final class DocumentDiffPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 diff page를 렌더링한다.
     *
     * @param Document $document 비교할 문서
     * @param Revision $fromRevision 비교 대상 이전 리비전
     * @param Revision $toRevision 비교 대상 이후 리비전
     */
    public function render(Document $document, Revision $fromRevision, Revision $toRevision): string
    {
        $title = $this->escaper->html($document->title());
        $fromRevisionId = $this->escaper->html($fromRevision->id());
        $toRevisionId = $this->escaper->html($toRevision->id());

        $body = '<main>'
            . '<h1>' . $title . ' - diff</h1>'
            . '<p>리비전 비교</p>'
            . '<p>From: ' . $fromRevisionId . '</p>'
            . '<p>To: ' . $toRevisionId . '</p>'
            . '<p>실제 diff 내용은 후속 작업에서 구현됩니다.</p>'
            . '</main>';

        return $this->layout->render($title . ' - diff', $body);
    }
}
