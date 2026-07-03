<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 검색 결과 컴포넌트 (태스크 0571).
 *
 * 검색 결과 목록을 렌더링한다. 각 결과는 제목과 snippet으로 구성된다.
 * 모든 텍스트와 URL은 XSS 방지를 위해 escaping된다.
 */
final class SearchResult
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 검색 결과 항목을 렌더링한다.
     *
     * @param string $title 문서 제목 (필수)
     * @param string $url 문서 링크 URL (필수)
     * @param string|null $snippet 문서 내용의 발췌(snippet) (선택사항)
     * @return string 검색 결과 항목 HTML
     */
    public function render(string $title, string $url, ?string $snippet = null): string
    {
        if (empty($title) || empty($url)) {
            return '';
        }

        $html = '<div class="search-result">';

        // 제목 링크
        $escapedTitle = $this->escaper->html($title);
        $escapedUrl = $this->escaper->attribute($url);
        $html .= '<h3 class="search-result__title">'
            . '<a href="' . $escapedUrl . '">' . $escapedTitle . '</a>'
            . '</h3>';

        // Snippet
        if ($snippet !== null && !empty($snippet)) {
            $escapedSnippet = $this->escaper->html($snippet);
            $html .= '<p class="search-result__snippet">' . $escapedSnippet . '</p>';
        }

        $html .= '</div>';

        return $html;
    }

    /**
     * 검색 결과 목록을 렌더링한다.
     *
     * @param array<array{title: string, url: string, snippet?: string}> $results 검색 결과 배열
     * @return string 검색 결과 목록 HTML
     */
    public function renderList(array $results): string
    {
        if (empty($results)) {
            return '';
        }

        $html = '<div class="search-results">';

        foreach ($results as $result) {
            if (!isset($result['title']) || !isset($result['url'])) {
                continue;
            }

            $title = (string) $result['title'];
            $url = (string) $result['url'];
            $snippet = isset($result['snippet']) ? (string) $result['snippet'] : null;

            $html .= $this->render($title, $url, $snippet);
        }

        $html .= '</div>';

        return $html;
    }
}
