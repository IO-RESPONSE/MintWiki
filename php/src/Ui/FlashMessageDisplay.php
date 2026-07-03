<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 플래시 메시지 표시 컴포넌트 (태스크 0543).
 *
 * 세션에 저장된 플래시 메시지를 렌더링한다. 메시지 타입에 따라 다른 스타일을 적용한다.
 * 모든 메시지는 XSS를 방지하기 위해 escaping된다.
 */
final class FlashMessageDisplay
{
    private Escaper $escaper;
    private FlashMessage $flashMessage;

    public function __construct(?Escaper $escaper = null, ?FlashMessage $flashMessage = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->flashMessage = $flashMessage ?? new FlashMessage();
    }

    /**
     * 플래시 메시지를 렌더링한다.
     *
     * @return string 플래시 메시지 HTML, 메시지가 없으면 빈 문자열
     */
    public function render(): string
    {
        $message = $this->flashMessage->get();

        if ($message === null) {
            return '';
        }

        $type = $message['type'] ?? 'success';
        $text = $message['message'] ?? '';

        $escapedText = $this->escaper->html($text);
        $escapedType = $this->escaper->attribute($type);

        return '<div class="flash-message flash-message--' . $escapedType . '" role="status" aria-label="알림">'
            . '<p>'
            . $escapedText
            . '</p>'
            . '</div>';
    }
}
