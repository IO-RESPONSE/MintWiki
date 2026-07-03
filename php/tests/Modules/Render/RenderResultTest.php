<?php

declare(strict_types=1);

/**
 * RenderResult 도메인 모델 테스트 (태스크 0581).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Render\RenderResult;

final class RenderResultTest
{
    public static function run(): void
    {
        self::testCreationWithHtmlOnly();
        self::testCreationWithMetadata();
        self::testHeadings();
        self::testLinks();
        self::testCategories();
        self::testFootnotes();
        self::testEmptyMetadata();
    }

    private static function testCreationWithHtmlOnly(): void
    {
        $html = '<p>안녕하세요</p>';
        $result = new RenderResult($html);

        assert($result->html() === $html, 'html() 메서드가 정확한 HTML을 반환해야 함');
        assert($result->metadata() === [], 'metadata()는 기본값 빈 배열을 반환해야 함');
    }

    private static function testCreationWithMetadata(): void
    {
        $html = '<h1>제목</h1><p>내용</p>';
        $metadata = [
            'headings' => [
                ['level' => 1, 'text' => '제목', 'id' => 'title'],
            ],
            'links' => ['https://example.com'],
            'categories' => ['카테고리1'],
            'footnotes' => [
                ['id' => 'fn1', 'text' => '각주 내용'],
            ],
        ];

        $result = new RenderResult($html, $metadata);

        assert($result->html() === $html, 'html()이 정확한 값을 반환해야 함');
        assert($result->metadata() === $metadata, 'metadata()가 정확한 값을 반환해야 함');
    }

    private static function testHeadings(): void
    {
        $metadata = [
            'headings' => [
                ['level' => 1, 'text' => '제목1', 'id' => 'h1'],
                ['level' => 2, 'text' => '제목2', 'id' => 'h2'],
            ],
        ];

        $result = new RenderResult('<p></p>', $metadata);
        assert($result->headings() === $metadata['headings'], 'headings()이 정확한 제목 목록을 반환해야 함');
    }

    private static function testLinks(): void
    {
        $metadata = [
            'links' => ['https://example.com', 'https://test.org'],
        ];

        $result = new RenderResult('<p></p>', $metadata);
        assert($result->links() === $metadata['links'], 'links()가 정확한 링크 목록을 반환해야 함');
    }

    private static function testCategories(): void
    {
        $metadata = [
            'categories' => ['카테고리1', '카테고리2'],
        ];

        $result = new RenderResult('<p></p>', $metadata);
        assert($result->categories() === $metadata['categories'], 'categories()가 정확한 카테고리 목록을 반환해야 함');
    }

    private static function testFootnotes(): void
    {
        $metadata = [
            'footnotes' => [
                ['id' => 'fn1', 'text' => '각주1'],
                ['id' => 'fn2', 'text' => '각주2'],
            ],
        ];

        $result = new RenderResult('<p></p>', $metadata);
        assert($result->footnotes() === $metadata['footnotes'], 'footnotes()가 정확한 각주 목록을 반환해야 함');
    }

    private static function testEmptyMetadata(): void
    {
        $result = new RenderResult('<p>내용</p>');

        assert($result->headings() === [], 'headings()는 메타데이터가 없으면 빈 배열을 반환해야 함');
        assert($result->links() === [], 'links()는 메타데이터가 없으면 빈 배열을 반환해야 함');
        assert($result->categories() === [], 'categories()는 메타데이터가 없으면 빈 배열을 반환해야 함');
        assert($result->footnotes() === [], 'footnotes()는 메타데이터가 없으면 빈 배열을 반환해야 함');
    }
}

RenderResultTest::run();
fwrite(STDOUT, "RenderResult 테스트 통과.\n");
