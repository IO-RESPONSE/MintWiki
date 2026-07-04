<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\User\User;

/**
 * 나무위키풍 상단 네비게이션 바를 렌더링한다 (태스크 0690).
 *
 * `Navigation`/`NavigationItem`은 데이터만 보유하므로, 이 컴포넌트가 실제
 * `<nav>` HTML로 변환한다. 좌측 브랜드 로고(홈 링크), 검색 입력, `Navigation`
 * 항목 목록(현재 경로/권한에 따른 활성화·필터링은 `Navigation` API를 그대로
 * 사용), 우측 로그인 상태 링크로 구성된다. 모든 출력은 `Escaper`로
 * escaping되어 XSS를 방지한다. Layout으로의 실제 삽입은 0691에서 이루어진다.
 */
final class NavigationBar
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 상단 네비게이션 바 HTML을 렌더링한다.
     *
     * @param Navigation $navigation navigation 항목 컬렉션
     * @param string $currentPath 현재 페이지의 경로 (활성 항목 판단용)
     * @param string[] $allowedPermissions 사용자가 가진 권한 배열
     * @param User|null $currentUser 로그인한 사용자, 비로그인이면 null
     */
    public function render(
        Navigation $navigation,
        string $currentPath,
        array $allowedPermissions = [],
        ?User $currentUser = null
    ): string {
        $brand = '<a class="site-nav__brand" href="/">MintWiki</a>';

        $search = '<form class="site-nav__search" action="/search" method="get" role="search">'
            . '<label for="site-nav-search-input" class="sr-only">문서 검색</label>'
            . '<input type="search" id="site-nav-search-input" name="q" placeholder="검색어를 입력하세요">'
            . '<button type="submit">검색</button>'
            . '</form>';

        $menu = $this->renderMenu($navigation, $currentPath, $allowedPermissions);
        $auth = $this->renderAuth($currentUser);

        return '<nav class="site-nav" aria-label="주요 내비게이션">'
            . $brand
            . $search
            . $menu
            . $auth
            . '</nav>';
    }

    /**
     * @param string[] $allowedPermissions
     */
    private function renderMenu(Navigation $navigation, string $currentPath, array $allowedPermissions): string
    {
        $items = $navigation->filterByPermissions($allowedPermissions);

        if ($items === []) {
            return '';
        }

        $listItems = '';
        foreach ($items as $item) {
            $escapedHref = $this->escaper->attribute($item->href());
            $escapedLabel = $this->escaper->html($item->label());
            $isActive = $item->isActive($currentPath);

            $linkClass = 'site-nav__link';
            $ariaCurrent = '';
            if ($isActive) {
                $linkClass .= ' site-nav__link--active';
                $ariaCurrent = ' aria-current="page"';
            }

            $listItems .= '<li><a class="' . $linkClass . '" href="' . $escapedHref . '"' . $ariaCurrent . '>'
                . $escapedLabel
                . '</a></li>';
        }

        return '<ul class="site-nav__menu">' . $listItems . '</ul>';
    }

    private function renderAuth(?User $currentUser): string
    {
        if ($currentUser === null) {
            return '<div class="site-nav__auth"><a class="site-nav__auth-link" href="/login">로그인</a></div>';
        }

        $escapedUsername = $this->escaper->html($currentUser->username());

        return '<div class="site-nav__auth">'
            . '<a class="site-nav__auth-link" href="/logout">로그아웃(' . $escapedUsername . ')</a>'
            . '</div>';
    }
}
