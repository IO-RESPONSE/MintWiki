<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;

/**
 * 문서 히스토리 page의 서버 렌더링 (태스크 0534).
 *
 * 특정 문서의 모든 리비전 목록을 시간순으로 표시한다.
 * 모든 사용자 입력(문서 title, 작성자 id 등)은 escaping되어 XSS를 방지한다.
 */
final class DocumentHistoryPage
{
    private Escaper $escaper;
    private Layout $layout;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
    }

    /**
     * 문서 히스토리 page를 렌더링한다.
     *
     * @param Document $document 조회한 문서
     * @param Revision[] $revisions 문서의 리비전 목록
     */
    public function render(Document $document, array $revisions = []): string
    {
        $title = $this->escaper->html($document->title());
        $id = $this->escaper->html($document->id());

        $revisionList = $this->renderRevisionList($revisions);

        $body = '<main>'
            . '<h1>' . $title . ' - 히스토리</h1>'
            . '<p>문서 리비전 목록</p>'
            . $revisionList
            . '</main>';

        return $this->layout->render('문서 히스토리', $body);
    }

    /**
     * 리비전 목록을 렌더링한다.
     *
     * @param Revision[] $revisions 리비전 배열
     */
    private function renderRevisionList(array $revisions): string
    {
        if (empty($revisions)) {
            return '<p>리비전이 없습니다.</p>';
        }

        $html = '<ul>';
        foreach ($revisions as $revision) {
            $html .= $this->renderRevisionItem($revision);
        }
        $html .= '</ul>';

        return $html;
    }

    /**
     * 단일 리비전 항목을 렌더링한다.
     */
    private function renderRevisionItem(Revision $revision): string
    {
        $revisionId = $this->escaper->html($revision->id());
        $authorId = $this->escaper->html($revision->authorId());
        $summary = $this->escaper->html($revision->summary());

        return '<li>'
            . 'ID: ' . $revisionId
            . ' | 작성자: ' . $authorId
            . ' | 요약: ' . $summary
            . '</li>';
    }
}
