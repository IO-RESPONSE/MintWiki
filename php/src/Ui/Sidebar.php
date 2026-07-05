<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 나무위키풍 사이드바/도구 영역을 렌더링한다 (태스크 0694).
 *
 * "최근 변경", "랜덤 문서", "문서 검색" 등 도구 링크를 노출한다.
 * DocumentActionTabs(0692)와 같은 관례로, 아직 대응하는 route가 없는 링크
 * (랜덤 문서 등)도 항상 링크 자체는 노출한다 — 실제 라우트 연결은 후속
 * 태스크에서 이루어진다(0694 Out of Scope).
 *
 * `<details>`/`<summary>` 네이티브 엘리먼트로 접힘/펼침을 구현해 JS 없이도
 * 동작한다. 데스크톱 폭에서는 sidebar.css가 메뉴를 항상 펼쳐 본문 옆
 * 고정 폭 컬럼으로 보여주고, 모바일 폭에서는 summary를 토글 버튼으로 남겨
 * 상단 도구 메뉴처럼 접었다 펼 수 있게 한다.
 */
final class Sidebar
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 사이드바 HTML을 렌더링한다.
     */
    public function render(): string
    {
        $items = '';
        foreach ($this->links() as $link) {
            $escapedHref = $this->escaper->attribute($link['href']);
            $escapedLabel = $this->escaper->html($link['label']);
            $items .= '<li><a class="site-sidebar__link" href="' . $escapedHref . '">' . $escapedLabel . '</a></li>';
        }

        return '<aside class="site-sidebar" aria-label="도구">'
            . '<details class="site-sidebar__toggle">'
            . '<summary class="site-sidebar__summary">도구</summary>'
            . '<ul class="site-sidebar__menu">' . $items . '</ul>'
            . '</details>'
            . '</aside>';
    }

    /**
     * @return array<int, array{label: string, href: string}>
     */
    private function links(): array
    {
        return [
            ['label' => '최근 변경', 'href' => '/recent-changes'],
            ['label' => '랜덤 문서', 'href' => '/random'],
            ['label' => '문서 검색', 'href' => '/search'],
        ];
    }
}
