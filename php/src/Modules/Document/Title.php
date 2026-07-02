<?php

declare(strict_types=1);

namespace MintWiki\Document;

/**
 * 문서 제목 정규화 유틸리티 (태스크 0401).
 *
 * Python `normalize_title`(src/modules/document/title.py)와 동작을 맞춘다:
 * 주변 공백을 제거하고 내부 공백을 단일 공백으로 축소하며, 정규화 결과가
 * 빈 문자열이면 EmptyTitleError를 던진다.
 */
final class Title
{
    private function __construct()
    {
    }

    public static function normalize(string $title): string
    {
        $trimmed = trim($title);
        $normalized = $trimmed === '' ? '' : preg_replace('/\s+/u', ' ', $trimmed);

        if ($normalized === '') {
            throw new EmptyTitleError('제목은 비어있을 수 없습니다');
        }

        return $normalized;
    }
}
