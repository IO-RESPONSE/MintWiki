<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 빈 상태 컴포넌트 (태스크 0553).
 *
 * 데이터가 없거나 콘텐츠가 없는 상태를 사용자에게 명확하게 전달한다.
 * title/description/action 구조로 구성된다.
 * 모든 텍스트와 URL은 XSS 방지를 위해 escaping된다.
 */
final class EmptyState
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 빈 상태 콘텐츠를 렌더링한다.
     *
     * @param string $title 제목 텍스트 (필수)
     * @param string|null $description 설명 텍스트 (선택사항)
     * @param array<string, string>|null $action 액션 버튼 정보 (선택사항)
     *                                             - 'href': 링크 URL
     *                                             - 'label': 버튼 텍스트
     * @return string 빈 상태 HTML
     */
    public function render(
        string $title,
        ?string $description = null,
        ?array $action = null
    ): string {
        if (empty($title)) {
            return '';
        }

        $html = '<div class="empty-state">';
        $html .= '<div class="empty-state__content">';

        // 제목
        $escapedTitle = $this->escaper->html($title);
        $html .= '<h2 class="empty-state__title">' . $escapedTitle . '</h2>';

        // 설명
        if ($description !== null && !empty($description)) {
            $escapedDescription = $this->escaper->html($description);
            $html .= '<p class="empty-state__description">' . $escapedDescription . '</p>';
        }

        // 액션 버튼
        if ($action !== null && isset($action['href']) && isset($action['label'])) {
            $href = $action['href'];
            $label = $action['label'];

            if (!empty($href) && !empty($label)) {
                $escapedHref = $this->escaper->attribute($href);
                $escapedLabel = $this->escaper->html($label);
                $html .= '<a href="' . $escapedHref . '" class="empty-state__action">'
                    . $escapedLabel
                    . '</a>';
            }
        }

        $html .= '</div>';
        $html .= '</div>';

        return $html;
    }
}
