<?php

declare(strict_types=1);

/**
 * PlainTextDocumentRenderer 테스트 (태스크 0581).
 *
 * DocumentRenderer 인터페이스의 기본 구현을 검증한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Render\PlainTextDocumentRenderer;

final class PlainTextDocumentRendererTest
{
    public static function run(): void
    {
        self::testSimpleText();
        self::testMultipleParagraphs();
        self::testHTMLEscaping();
        self::testEmptySource();
        self::testWhitespaceHandling();
        self::testLineBreaks();
        self::testMetadataStructure();
    }

    private static function testSimpleText(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = '안녕하세요';

        $result = $renderer->render($source);

        assert(
            strpos($result->html(), '<p>') !== false && strpos($result->html(), '</p>') !== false,
            'HTML이 <p> 태그를 포함해야 함'
        );
        assert(
            strpos($result->html(), '안녕하세요') !== false,
            'HTML이 원본 텍스트를 포함해야 함'
        );
    }

    private static function testMultipleParagraphs(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = "첫 번째 단락\n\n두 번째 단락";

        $result = $renderer->render($source);
        $html = $result->html();

        // 두 개의 <p> 태그가 있어야 함
        assert(
            substr_count($html, '<p>') === 2,
            'HTML이 두 개의 <p> 태그를 포함해야 함'
        );
        assert(
            strpos($html, '첫 번째 단락') !== false,
            'HTML이 첫 번째 단락을 포함해야 함'
        );
        assert(
            strpos($html, '두 번째 단락') !== false,
            'HTML이 두 번째 단락을 포함해야 함'
        );
    }

    private static function testHTMLEscaping(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = '<script>alert("XSS")</script>';

        $result = $renderer->render($source);
        $html = $result->html();

        assert(
            strpos($html, '<script>') === false,
            'HTML이 script 태그를 escape하여 포함하지 않아야 함'
        );
        assert(
            strpos($html, '&lt;script&gt;') !== false || strpos($html, 'script') === false,
            'HTML이 위험한 마크업을 escape해야 함'
        );
    }

    private static function testEmptySource(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = '';

        $result = $renderer->render($source);

        // 빈 source도 유효한 HTML을 반환해야 함
        assert(
            strpos($result->html(), '<p>') !== false,
            'HTML이 <p> 태그를 포함해야 함'
        );
    }

    private static function testWhitespaceHandling(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = "   안녕하세요   \n\n   반갑습니다   ";

        $result = $renderer->render($source);
        $html = $result->html();

        // 공백 주위의 whitespace가 처리되어야 함
        assert(
            substr_count($html, '<p>') === 2,
            'HTML이 두 개의 단락을 렌더링해야 함'
        );
    }

    private static function testLineBreaks(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $source = "첫 번째 줄\n두 번째 줄";

        $result = $renderer->render($source);
        $html = $result->html();

        // 같은 단락 내에서 줄 바꿈이 <br>로 변환되어야 함
        assert(
            strpos($html, '<br') !== false || strpos($html, "\n") === false,
            'HTML이 줄 바꿈을 처리해야 함'
        );
    }

    private static function testMetadataStructure(): void
    {
        $renderer = new PlainTextDocumentRenderer();
        $result = $renderer->render('테스트');

        $metadata = $result->metadata();

        assert(
            isset($metadata['headings'], $metadata['links'], $metadata['categories'], $metadata['footnotes']),
            'metadata가 필수 키를 모두 포함해야 함'
        );
        assert(
            is_array($metadata['headings']),
            'headings은 배열이어야 함'
        );
        assert(
            is_array($metadata['links']),
            'links는 배열이어야 함'
        );
        assert(
            is_array($metadata['categories']),
            'categories는 배열이어야 함'
        );
        assert(
            is_array($metadata['footnotes']),
            'footnotes는 배열이어야 함'
        );
    }
}

PlainTextDocumentRendererTest::run();
fwrite(STDOUT, "PlainTextDocumentRenderer 테스트 통과.\n");
