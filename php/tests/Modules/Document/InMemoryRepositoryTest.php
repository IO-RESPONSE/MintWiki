<?php

declare(strict_types=1);

/**
 * `MintWiki\Document\InMemoryRepository`가 Python
 * `InMemoryDocumentRepository`(tests/modules/document/test_repository.py의
 * `TestInMemoryDocumentRepository`/`TestInMemoryDocumentRepositoryUpdate`)와
 * 같은 시나리오에서 같은 결과를 내는지 확인하는 parity 테스트.
 * phpunit 없이 `php` CLI만으로 실행된다(0402 RepositoryTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\InMemoryRepository;
use MintWiki\Document\NotFoundError;
use MintWiki\Document\Repository;

$failures = [];

if (!(new InMemoryRepository()) instanceof Repository) {
    $failures[] = 'InMemoryRepository는 Repository 인터페이스를 구현해야 한다.';
}

// test_can_create_document / test_can_fetch_document_by_id
$repository = new InMemoryRepository();
$created = $repository->create(new Document('doc1', 'Test Document'));
if ($created->id() !== 'doc1' || $created->title() !== 'Test Document') {
    $failures[] = 'create()는 저장한 document를 그대로 반환해야 한다.';
}
$fetched = $repository->get('doc1');
if ($fetched === null || $fetched->id() !== 'doc1' || $fetched->title() !== 'Test Document') {
    $failures[] = 'get()은 create()로 저장한 document를 id로 조회해야 한다.';
}

// test_returns_none_for_missing_id
if ($repository->get('nonexistent') !== null) {
    $failures[] = 'get()은 없는 id에 대해 null을 반환해야 한다.';
}

// test_can_fetch_document_by_normalized_title
$byTitle = $repository->getByNormalizedTitle('Test Document');
if ($byTitle === null || $byTitle->id() !== 'doc1') {
    $failures[] = 'getByNormalizedTitle()은 정규화된 제목으로 document를 조회해야 한다.';
}

// test_can_fetch_document_by_normalized_title_with_spaces
$repository = new InMemoryRepository();
$repository->create(new Document('doc1', '  Test   Document  '));
$byTitle = $repository->getByNormalizedTitle('Test Document');
if ($byTitle === null || $byTitle->id() !== 'doc1') {
    $failures[] = 'getByNormalizedTitle()은 공백이 다른 제목도 정규화하여 조회해야 한다.';
}

// test_returns_none_for_missing_normalized_title
$repository = new InMemoryRepository();
if ($repository->getByNormalizedTitle('Nonexistent Title') !== null) {
    $failures[] = 'getByNormalizedTitle()은 없는 정규화된 제목에 대해 null을 반환해야 한다.';
}

// test_rejects_duplicate_normalized_title
$repository = new InMemoryRepository();
$repository->create(new Document('doc1', 'Test Document'));
try {
    $repository->create(new Document('doc2', 'Test Document'));
    $failures[] = 'create()는 중복된 normalizedTitle에 대해 DuplicateNormalizedTitleError를 던져야 한다.';
} catch (DuplicateNormalizedTitleError $error) {
    // 정상 경로.
}

// test_rejects_duplicate_normalized_title_with_different_spaces
$repository = new InMemoryRepository();
$repository->create(new Document('doc1', 'Test Document'));
try {
    $repository->create(new Document('doc2', '  Test   Document  '));
    $failures[] = 'create()는 공백만 다른 중복 title도 DuplicateNormalizedTitleError로 감지해야 한다.';
} catch (DuplicateNormalizedTitleError $error) {
    // 정상 경로.
}

// test_stores_multiple_documents
$repository = new InMemoryRepository();
$repository->create(new Document('doc1', 'Document One'));
$repository->create(new Document('doc2', 'Document Two'));
$repository->create(new Document('doc3', 'Document Three'));
if ($repository->get('doc1') === null || $repository->get('doc2') === null || $repository->get('doc3') === null) {
    $failures[] = 'InMemoryRepository는 여러 document를 저장할 수 있어야 한다.';
}
if (
    $repository->getByNormalizedTitle('Document One') === null
    || $repository->getByNormalizedTitle('Document Two') === null
    || $repository->getByNormalizedTitle('Document Three') === null
) {
    $failures[] = '여러 document 모두 normalizedTitle로 조회할 수 있어야 한다.';
}

// test_update_existing_document
$repository = new InMemoryRepository();
$repository->create(new Document('doc1', 'Original Title'));
$updated = $repository->update(new Document('doc1', 'Original Title', 'rev1'));
if ($updated->currentRevisionId() !== 'rev1') {
    $failures[] = 'update()는 currentRevisionId를 갱신해야 한다.';
}
$reloaded = $repository->get('doc1');
if ($reloaded === null || $reloaded->currentRevisionId() !== 'rev1') {
    $failures[] = 'update() 결과는 get()으로 재조회해도 유지되어야 한다.';
}

// test_update_nonexistent_document_raises_error
$repository = new InMemoryRepository();
try {
    $repository->update(new Document('nonexistent', 'Test Document'));
    $failures[] = 'update()는 없는 id에 대해 NotFoundError를 던져야 한다.';
} catch (NotFoundError $error) {
    // 정상 경로.
}

if ($failures !== []) {
    fwrite(STDERR, "InMemoryRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InMemoryRepository 테스트 통과.\n");
exit(0);
