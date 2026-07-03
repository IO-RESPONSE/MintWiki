<?php

declare(strict_types=1);

/**
 * `MintWiki\Http\DocumentCreateHandler`의 동작을 확인하는 smoke test (태스크 0531).
 *
 * phpunit 없이 `php` CLI만으로 실행된다. 문서 생성 핸들러가 DocumentService를
 * 호출하고, 성공/실패 응답을 올바르게 반환하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;
use MintWiki\Http\DocumentCreateHandler;
use MintWiki\Ui\DocumentViewPage;

$failures = [];

// 테스트용 repository 구현
$repository = new class implements Repository {
    /** @var array<string, Document> */
    private array $documents = [];

    public function create(Document $document): Document
    {
        foreach ($this->documents as $existing) {
            if ($existing->normalizedTitle() === $document->normalizedTitle()) {
                throw new DuplicateNormalizedTitleError();
            }
        }
        $this->documents[$document->id()] = $document;
        return $document;
    }

    public function get(string $id): ?Document
    {
        return $this->documents[$id] ?? null;
    }

    public function getByNormalizedTitle(string $normalizedTitle): ?Document
    {
        foreach ($this->documents as $document) {
            if ($document->normalizedTitle() === $normalizedTitle) {
                return $document;
            }
        }
        return null;
    }

    public function update(Document $document): Document
    {
        $this->documents[$document->id()] = $document;
        return $document;
    }
};

$service = new Service($repository);
$viewPage = new DocumentViewPage();
$handler = new DocumentCreateHandler($service, $viewPage);

$expectedHtmlHeaders = [
    'Content-Type' => 'text/html; charset=utf-8',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
];

// (1) 정상적인 문서 생성
$response = $handler->handle('Test Document');
if ($response->status() !== 201) {
    $failures[] = '성공한 생성의 status는 201이어야 한다.';
}
if ($response->headers() !== $expectedHtmlHeaders) {
    $failures[] = '성공한 생성의 Content-Type은 text/html; charset=utf-8이어야 한다.';
}
if (!str_contains($response->body(), 'Test Document')) {
    $failures[] = '성공한 생성의 응답이 생성된 문서 제목을 포함해야 한다.';
}

// (2) 빈 제목으로 생성 시도
$response = $handler->handle('   ');
if ($response->status() !== 400) {
    $failures[] = '빈 제목의 생성은 400 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), '제목이 비어있습니다')) {
    $failures[] = '빈 제목의 응답이 적절한 에러 메시지를 포함해야 한다.';
}

// (3) 중복 제목으로 생성 시도
$response = $handler->handle('Duplicate');
if ($response->status() !== 201) {
    $failures[] = '첫 번째 생성은 성공해야 한다.';
}

$response = $handler->handle('Duplicate');
if ($response->status() !== 409) {
    $failures[] = '중복 제목의 생성은 409 상태코드를 반환해야 한다.';
}
if (!str_contains($response->body(), '이미 존재하는 제목입니다')) {
    $failures[] = '중복 제목의 응답이 적절한 에러 메시지를 포함해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentCreateHandler 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentCreateHandler 테스트 통과.\n");
exit(0);
