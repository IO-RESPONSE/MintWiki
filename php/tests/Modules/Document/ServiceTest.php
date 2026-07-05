<?php

declare(strict_types=1);

/**
 * MintWiki\Document\Service의 create/get 계약을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0402 RepositoryTest.php와 동일한 방식).
 *
 * 태스크 0403은 create/get 계약만 다루므로, get_by_title 등 나머지 서비스
 * 메서드는 이 테스트의 범위가 아니다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\NotFoundError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;

$failures = [];

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
        if (!isset($this->documents[$document->id()])) {
            throw new NotFoundError();
        }
        $this->documents[$document->id()] = $document;
        return $document;
    }

    public function delete(string $id): void
    {
        if (!isset($this->documents[$id])) {
            throw new NotFoundError();
        }
        unset($this->documents[$id]);
    }
};

$service = new Service($repository);

$created = $service->create('First Document');

if ($created->title() !== 'First Document') {
    $failures[] = 'create()는 전달한 title을 가진 document를 반환해야 한다.';
}
if ($created->id() === '') {
    $failures[] = 'create()는 비어있지 않은 id를 발급해야 한다.';
}

$fetched = $service->get($created->id());

if ($fetched === null || $fetched->id() !== $created->id()) {
    $failures[] = 'get()은 create()로 만든 document를 id로 조회해야 한다.';
}

if ($service->get('missing-id') !== null) {
    $failures[] = 'get()은 없는 id에 대해 null을 반환해야 한다.';
}

$first = $service->create('First');
$second = $service->create('Second');

if ($first->id() === $second->id()) {
    $failures[] = 'create()는 호출마다 서로 다른 id를 발급해야 한다.';
}

try {
    $service->create('   ');
    $failures[] = 'create()는 공백만 있는 title에 대해 EmptyTitleError를 던져야 한다.';
} catch (EmptyTitleError $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

try {
    $service->create('First Document');
    $failures[] = 'create()는 중복된 normalizedTitle에 대해 DuplicateNormalizedTitleError를 던져야 한다.';
} catch (DuplicateNormalizedTitleError $error) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

if ($failures !== []) {
    fwrite(STDERR, "Service 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Service 테스트 통과.\n");
exit(0);
