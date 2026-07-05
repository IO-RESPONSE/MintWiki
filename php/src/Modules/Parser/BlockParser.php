<?php

declare(strict_types=1);

namespace MintWiki\Parser;

use MintWiki\Ui\Escaper;

/**
 * NamuMark풍 **블록** 문법을 HTML로 변환하는 파서 (태스크 0705).
 *
 * 인라인 문법(굵게/기울임/링크 등, 0704 `InlineParser`)은 이 클래스의
 * 책임이 아니다 — 이 클래스는 줄 단위로 소스를 블록(제목/목록/표/구분선/
 * 인용/문단)으로 나누고, 각 블록의 텍스트를 `InlineParser`에 위임해
 * 렌더링한 뒤 하나의 문서 본문 HTML로 조립한다. 최종 렌더 조립(0706,
 * `NamuMarkDocumentRenderer`/`RenderResult`)은 이 클래스를 호출하는
 * 상위 계층의 책임이다.
 *
 * 지원 블록 문법:
 * - `== 제목 ==` ~ `====== 제목 ======` (나무위키식, 레벨 1~5) -> `<h2>`~`<h6>`
 *   (레벨 = 등호 개수 - 1). 각 제목은 앵커 id와 함께 `headings()`로 수집된다.
 * - `* 항목`, `** 하위 항목`, ... -> 중첩 `<ul>` (중첩 깊이는 `*`의 개수)
 * - `1. 항목` -> `<ol>` (목록 안의 실제 숫자는 무시하고 순서만 사용)
 * - `||셀||셀||` -> `<table>` (연속된 행을 하나의 표로 묶는다)
 * - `----` (대시 4개 이상) -> `<hr>`
 * - `> 인용문` -> `<blockquote>` (연속된 인용 줄을 하나의 블록으로 묶는다)
 * - 그 외 텍스트: 빈 줄로 구분되는 문단 -> `<p>` (같은 문단 안 줄바꿈은 `<br>`)
 *
 * XSS 안전: 각 블록의 텍스트는 `InlineParser`를 거쳐서만 HTML에 들어가므로
 * 0704가 보장하는 이스케이프 계약이 그대로 유지된다. 제목 앵커 id는 원문이
 * 아니라 안전한 문자(유니코드 문자/숫자/하이픈)만 남긴 slug이며, `Escaper`로
 * attribute 이스케이프까지 거친다.
 */
final class BlockParser
{
    private const HEADING_PATTERN = '/^(={2,6})\s*(.+?)\s*\1$/u';
    private const HORIZONTAL_RULE_PATTERN = '/^-{4,}$/u';
    private const UNORDERED_ITEM_PATTERN = '/^(\*+)\s+(.+)$/u';
    private const ORDERED_ITEM_PATTERN = '/^\d+\.\s+(.+)$/u';
    private const TABLE_ROW_PATTERN = '/^\|\|(.*)\|\|$/u';
    private const QUOTE_LINE_PATTERN = '/^>\s?(.*)$/u';

    private InlineParser $inlineParser;
    private Escaper $escaper;

    /** @var list<string> */
    private array $htmlChunks = [];

    /** @var list<array{level: int, text: string, id: string}> */
    private array $headings = [];

    /** @var list<string> */
    private array $links = [];

    /** @var array<string, int> 제목 slug 중복 카운트(슬러그 -> 지금까지 등장 횟수) */
    private array $slugCounts = [];

    public function __construct(?InlineParser $inlineParser = null, ?Escaper $escaper = null)
    {
        $this->inlineParser = $inlineParser ?? new InlineParser();
        $this->escaper = $escaper ?? new Escaper();
    }

