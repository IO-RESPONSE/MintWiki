<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 폼 오류 요약 컴포넌트 (태스크 0542).
 *
 * 폼 검증 오류를 접근 가능한 방식으로 렌더링한다.
 * role="alert"와 aria-label을 사용하여 화면 읽기 프로그램이
 * 오류 요약을 감지하고 사용자에게 알릴 수 있도록 한다.
 * 모든 오류 메시지는 XSS를 방지하기 위해 escaping된다.
 */
final class FormErrorSummary
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 폼 오류 요약을 렌더링한다.
     *
     * @param array<string, string|array<string>> $errors 필드명 => 오류 메시지(들)
     * @return string 오류 요약 HTML, 오류가 없으면 빈 문자열
     */
    public function render(array $errors): string
    {
        if (empty($errors)) {
            return '';
        }

        $errorItems = '';
        foreach ($errors as $field => $messages) {
            if (is_array($messages)) {
                foreach ($messages as $message) {
                    $errorItems .= '<li>'
                        . $this->escaper->html($message)
                        . '</li>';
                }
            } else {
                $errorItems .= '<li>'
                    . $this->escaper->html($messages)
                    . '</li>';
            }
        }

        return '<div role="alert" aria-label="오류 요약">'
            . '<strong>오류가 발생했습니다</strong>'
            . '<ul>'
            . $errorItems
            . '</ul>'
            . '</div>';
    }
}
