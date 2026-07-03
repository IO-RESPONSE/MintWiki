<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 페이지네이션 컴포넌트 (태스크 0552).
 *
 * 페이지 번호 링크와 이전/다음 네비게이션을 렌더링한다.
 * 쿼리 매개변수를 보존하여 페이지 링크에 포함한다.
 * 모든 URL과 텍스트는 XSS 방지를 위해 escaping된다.
 */
final class Pagination
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 페이지네이션을 렌더링한다.
     *
     * @param string $basePath 페이지네이션 링크의 기본 경로 (예: "/documents")
     * @param int $currentPage 현재 페이지 번호 (1부터 시작)
     * @param int $totalPages 전체 페이지 수
     * @param array<string, string> $queryParams 보존할 쿼리 매개변수 배열
     * @param int $maxLinks 표시할 최대 페이지 링크 수 (기본값: 5)
     * @return string 페이지네이션 HTML
     */
    public function render(
        string $basePath,
        int $currentPage,
        int $totalPages,
        array $queryParams = [],
        int $maxLinks = 5
    ): string {
        if ($totalPages <= 1) {
            return '';
        }

        if ($currentPage < 1 || $currentPage > $totalPages) {
            return '';
        }

        $html = '<nav class="pagination" aria-label="페이지 네비게이션">';
        $html .= '<ul class="pagination__list">';

        // 이전 페이지 링크
        if ($currentPage > 1) {
            $html .= $this->renderPrevLink($basePath, $currentPage - 1, $queryParams);
        } else {
            $html .= '<li class="pagination__item pagination__item--disabled">'
                . '<span class="pagination__link" aria-disabled="true">이전</span>'
                . '</li>';
        }

        // 페이지 번호 링크
        $startPage = max(1, $currentPage - (int)($maxLinks / 2));
        $endPage = min($totalPages, $startPage + $maxLinks - 1);

        if ($endPage - $startPage + 1 < $maxLinks) {
            $startPage = max(1, $endPage - $maxLinks + 1);
        }

        // 첫 페이지로의 간격 표시
        if ($startPage > 1) {
            $html .= $this->renderPageLink($basePath, 1, $queryParams);
            if ($startPage > 2) {
                $html .= '<li class="pagination__item pagination__item--spacer">'
                    . '<span class="pagination__link">…</span>'
                    . '</li>';
            }
        }

        // 페이지 번호 링크들
        for ($page = $startPage; $page <= $endPage; $page++) {
            if ($page === $currentPage) {
                $html .= '<li class="pagination__item pagination__item--current">'
                    . '<span class="pagination__link" aria-current="page">' . $page . '</span>'
                    . '</li>';
            } else {
                $html .= $this->renderPageLink($basePath, $page, $queryParams);
            }
        }

        // 마지막 페이지로의 간격 표시
        if ($endPage < $totalPages) {
            if ($endPage < $totalPages - 1) {
                $html .= '<li class="pagination__item pagination__item--spacer">'
                    . '<span class="pagination__link">…</span>'
                    . '</li>';
            }
            $html .= $this->renderPageLink($basePath, $totalPages, $queryParams);
        }

        // 다음 페이지 링크
        if ($currentPage < $totalPages) {
            $html .= $this->renderNextLink($basePath, $currentPage + 1, $queryParams);
        } else {
            $html .= '<li class="pagination__item pagination__item--disabled">'
                . '<span class="pagination__link" aria-disabled="true">다음</span>'
                . '</li>';
        }

        $html .= '</ul>';
        $html .= '</nav>';

        return $html;
    }

    /**
     * 페이지 번호 링크를 렌더링한다.
     *
     * @param string $basePath 기본 경로
     * @param int $page 페이지 번호
     * @param array<string, string> $queryParams 쿼리 매개변수
     */
    private function renderPageLink(
        string $basePath,
        int $page,
        array $queryParams
    ): string {
        $url = $this->buildUrl($basePath, $page, $queryParams);
        $escapedUrl = $this->escaper->attribute($url);
        $escapedLabel = $this->escaper->html((string)$page);

        return '<li class="pagination__item">'
            . '<a href="' . $escapedUrl . '" class="pagination__link">' . $escapedLabel . '</a>'
            . '</li>';
    }

    /**
     * 이전 페이지 링크를 렌더링한다.
     *
     * @param string $basePath 기본 경로
     * @param int $page 이전 페이지 번호
     * @param array<string, string> $queryParams 쿼리 매개변수
     */
    private function renderPrevLink(
        string $basePath,
        int $page,
        array $queryParams
    ): string {
        $url = $this->buildUrl($basePath, $page, $queryParams);
        $escapedUrl = $this->escaper->attribute($url);

        return '<li class="pagination__item pagination__item--prev">'
            . '<a href="' . $escapedUrl . '" class="pagination__link">이전</a>'
            . '</li>';
    }

    /**
     * 다음 페이지 링크를 렌더링한다.
     *
     * @param string $basePath 기본 경로
     * @param int $page 다음 페이지 번호
     * @param array<string, string> $queryParams 쿼리 매개변수
     */
    private function renderNextLink(
        string $basePath,
        int $page,
        array $queryParams
    ): string {
        $url = $this->buildUrl($basePath, $page, $queryParams);
        $escapedUrl = $this->escaper->attribute($url);

        return '<li class="pagination__item pagination__item--next">'
            . '<a href="' . $escapedUrl . '" class="pagination__link">다음</a>'
            . '</li>';
    }

    /**
     * 페이지 URL을 구성한다.
     *
     * @param string $basePath 기본 경로
     * @param int $page 페이지 번호
     * @param array<string, string> $queryParams 기존 쿼리 매개변수
     */
    private function buildUrl(
        string $basePath,
        int $page,
        array $queryParams
    ): string {
        $params = $queryParams;
        $params['page'] = (string)$page;

        $queryString = http_build_query($params, '', '&', PHP_QUERY_RFC3986);

        if ($queryString === '') {
            return $basePath;
        }

        return $basePath . '?' . $queryString;
    }
}
