<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 나무위키풍 문서 헤더: 제목(H1) + 액션 탭 + "마지막 편집" 메타 정보 (태스크 0692).
 *
 * `DocumentViewPage`가 문서 존재/미존재 두 화면 모두에서 재사용한다. h1은
 * 기존 `DocumentViewPage` 테스트가 기대하는 `<h1>{title}</h1>` 형태를 그대로
 * 유지한다 — class/속성을 h1 태그 자체에 붙이지 않고 바깥 wrapper에만 둔다.
 * 모든 출력은 `Escaper`로 escaping되어 XSS를 방지한다.
 */
final class DocumentHeader
{
    private Escaper $escaper;
    private DocumentActionTabs $actionTabs;

    public function __construct(?Escaper $escaper = null, ?DocumentActionTabs $actionTabs = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->actionTabs = $actionTabs ?? new DocumentActionTabs($this->escaper);
    }

    /**
     * 문서 헤더 HTML을 렌더링한다.
     *
     * @param string $title 문서 제목 (h1 및 탭 링크 구성에 사용)
     * @param string $currentPath 현재 페이지의 경로 (활성 탭 판단용)
     * @param string|null $lastEditedBy 마지막 편집자 정보, 없으면 메타 정보를 생략한다
     */
    public function render(string $title, string $currentPath = '', ?string $lastEditedBy = null): string
    {
        $escapedTitle = $this->escaper->html($title);
        $tabsHtml = $this->actionTabs->render($title, $currentPath);

        $meta = '';
        if ($lastEditedBy !== null && trim($lastEditedBy) !== '') {
            $escapedAuthor = $this->escaper->html($lastEditedBy);
            $meta = '<p class="document-header__meta">마지막 편집: ' . $escapedAuthor . '</p>';
        }

        return '<div class="document-header">'
            . '<h1>' . $escapedTitle . '</h1>'
            . $tabsHtml
            . $meta
            . '</div>';
    }
}
