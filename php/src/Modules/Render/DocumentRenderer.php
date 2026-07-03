<?php

declare(strict_types=1);

namespace MintWiki\Render;

/**
 * 문서 source를 HTML로 렌더링하는 adapter (태스크 0581).
 *
 * 이 인터페이스는 source->HTML 연결 지점을 정의한다. 파서와 렌더 모듈을
 * 조직하여 문서 source를 최종 HTML로 변환한다. 구현체는 parser 결과를
 * 처리하고 render 함수들을 활용하여 HTML을 생성한다.
 */
interface DocumentRenderer
{
    /**
     * 문서 source를 HTML로 렌더링한다.
     *
     * @param string $source 문서의 source 텍스트
     * @return RenderResult 렌더링된 HTML과 메타데이터
     */
    public function render(string $source): RenderResult;
}
