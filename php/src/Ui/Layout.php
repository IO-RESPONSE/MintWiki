<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * Phase D 서버 렌더링 UI의 최소 layout skeleton.
 *
 * 화면별 템플릿이 만든 HTML body를 문서 구조로 감싼다. body는 호출자가 이미
 * escaping한 HTML로 간주하고, title/lang 같은 layout 값만 여기서 escape한다.
 * requestId는 운영 문의 추적을 위해 footer에 표시된다.
 */
final class Layout
{
    private Escaper $escaper;

    public function __construct(?Escaper $escaper = null)
    {
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * HTML 페이지를 렌더링한다.
     *
     * @param string $title 페이지 제목
     * @param string $body 페이지 본문 (이미 escaping된 HTML)
     * @param string $lang HTML lang 속성 값
     * @param string|null $requestId 운영 문의 추적용 요청 id
     */
    public function render(string $title, string $body, string $lang = 'ko', ?string $requestId = null): string
    {
        $escapedTitle = $this->escaper->html($title);
        $escapedLang = $this->escaper->attribute($lang);

        $footer = '<footer>';
        if ($requestId !== null) {
            $escapedRequestId = $this->escaper->html($requestId);
            $footer .= '<div data-request-id="' . $this->escaper->attribute($requestId) . '">요청ID: ' . $escapedRequestId . '</div>';
        }
        $footer .= '</footer>';

        return '<!doctype html>'
            . '<html lang="' . $escapedLang . '">'
            . '<head>'
            . '<meta charset="utf-8">'
            . '<meta name="viewport" content="width=device-width, initial-scale=1">'
            . '<title>' . $escapedTitle . '</title>'
            . '<link rel="stylesheet" href="/assets/css/design-tokens.css">'
            . '<link rel="stylesheet" href="/assets/css/print.css" media="print">'
            . '</head>'
            . '<body>'
            . '<header></header>'
            . $body
            . $footer
            . '</body>'
            . '</html>';
    }
}
