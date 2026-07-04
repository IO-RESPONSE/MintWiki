<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * Phase D 서버 렌더링 UI의 최소 layout skeleton.
 *
 * 화면별 템플릿이 만든 HTML body를 문서 구조로 감싼다. body는 호출자가 이미
 * escaping한 HTML로 간주하고, title/lang 같은 layout 값만 여기서 escape한다.
 * requestId는 운영 문의 추적을 위해 footer에 표시된다.
 *
 * 0691에서 header에 상단 네비게이션 바(0690 `NavigationBar`)를 주입할 수
 * 있도록 확장했다. 생성자에 이미 렌더링된 header HTML을 전달하며, body와
 * 같은 계약으로 이미 escaping을 마친 신뢰 가능한 HTML로 간주한다. 생성자에
 * 아무것도 넘기지 않으면 기존과 동일하게 빈 `<header></header>`를 렌더링해
 * `render()` 시그니처의 하위 호환을 그대로 지킨다(navigation 미전달 시에도
 * 깨지지 않아야 한다는 계약). footer의 사이트 정보(이름/라이선스 안내)는
 * header와 달리 항상 표시된다. body는 0689의 `--content-max-width` 토큰으로
 * 중앙 정렬되는 콘텐츠 wrapper로 감싼다.
 */
final class Layout
{
    private Escaper $escaper;
    private ?string $headerContent;

    public function __construct(?Escaper $escaper = null, ?string $headerContent = null)
    {
        $this->escaper = $escaper ?? new Escaper();
        $this->headerContent = $headerContent;
    }

    /**
     * HTML 페이지를 렌더링한다.
     *
     * @param string $title 페이지 제목
     * @param string $body 페이지 본문 (이미 escaping된 HTML)
     * @param string $lang HTML lang 속성 값
     * @param string|null $requestId 운영 문의 추적용 요청 id
     * @param SeoMetadata|null $seo SEO 메타데이터 (description, canonical URL 등)
     */
    public function render(string $title, string $body, string $lang = 'ko', ?string $requestId = null, ?SeoMetadata $seo = null): string
    {
        $escapedTitle = $this->escaper->html($title);
        $escapedLang = $this->escaper->attribute($lang);

        $header = '<header>' . ($this->headerContent ?? '') . '</header>';

        $footer = '<footer>'
            . '<div class="site-footer-info">'
            . '<p class="site-footer-info__name">MintWiki</p>'
            . '<p class="site-footer-info__license">이 위키의 문서는 별도로 표시하지 않는 한 자유 이용 라이선스를 따르며, 이용에 대한 책임은 이용자 본인에게 있습니다.</p>'
            . '</div>';
        if ($requestId !== null) {
            $escapedRequestId = $this->escaper->html($requestId);
            $footer .= '<div data-request-id="' . $this->escaper->attribute($requestId) . '">요청ID: ' . $escapedRequestId . '</div>';
        }
        $footer .= '</footer>';

        $headContent = '<meta charset="utf-8">'
            . '<meta name="viewport" content="width=device-width, initial-scale=1">';

        if ($seo !== null) {
            if ($seo->description() !== null) {
                $escapedDescription = $this->escaper->attribute($seo->description());
                $headContent .= '<meta name="description" content="' . $escapedDescription . '">';
            }

            if ($seo->canonicalUrl() !== null) {
                $escapedCanonical = $this->escaper->attribute($seo->canonicalUrl());
                $headContent .= '<link rel="canonical" href="' . $escapedCanonical . '">';
            }
        }

        return '<!doctype html>'
            . '<html lang="' . $escapedLang . '">'
            . '<head>'
            . $headContent
            . '<title>' . $escapedTitle . '</title>'
            . '<link rel="stylesheet" href="/assets/css/design-tokens.css">'
            . '<link rel="stylesheet" href="/assets/css/navigation.css">'
            . '<link rel="stylesheet" href="/assets/css/layout.css">'
            . '<link rel="stylesheet" href="/assets/css/buttons.css">'
            . '<link rel="stylesheet" href="/assets/css/print.css" media="print">'
            . '</head>'
            . '<body>'
            . $header
            . '<div class="site-content">' . $body . '</div>'
            . $footer
            . '</body>'
            . '</html>';
    }
}