    /**
     * 소스 텍스트의 블록 문법을 HTML로 변환한다.
     */
    public function parse(string $source): BlockParseResult
    {
        $this->htmlChunks = [];
        $this->headings = [];
        $this->links = [];
        $this->slugCounts = [];

        $lines = preg_split('/\r\n|\r|\n/', $source);
        if ($lines === false) {
            $lines = [];
        }

        $pendingKind = null;
        /** @var list<mixed> $pendingItems */
        $pendingItems = [];

        foreach ($lines as $rawLine) {
            $line = trim($rawLine);

            if ($line === '') {
                [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                continue;
            }

            if (preg_match(self::HEADING_PATTERN, $line, $matches) === 1) {
                [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                $this->htmlChunks[] = $this->renderHeading(strlen($matches[1]) - 1, $matches[2]);
                continue;
            }

            if (preg_match(self::HORIZONTAL_RULE_PATTERN, $line) === 1) {
                [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                $this->htmlChunks[] = '<hr>';
                continue;
            }

            if (preg_match(self::UNORDERED_ITEM_PATTERN, $line, $matches) === 1) {
                if ($pendingKind !== 'ulist') {
                    [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                    $pendingKind = 'ulist';
                }
                $pendingItems[] = ['level' => strlen($matches[1]), 'text' => $matches[2]];
                continue;
            }

            if (preg_match(self::ORDERED_ITEM_PATTERN, $line, $matches) === 1) {
                if ($pendingKind !== 'olist') {
                    [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                    $pendingKind = 'olist';
                }
                $pendingItems[] = $matches[1];
                continue;
            }

            if (preg_match(self::TABLE_ROW_PATTERN, $line, $matches) === 1) {
                if ($pendingKind !== 'table') {
                    [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                    $pendingKind = 'table';
                }
                $pendingItems[] = $matches[1];
                continue;
            }

            if (preg_match(self::QUOTE_LINE_PATTERN, $line, $matches) === 1) {
                if ($pendingKind !== 'quote') {
                    [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                    $pendingKind = 'quote';
                }
                $pendingItems[] = $matches[1];
                continue;
            }

            if ($pendingKind !== 'paragraph') {
                [$pendingKind, $pendingItems] = $this->flushPending($pendingKind, $pendingItems);
                $pendingKind = 'paragraph';
            }
            $pendingItems[] = $line;
        }

        $this->flushPending($pendingKind, $pendingItems);

        return new BlockParseResult(implode('', $this->htmlChunks), $this->headings, $this->links);
    }

    /**
     * 누적 중이던 블록을 렌더링해 htmlChunks에 추가하고, 빈 pending 상태를 반환한다.
     *
     * @param list<mixed> $items
     * @return array{0: null, 1: list<mixed>}
     */
    private function flushPending(?string $kind, array $items): array
    {
        if ($kind !== null && $items !== []) {
            $this->htmlChunks[] = $this->renderPending($kind, $items);
        }

        return [null, []];
    }

    /**
     * @param list<mixed> $items
     */
    private function renderPending(string $kind, array $items): string
    {
        return match ($kind) {
            'paragraph' => $this->renderParagraph($items),
            'ulist' => $this->renderNestedList($this->buildNestedList($items), 'ul'),
            'olist' => $this->renderFlatOrderedList($items),
            'table' => $this->renderTable($items),
            'quote' => $this->renderQuote($items),
            default => throw new \LogicException("알 수 없는 블록 종류입니다: {$kind}"),
        };
    }

    /**
     * @param list<string> $lines
     */
    private function renderParagraph(array $lines): string
    {
        $rendered = array_map(fn (string $line): string => $this->renderInline($line), $lines);

        return '<p>' . implode('<br>', $rendered) . '</p>';
    }

    /**
     * @param list<string> $lines
     */
    private function renderQuote(array $lines): string
    {
        $rendered = array_map(fn (string $line): string => $this->renderInline($line), $lines);

        return '<blockquote><p>' . implode('<br>', $rendered) . '</p></blockquote>';
    }

    /**
     * @param list<string> $rows ||와 ||사이의 원문(셀 구분자는 아직 분리하지 않은 상태)
     */
    private function renderTable(array $rows): string
    {
        $rowsHtml = '';
        foreach ($rows as $rowContent) {
            $cellsHtml = '';
            foreach (explode('||', $rowContent) as $cell) {
                $cellsHtml .= '<td>' . $this->renderInline(trim($cell)) . '</td>';
            }
            $rowsHtml .= "<tr>{$cellsHtml}</tr>";
        }

        return "<table>{$rowsHtml}</table>";
    }

    /**
     * @param list<string> $texts
     */
    private function renderFlatOrderedList(array $texts): string
    {
        $itemsHtml = '';
        foreach ($texts as $text) {
            $itemsHtml .= '<li>' . $this->renderInline($text) . '</li>';
        }

        return "<ol>{$itemsHtml}</ol>";
    }

    /**
     * 평탄한 (level, text) 아이템 배열을 중첩 트리로 변환한다 — 스택에
     * 부모 노드를 쌓아 두고, 더 얕거나 같은 레벨을 만나면 그 부모까지
     * pop 한 뒤 남은 최상단(또는 루트)에 자식으로 매단다.
     *
     * @param list<array{level: int, text: string}> $items
     * @return list<object{text: string, children: list<object>}>
     */
    private function buildNestedList(array $items): array
    {
        $root = [];
        /** @var list<array{level: int, node: object}> $stack */
        $stack = [];

        foreach ($items as $item) {
            $node = (object) ['text' => $item['text'], 'children' => []];

            while ($stack !== [] && end($stack)['level'] >= $item['level']) {
                array_pop($stack);
            }

            if ($stack === []) {
                $root[] = $node;
            } else {
                end($stack)['node']->children[] = $node;
            }

            $stack[] = ['level' => $item['level'], 'node' => $node];
        }

        return $root;
    }

    /**
     * @param list<object{text: string, children: list<object>}> $nodes
     */
    private function renderNestedList(array $nodes, string $tag): string
    {
        $itemsHtml = '';
        foreach ($nodes as $node) {
            $innerHtml = $this->renderInline($node->text);
            $childrenHtml = $node->children !== [] ? $this->renderNestedList($node->children, $tag) : '';
            $itemsHtml .= "<li>{$innerHtml}{$childrenHtml}</li>";
        }

        return "<{$tag}>{$itemsHtml}</{$tag}>";
    }

    /**
     * 제목 블록 하나를 렌더링하고, 앵커 id와 함께 headings()용 컬렉션에 담는다.
     */
    private function renderHeading(int $level, string $rawText): string
    {
        $innerHtml = $this->renderInline($rawText);
        $label = $this->plainLabel($innerHtml);
        $id = $this->slugify($label);
        $tag = 'h' . ($level + 1);
        $escapedId = $this->escaper->attribute($id);

        $this->headings[] = ['level' => $level, 'text' => $label, 'id' => $id];

        return "<{$tag} id=\"{$escapedId}\">{$innerHtml}</{$tag}>";
    }

    /**
     * 인라인 파서로 렌더링한 HTML에서 태그를 걷어낸 순수 텍스트를 얻는다
     * (제목 label/slug 계산용) — `'''굵게'''` 같은 마크업 기호가 앵커 id나
     * TOC 라벨에 그대로 노출되지 않게 한다.
     */
    private function plainLabel(string $html): string
    {
        $plain = strip_tags($html);

        return html_entity_decode($plain, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }

    /**
     * 제목 텍스트를 앵커 id로 쓸 수 있는 slug로 변환한다. 유니코드
     * 문자/숫자/공백/하이픈만 남기고 나머지는 제거한 뒤, 공백을 하이픈으로
     * 접고 소문자화한다. 같은 slug가 이미 있으면 `-2`, `-3`, ... 접미사를
     * 붙여 충돌을 피한다.
     */
    private function slugify(string $text): string
    {
        $stripped = preg_replace('/[^\p{L}\p{N}\s-]/u', '', $text) ?? '';
        $collapsed = preg_replace('/[\s-]+/u', '-', trim($stripped)) ?? '';
        $slug = trim(mb_strtolower($collapsed, 'UTF-8'), '-');

        if ($slug === '') {
            $slug = 'section';
        }

        $seenCount = $this->slugCounts[$slug] ?? 0;
        $this->slugCounts[$slug] = $seenCount + 1;

        return $seenCount === 0 ? $slug : "{$slug}-" . ($seenCount + 1);
    }

    /**
     * 인라인 파서를 호출하고, 발견된 내부 링크를 문서 전체 links()에 모은다.
     */
    private function renderInline(string $text): string
    {
        $result = $this->inlineParser->parse($text);

        foreach ($result->links() as $link) {
            $this->links[] = $link;
        }

        return $result->html();
    }
}
