<?php

declare(strict_types=1);

namespace MintWiki\Render;

/**
 * 렌더링 결과를 나타내는 도메인 모델 (태스크 0581).
 *
 * Python `RenderResult`(src/modules/render/model.py)를 참조한다.
 * 렌더러가 파서 결과를 처리한 후 생성하는 결과이며, 안전하게 이스케이프된
 * HTML과 렌더링 중에 추출된 메타데이터를 포함한다.
 */
final class RenderResult
{
    /**
     * 렌더링 결과를 생성한다.
     *
     * @param string $html 렌더링된 HTML 문자열
     * @param array{headings?: list<array{level: int, text: string, id: string}>, links?: list<string>, categories?: list<string>, footnotes?: list<array{id: string, text: string}>} $metadata 렌더링 중에 추출된 메타데이터
     */
    public function __construct(
        private readonly string $html,
        private readonly array $metadata = []
    ) {
    }

    /**
     * 렌더링된 HTML을 반환한다.
     */
    public function html(): string
    {
        return $this->html;
    }

    /**
     * 렌더링 중에 추출된 메타데이터를 반환한다.
     */
    public function metadata(): array
    {
        return $this->metadata;
    }

    /**
     * 제목 메타데이터를 반환한다.
     *
     * @return list<array{level: int, text: string, id: string}>
     */
    public function headings(): array
    {
        return $this->metadata['headings'] ?? [];
    }

    /**
     * 링크 메타데이터를 반환한다.
     *
     * @return list<string>
     */
    public function links(): array
    {
        return $this->metadata['links'] ?? [];
    }

    /**
     * 카테고리 메타데이터를 반환한다.
     *
     * @return list<string>
     */
    public function categories(): array
    {
        return $this->metadata['categories'] ?? [];
    }

    /**
     * 각주 메타데이터를 반환한다.
     *
     * @return list<array{id: string, text: string}>
     */
    public function footnotes(): array
    {
        return $this->metadata['footnotes'] ?? [];
    }
}
