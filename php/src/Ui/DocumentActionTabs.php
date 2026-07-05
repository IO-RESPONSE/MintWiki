<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 나무위키풍 문서 액션 탭(읽기/편집/역사/토론/삭제)을 렌더링한다 (태스크 0692, 삭제
 * 탭은 0715).
 *
 * 읽기/편집/역사/토론 네 탭은 `/wiki/{title}` 계열 경로로 링크하며, 역사/토론
 * 탭은 대응하는 route가 없던 시절(0692 Out of Scope)에도 나무위키 관례대로
 * 항상 노출했다 — 이후 라우트가 연결되면 자연스럽게 동작한다. 삭제 탭은 그와
 * 달리 항상 노출하지 않는다 — 되돌릴 수 없는 위험 작업이라 `$canDelete`가
 * true인 경우(로그인 + delete 권한 보유, 호출자가 ACL 검사 결과로 판단)에만
 * `/wiki/{title}/delete`로 링크를 추가한다.
 * 활성 탭은 `NavigationItem::isActive()`와 동일하게 currentPath와 탭의 href가
 * 정확히 일치할 때로 판단한다. 모든 출력은 `Escaper`로 escaping되어 XSS를
 * 방지한다.
 */
final class DocumentActionTabs
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 문서 액션 탭 목록 HTML을 렌더링한다.
     *
     * @param string $title 탭 링크를 구성할 문서 제목 (URL 인코딩은 내부에서 처리)
     * @param string $currentPath 현재 페이지의 경로 (활성 탭 판단용)
     * @param bool $canDelete 삭제 탭 노출 여부 (태스크 0715, 기본값 false: 숨김)
     */
    public function render(string $title, string $currentPath = '', bool $canDelete = false): string
    {
        $items = '';
        foreach ($this->tabs($title, $canDelete) as $tab) {
            $isActive = $currentPath !== '' && $tab['href'] === $currentPath;
            $escapedHref = $this->escaper->attribute($tab['href']);
            $escapedLabel = $this->escaper->html($tab['label']);

            $linkClass = 'document-tabs__link';
            $ariaCurrent = '';
            if ($isActive) {
                $linkClass .= ' document-tabs__link--active';
                $ariaCurrent = ' aria-current="page"';
            }

            $items .= '<li><a class="' . $linkClass . '" href="' . $escapedHref . '"' . $ariaCurrent . '>'
                . $escapedLabel
                . '</a></li>';
        }

        return '<ul class="document-tabs">' . $items . '</ul>';
    }

    /**
     * @return array<int, array{label: string, href: string}>
     */
    private function tabs(string $title, bool $canDelete): array
    {
        $encodedTitle = rawurlencode($title);

        $tabs = [
            ['label' => '읽기', 'href' => '/wiki/' . $encodedTitle],
            ['label' => '편집', 'href' => '/wiki/' . $encodedTitle . '/edit'],
            ['label' => '역사', 'href' => '/wiki/' . $encodedTitle . '/history'],
            ['label' => '토론', 'href' => '/wiki/' . $encodedTitle . '/discussion'],
        ];

        if ($canDelete) {
            $tabs[] = ['label' => '삭제', 'href' => '/wiki/' . $encodedTitle . '/delete'];
        }

        return $tabs;
    }
}
