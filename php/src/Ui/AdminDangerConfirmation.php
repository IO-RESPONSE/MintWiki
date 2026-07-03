<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 관리자 위험 작업 확인 컴포넌트 (태스크 0574).
 *
 * 사용자 차단, 문서 삭제 등 돌이킬 수 없는 관리자 작업 전에
 * 명시적 확인을 요구하는 컴포넌트다. 위험성을 강조하고,
 * 체크박스를 통해 사용자가 의도를 명시해야 한다.
 * 모든 메시지는 XSS 방지를 위해 escaping된다.
 */
final class AdminDangerConfirmation
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 위험 작업 확인 영역을 렌더링한다.
     *
     * @param string $title 위험 작업의 제목 (필수, 예: "사용자 차단")
     * @param string $message 사용자에게 보여줄 경고 메시지 (필수)
     * @param string $confirmLabel 확인 체크박스의 레이블 (필수, 예: "네, 이 작업을 수행하겠습니다")
     * @param string $inputName HTML input의 name 속성 (필수, 예: "confirm_danger")
     * @return string 위험 확인 영역 HTML
     */
    public function render(string $title, string $message, string $confirmLabel, string $inputName): string
    {
        if (empty($title) || empty($message) || empty($confirmLabel) || empty($inputName)) {
            return '';
        }

        $escapedTitle = $this->escaper->html($title);
        $escapedMessage = $this->escaper->html($message);
        $escapedConfirmLabel = $this->escaper->html($confirmLabel);
        $escapedInputName = $this->escaper->html($inputName);

        $html = '<div class="admin-danger-confirmation" role="alert">';
        $html .= '<div class="admin-danger-confirmation__header">';
        $html .= '<strong class="admin-danger-confirmation__title">⚠️ ' . $escapedTitle . '</strong>';
        $html .= '</div>';
        $html .= '<p class="admin-danger-confirmation__message">' . $escapedMessage . '</p>';
        $html .= '<label class="admin-danger-confirmation__confirm-label">';
        $html .= '<input type="checkbox" name="' . $escapedInputName . '" value="1" required aria-required="true">';
        $html .= ' ' . $escapedConfirmLabel;
        $html .= '</label>';
        $html .= '</div>';

        return $html;
    }
}
