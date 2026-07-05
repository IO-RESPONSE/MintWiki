<?php

declare(strict_types=1);

namespace MintWiki\Parser;

/**
 * 블록 파싱 결과를 나타내는 value object (태스크 0705).
 *
 * 문서 본문 HTML과, TOC 생성을 위한 제목 컬렉션, 그리고 문서 전체에서
 * 발견한 내부 링크 문서 제목 목록을 담는다. `headings()`의 반환 shape은
 * `MintWiki\Render\RenderResult::headings()`가 기대하는
 * `list<array{level: int, text: string, id: string}>`와 동일하게 맞춰
 * 0706의 렌더러가 그대로 옮겨 담을 수 있게 한다.
 */
final class BlockParseResult
{
    /**
     * @param list<array{level: int, text: string, id: string}> $headings
     * @param list<string> $links 본문에서 발견한 내부 링크 문서 제목 목록(중복 포함, 발견 순서)
     */
    public function __construct(
        private readonly string $html,
        private readonly array $headings = [],
        private readonly array $links = []
    ) {
    }

    public function html(): string
    {
        return $this->html;
    }

    /**
     * @return list<array{level: int, text: string, id: string}>
     */
    public function headings(): array
    {
        return $this->headings;
    }

    /**
     * @return list<string>
     */
    public function links(): array
    {
        return $this->links;
    }
}
