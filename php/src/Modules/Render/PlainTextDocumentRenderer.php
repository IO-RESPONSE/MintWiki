<?php

declare(strict_types=1);

namespace MintWiki\Render;

/**
 * 평문 문서를 HTML로 렌더링하는 기본 구현 (태스크 0581).
 *
 * DocumentRenderer 인터페이스의 기본 구현으로, source를 평문으로 간주하고
 * 기본 HTML escaping과 단락 분할만 수행한다. 파서와 특화된 render 함수들이
 * 추가되면 이를 활용하도록 개선된다.
 */
final class PlainTextDocumentRenderer implements DocumentRenderer
{
    /**
     * 평문 source를 기본 HTML로 렌더링한다.
     *
     * 현재 구현은 source->HTML 연결 지점만 제공하며, 실제 파서/렌더 로직은
     * 후속 작업에서 추가된다.
     */
    public function render(string $source): RenderResult
    {
        // 빈 source 처리
        if (trim($source) === '') {
            return new RenderResult('<p></p>', []);
        }

        // 기본 HTML escaping
        $escaped = htmlspecialchars($source, ENT_QUOTES, 'UTF-8');

        // 단순한 단락 분할 (이후 파서가 더 정교한 블록 구조를 제공하게 될 예정)
        $paragraphs = array_filter(
            array_map('trim', explode("\n\n", $escaped)),
            static fn (string $para): bool => $para !== ''
        );

        $htmlParagraphs = array_map(
            static fn (string $para): string => '<p>' . nl2br($para) . '</p>',
            $paragraphs
        );

        $html = implode('', $htmlParagraphs);

        // 메타데이터 추출 (현재는 빈 배열; 파서가 통합되면 채워짐)
        $metadata = [
            'headings' => [],
            'links' => [],
            'categories' => [],
            'footnotes' => [],
        ];

        return new RenderResult($html, $metadata);
    }
}
