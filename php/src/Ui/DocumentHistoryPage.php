<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Revision\Revision;

/**
 * 문서 히스토리 page의 서버 렌더링 (태스크 0534, 라우트 연결은 0710).
 *
 * 특정 문서의 모든 리비전 목록을 시간 내림차순(최신순)으로 표시한다.
 * 각 행에는 작성자·생성 시각·편집 요약(0707)과, 직전 리비전 대비 변경사항을
 * 보는 "보기" 링크(`/wiki/{title}/diff`)를 함께 보여준다. 리비전이 둘 이상일
 * 때만 라디오 버튼(from/to)과 "선택한 리비전 비교" 제출 버튼을 추가해 임의의
 * 두 리비전을 비교하는 diff 요청을 만들 수 있게 한다 — 최신 리비전이 기본
 * "이후(to)", 그 바로 이전 리비전이 기본 "이전(from)"으로 선택되어 있어 그대로
 * 제출해도 바로 직전 변경사항을 볼 수 있다. 모든 사용자 입력(문서 title,
 * 작성자 id 등)은 escaping되어 XSS를 방지한다.
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
     * @param Revision[] $revisions 문서의 리비전 목록 (시간 내림차순으로 정렬되어 있다고 가정)
     */
    public function render(Document $document, array $revisions = []): string
    {
        $title = $this->escaper->html($document->title());
        $encodedTitle = rawurlencode($document->title());

        $revisionList = $this->renderRevisionList($revisions, $encodedTitle);

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
    private function renderRevisionList(array $revisions, string $encodedTitle): string
    {
        if ($revisions === []) {
            return '<p>리비전이 없습니다.</p>';
        }

        $canCompare = count($revisions) > 1;

        $html = $canCompare
            ? '<form method="get" action="/wiki/' . $encodedTitle . '/diff">'
            : '';
        $html .= '<ul>';
        foreach ($revisions as $index => $revision) {
            $html .= $this->renderRevisionItem($revision, $index, $encodedTitle, $canCompare);
        }
        $html .= '</ul>';
        if ($canCompare) {
            $html .= '<button type="submit">선택한 리비전 비교</button></form>';
        }

        return $html;
    }

    /**
     * 단일 리비전 항목을 렌더링한다.
     */
    private function renderRevisionItem(Revision $revision, int $index, string $encodedTitle, bool $canCompare): string
    {
        $revisionId = $this->escaper->html($revision->id());
        $revisionIdAttr = $this->escaper->attribute($revision->id());
        $authorId = $this->escaper->html($revision->authorId());
        $summary = $this->escaper->html($revision->summary());
        $createdAt = $revision->createdAt();
        $createdAtHtml = $createdAt !== null ? $this->escaper->html($createdAt) : '-';

        if ($revision->parentRevisionId() !== null) {
            $diffHref = $this->escaper->attribute(
                '/wiki/' . $encodedTitle . '/diff?from=' . rawurlencode($revision->parentRevisionId())
                . '&to=' . rawurlencode($revision->id())
            );
            $viewLink = ' | <a href="' . $diffHref . '">보기</a>';
        } else {
            $viewLink = ' | 최초 버전';
        }

        $compareInputs = '';
        if ($canCompare) {
            $fromChecked = $index === 1 ? ' checked' : '';
            $toChecked = $index === 0 ? ' checked' : '';
            $compareInputs = ' <label>이전 <input type="radio" name="from" value="' . $revisionIdAttr . '"' . $fromChecked . '></label>'
                . ' <label>이후 <input type="radio" name="to" value="' . $revisionIdAttr . '"' . $toChecked . '></label>';
        }

        return '<li>'
            . 'ID: ' . $revisionId
            . ' | 작성자: ' . $authorId
            . ' | 시각: ' . $createdAtHtml
            . ' | 요약: ' . $summary
            . $viewLink
            . $compareInputs
            . '</li>';
    }
}
