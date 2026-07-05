<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;

/**
 * 나무위키풍 대문(프론트페이지) 서버 렌더링 (태스크 0693).
 *
 * 기존에는 `GET /`가 검색 폼만 담은 인라인 HTML 문자열을 반환했다. 이
 * 컴포넌트는 그 자리를 대체해 (1) 눈에 띄는 검색 영역, (2) 최근 편집된
 * 문서 목록(있으면), (3) 사이트 소개 안내 블록을 나무위키풍으로 배치한다.
 * `Layout`(0691 스킨의 상단바/푸터)을 그대로 재사용한다.
 *
 * 최근 문서 목록은 DB 미설정/오류/비어있음 어느 경우에도 `EmptyState`로
 * 안전하게 안내하며, 조회 실패로 이 컴포넌트 자체가 죽지 않는다 — 호출자
 * (`public/index.php`)가 조회를 시도하고 실패하면 빈 배열을 넘기는 것으로
 * 충분하다.
 */
final class FrontPage
{
    private Escaper $escaper;
    private Layout $layout;
    private EmptyState $emptyState;

    public function __construct(?Escaper $escaper = null, ?Layout $layout = null, ?EmptyState $emptyState = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->emptyState = $emptyState ?? new EmptyState($this->escaper);
    }

    /**
     * 대문을 렌더링한다.
     *
     * @param Document[] $recentDocuments 최근 편집된 문서 목록(최신순), 없으면 빈 배열
     */
    public function render(array $recentDocuments = []): string
    {
        $body = '<main class="front-page">'
            . $this->renderSearchSection()
            . $this->renderRecentDocumentsSection($recentDocuments)
            . $this->renderAboutSection()
            . '</main>';

        return $this->layout->render('MintWiki', $body);
    }

    /**
     * 눈에 띄는 검색 영역을 렌더링한다.
     */
    private function renderSearchSection(): string
    {
        return '<section class="front-page__search" aria-label="문서 검색">'
            . '<h1 class="front-page__title">MintWiki</h1>'
            . '<form method="get" action="/api/documents/by-title" class="front-page__search-form">'
            . '<input type="text" name="q" placeholder="검색어를 입력하세요" required class="front-page__search-input">'
            . '<button type="submit" class="front-page__search-button">검색</button>'
            . '</form>'
            . '</section>';
    }

    /**
     * 최근 편집된 문서 목록 영역을 렌더링한다. 목록이 비어있으면
     * `EmptyState`로 안내한다.
     *
     * @param Document[] $recentDocuments
     */
    private function renderRecentDocumentsSection(array $recentDocuments): string
    {
        $content = $recentDocuments === []
            ? $this->emptyState->render('아직 편집된 문서가 없습니다.', '문서를 만들어 대문을 채워보세요.')
            : $this->renderRecentDocumentsList($recentDocuments);

        return '<section class="front-page__recent" aria-label="최근 편집된 문서">'
            . '<h2 class="front-page__section-title">최근 편집된 문서</h2>'
            . $content
            . '</section>';
    }

    /**
     * @param Document[] $recentDocuments
     */
    private function renderRecentDocumentsList(array $recentDocuments): string
    {
        $items = '';
        foreach ($recentDocuments as $document) {
            $escapedTitle = $this->escaper->html($document->title());
            $href = '/wiki/' . rawurlencode($document->title());
            $escapedHref = $this->escaper->attribute($href);

            $items .= '<li class="front-page__recent-item">'
                . '<a href="' . $escapedHref . '">' . $escapedTitle . '</a>'
                . '</li>';
        }

        return '<ul class="front-page__recent-list">' . $items . '</ul>';
    }

    /**
     * 사이트 소개/안내 블록을 렌더링한다.
     */
    private function renderAboutSection(): string
    {
        return '<section class="front-page__about" aria-label="사이트 소개">'
            . '<h2 class="front-page__section-title">MintWiki 소개</h2>'
            . '<p>MintWiki는 누구나 문서를 만들고 편집할 수 있는 위키입니다. '
            . '검색으로 원하는 문서를 찾아보거나, 없는 문서라면 직접 만들어보세요.</p>'
            . '</section>';
    }
}
