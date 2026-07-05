<?php

declare(strict_types=1);

namespace MintWiki\Render;

use MintWiki\Parser\BlockParser;
use MintWiki\Ui\Escaper;

/**
 * NamuMark풍 문서 source를 실제 HTML로 렌더링하는 DocumentRenderer 구현
 * (태스크 0706).
 *
 * 0705 `BlockParser`(-> 0704 `InlineParser`)에 실제 파싱을 위임하고, 그
 * 결과를 `RenderResult`로 감싼다. `BlockParseResult::headings()`/`links()`는
 * shape이 `RenderResult::headings()`/`links()`와 동일하므로 그대로 옮겨
 * 담는다.
 *
 * 제목이 2개 이상이면 각 제목의 앵커 id로 점프하는 목차(TOC)를 본문 HTML
 * 앞에 붙인다 — `DocumentViewPage`(및 0708 편집 미리보기)는 `html()`을
 * 그대로 표시하기만 하면 TOC가 본문 상단에 나타난다.
 *
 * XSS 안전: 본문 HTML은 전부 `BlockParser`(-> `InlineParser`)가 이스케이프한
 * 결과다. TOC 앵커도 `headings()`의 텍스트/id를 `Escaper`로 다시 이스케이프해
 * 조립하므로 안전하다.
 */
final class NamuMarkDocumentRenderer implements DocumentRenderer
{
    private const MIN_HEADINGS_FOR_TOC = 2;

    private BlockParser $blockParser;
    private Escaper $escaper;

    public function __construct(?BlockParser $blockParser = null, ?Escaper $escaper = null)
    {
        $this->blockParser = $blockParser ?? new BlockParser();
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * NamuMark풍 source를 HTML로 렌더링한다.
     */
    public function render(string $source): RenderResult
    {
        $blockResult = $this->blockParser->parse($source);
        $headings = $blockResult->headings();

        $html = $this->renderToc($headings) . $blockResult->html();

        return new RenderResult($html, [
            'headings' => $headings,
            'links' => $blockResult->links(),
            'categories' => [],
            'footnotes' => [],
        ]);
    }

    /**
     * 제목 컬렉션으로 목차(TOC) HTML을 만든다. 제목이 2개 미만이면
     * 목차를 노출하지 않는다.
     *
     * @param list<array{level: int, text: string, id: string}> $headings
     */
    private function renderToc(array $headings): string
    {
        if (count($headings) < self::MIN_HEADINGS_FOR_TOC) {
            return '';
        }

        $itemsHtml = '';
        foreach ($headings as $heading) {
            $escapedHref = $this->escaper->attribute('#' . $heading['id']);
            $escapedText = $this->escaper->html($heading['text']);
            $itemsHtml .= '<li class="toc__item toc__item--level-' . $heading['level'] . '">'
                . '<a class="toc__link" href="' . $escapedHref . '">' . $escapedText . '</a>'
                . '</li>';
        }

        return '<nav class="toc" aria-label="문서 목차">'
            . '<p class="toc__title">목차</p>'
            . '<ol class="toc__list">' . $itemsHtml . '</ol>'
            . '</nav>';
    }
}
