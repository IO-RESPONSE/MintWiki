<?php

declare(strict_types=1);

namespace MintWiki\Ui;

use MintWiki\Document\Document;
use MintWiki\Render\DocumentRenderer;
use MintWiki\Render\PlainTextDocumentRenderer;
use MintWiki\Ui\SeoMetadata;

/**
 * 단일 문서 view page의 서버 렌더링 (태스크 0529, 0582).
 *
 * 존재하는 문서를 표시하거나, 없는 경우 "문서를 찾을 수 없음" 메시지를 보여준다.
 * 모든 사용자 입력(문서 title 등)은 escaping되어 XSS를 방지한다.
 * 문서 source는 DocumentRenderer를 통해 HTML로 렌더링되며, 렌더러가 생성한
 * HTML은 이미 안전하게 처리되어 있다 (태스크 0582).
 */
final class DocumentViewPage
{
    private Escaper $escaper;
    private Layout $layout;
    private DocumentRenderer $renderer;

    public function __construct(
        ?Escaper $escaper = null,
        ?Layout $layout = null,
        ?DocumentRenderer $renderer = null
    ) {
        $this->escaper = $escaper ?? new Escaper();
        $this->layout = $layout ?? new Layout();
        $this->renderer = $renderer ?? new PlainTextDocumentRenderer();
    }

    /**
     * 문서 view page를 렌더링한다.
     *
     * @param Document|null $document 조회한 문서, 없으면 null
     * @param string|null $source 문서의 source 내용, 없으면 placeholder 표시
     */
    public function render(?Document $document, ?string $source = null): string
    {
        if ($document === null) {
            return $this->renderNotFound();
        }

        return $this->renderDocument($document, $source);
    }

    /**
     * 존재하는 문서를 렌더링한다.
     */
    private function renderDocument(Document $document, ?string $source = null): string
    {
        $title = $this->escaper->html($document->title());

        // source가 제공되면 렌더러로 렌더링, 아니면 placeholder
        if ($source !== null) {
            try {
                $renderResult = $this->renderer->render($source);
                $contentHtml = $renderResult->html();
            } catch (\Throwable $e) {
                // 렌더링 실패 시 fallback: source를 escape하여 표시
                $contentHtml = $this->renderFallback($source);
            }
        } else {
            $contentHtml = '<p>문서 내용이 여기에 표시됩니다.</p>';
        }

        $body = '<main>'
            . '<h1>' . $title . '</h1>'
            . $contentHtml
            . '</main>';

        $seo = new SeoMetadata(
            $document->title(),
            $this->extractDescription($source),
            '/docs/' . $document->id()
        );

        return $this->layout->render($document->title(), $body, 'ko', null, $seo);
    }

    /**
     * 렌더링 실패 시 fallback을 렌더링한다.
     *
     * source를 escape하여 사용자가 볼 수 있도록 표시하고,
     * 렌더링 오류 안내를 제공한다.
     */
    private function renderFallback(string $source): string
    {
        $escapedSource = $this->escaper->html($source);
        return '<div class="render-fallback">'
            . '<p class="render-fallback-message">문서 렌더링에 실패했습니다. 아래는 원본 소스입니다:</p>'
            . '<pre class="render-fallback-source">' . $escapedSource . '</pre>'
            . '</div>';
    }

    /**
     * 문서를 찾을 수 없을 때의 page를 렌더링한다.
     */
    private function renderNotFound(): string
    {
        $body = '<main>'
            . '<h1>문서를 찾을 수 없습니다</h1>'
            . '<p>요청하신 문서가 존재하지 않습니다.</p>'
            . '</main>';

        return $this->layout->render('문서를 찾을 수 없습니다', $body);
    }

    /**
     * source에서 meta description으로 사용할 텍스트를 추출한다.
     *
     * 첫 160 글자 이내의 텍스트를 사용하며, 줄바꿈은 공백으로 정규화된다.
     * source가 null이거나 비어있으면 null을 반환한다.
     */
    private function extractDescription(?string $source): ?string
    {
        if ($source === null || trim($source) === '') {
            return null;
        }

        $text = trim($source);
        $text = preg_replace('/\s+/', ' ', $text) ?? $text;

        $maxLength = 160;
        if (strlen($text) > $maxLength) {
            $text = substr($text, 0, $maxLength) . '...';
        }

        return $text;
    }
}
