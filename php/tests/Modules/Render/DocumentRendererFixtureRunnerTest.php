<?php

declare(strict_types=1);

/**
 * DocumentRenderer 인터페이스 구현 검증 테스트 (태스크 0581).
 *
 * PlainTextDocumentRenderer 구현을 통해 DocumentRenderer 인터페이스가
 * 정상적으로 작동하는지 확인한다. 이는 full fixture parity 테스트가 아니며,
 * 파서/렌더 모듈이 통합되는 이후 태스크에서 fixture 기반의 전체 parity
 * 테스트로 확장될 예정이다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Render\DocumentRenderer;
use MintWiki\Render\PlainTextDocumentRenderer;
use MintWiki\Render\RenderResult;

$failures = [];

// 1. DocumentRenderer 인터페이스 존재 확인
if (!interface_exists(DocumentRenderer::class)) {
    $failures[] = "DocumentRenderer 인터페이스가 존재해야 합니다.";
}

// 2. PlainTextDocumentRenderer 구현 확인
if (!class_exists(PlainTextDocumentRenderer::class)) {
    $failures[] = "PlainTextDocumentRenderer 클래스가 존재해야 합니다.";
}

// 3. PlainTextDocumentRenderer가 DocumentRenderer를 구현하는지 확인
if (class_exists(PlainTextDocumentRenderer::class)) {
    $reflection = new \ReflectionClass(PlainTextDocumentRenderer::class);
    if (!$reflection->implementsInterface(DocumentRenderer::class)) {
        $failures[] = "PlainTextDocumentRenderer는 DocumentRenderer 인터페이스를 구현해야 합니다.";
    }
}

// 4. render() 메서드 동작 테스트
try {
    $renderer = new PlainTextDocumentRenderer();

    // 단순 텍스트 렌더링
    $result = $renderer->render('안녕하세요');
    if (!($result instanceof RenderResult)) {
        $failures[] = "render()는 RenderResult 인스턴스를 반환해야 합니다.";
    } else {
        $html = $result->html();
        if (strpos($html, '<p>') === false) {
            $failures[] = "렌더링된 HTML이 <p> 태그를 포함해야 합니다.";
        }
        if (strpos($html, '안녕하세요') === false) {
            $failures[] = "렌더링된 HTML이 원본 텍스트를 포함해야 합니다.";
        }
    }

    // 다중 단락 렌더링
    $result = $renderer->render("첫 번째\n\n두 번째");
    if ($result instanceof RenderResult) {
        $html = $result->html();
        $count = substr_count($html, '<p>');
        if ($count !== 2) {
            $failures[] = "다중 단락 렌더링에서 {$count}개의 <p> 태그가 있는데 2개여야 합니다.";
        }
    }

    // XSS 방지 확인
    $result = $renderer->render('<script>alert("XSS")</script>');
    if ($result instanceof RenderResult) {
        $html = $result->html();
        if (strpos($html, '<script>') !== false) {
            $failures[] = "HTML이 <script> 태그를 escape하지 않았습니다.";
        }
    }

    // 메타데이터 구조 확인
    $result = $renderer->render('테스트');
    if ($result instanceof RenderResult) {
        $metadata = $result->metadata();
        if (!isset($metadata['headings'], $metadata['links'], $metadata['categories'], $metadata['footnotes'])) {
            $failures[] = "메타데이터가 필수 키를 모두 포함해야 합니다.";
        }
    }
} catch (\Throwable $error) {
    $failures[] = "render() 실행 중 예외: " . $error->getMessage();
}

// 5. RenderResult 동작 확인
try {
    $testHtml = '<p>test</p>';
    $testMetadata = [
        'headings' => [['level' => 1, 'text' => 'title', 'id' => 'title']],
        'links' => ['https://example.com'],
    ];

    $result = new RenderResult($testHtml, $testMetadata);

    if ($result->html() !== $testHtml) {
        $failures[] = "RenderResult::html()이 정확한 값을 반환해야 합니다.";
    }

    if ($result->metadata() !== $testMetadata) {
        $failures[] = "RenderResult::metadata()가 정확한 값을 반환해야 합니다.";
    }

    if ($result->headings() !== $testMetadata['headings']) {
        $failures[] = "RenderResult::headings()가 정확한 값을 반환해야 합니다.";
    }

    if ($result->links() !== $testMetadata['links']) {
        $failures[] = "RenderResult::links()가 정확한 값을 반환해야 합니다.";
    }
} catch (\Throwable $error) {
    $failures[] = "RenderResult 동작 확인 중 예외: " . $error->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentRenderer FixtureRunner 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentRenderer FixtureRunner 테스트 통과 — source->HTML 연결 지점 구현 확인.\n");
exit(0);
