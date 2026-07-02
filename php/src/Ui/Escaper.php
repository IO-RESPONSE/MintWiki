<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 서버 렌더링 템플릿에서 사용자 입력을 HTML 안전 문자열로 변환한다.
 */
final class Escaper
{
    public function html(string $value): string
    {
        return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }

    public function attribute(string $value): string
    {
        return $this->html($value);
    }
}
