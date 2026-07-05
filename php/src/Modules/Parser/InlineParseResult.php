<?php

declare(strict_types=1);

namespace MintWiki\Parser;

/**
 * 인라인 파싱 결과를 나타내는 value object (태스크 0704).
 *
 * 이스케이프까지 마친 HTML 조각과, 본문에서 발견한 내부 링크 문서 제목
 * 목록을 담는다. 링크 목록은 렌더러가 `RenderResult::links()`를 채우는 데
 * 그대로 사용할 수 있다 — 문서 존재 여부 판정은 이 결과의 책임이 아니다
 * (0706에서 렌더러가 처리한다).
 */
final class InlineParseResult
{
    /**
     * @param list<string> $links 본문에서 발견한 내부 링크 문서 제목 목록(중복 포함, 발견 순서)
     */
    public function __construct(
        private readonly string $html,
        private readonly array $links = []
    ) {
    }

    public function html(): string
    {
        return $this->html;
    }

    /**
     * @return list<string>
     */
    public function links(): array
    {
        return $this->links;
    }
}
