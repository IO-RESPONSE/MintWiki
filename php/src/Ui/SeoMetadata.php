<?php

declare(strict_types=1);

namespace MintWiki\Ui;

/**
 * 페이지의 SEO 메타데이터를 표현하는 immutable value object.
 *
 * title과 description 같은 기본 SEO 정보를 관리한다.
 * canonical URL은 선택사항이며, 주로 문서 페이지에서 사용된다.
 */
final class SeoMetadata
{
    public function __construct(
        private readonly string $title,
        private readonly ?string $description = null,
        private readonly ?string $canonicalUrl = null,
    ) {
    }

    public function title(): string
    {
        return $this->title;
    }

    public function description(): ?string
    {
        return $this->description;
    }

    public function canonicalUrl(): ?string
    {
        return $this->canonicalUrl;
    }
}
