<?php

declare(strict_types=1);

/**
 * `MintWiki\Revision\InMemoryRepository`가 Python
 * `InMemoryRevisionRepository`(tests/modules/revision/test_repository.py의
 * `TestInMemoryRevisionRepository`/`TestRevisionListingOrder`)와 같은
 * 시나리오에서 같은 결과를 내는지 확인하는 parity 테스트.
 * phpunit 없이 `php` CLI만으로 실행된다(Document/InMemoryRepositoryTest.php와
 * 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Revision\InMemoryRepository;
use MintWiki\Revision\Repository;
use MintWiki\Revision\Revision;

$failures = [];

if (!(new InMemoryRepository()) instanceof Repository) {
    $failures[] = 'InMemoryRepository는 Repository 인터페이스를 구현해야 한다.';
}

// test_can_create_revision / test_can_fetch_revision_by_id
$repository = new InMemoryRepository();
$revision = new Revision('rev1', 'doc1', 'Hello, World!', 'user1', 'Initial content');
$created = $repository->create($revision);
if (
    $created->id() !== 'rev1'
    || $created->documentId() !== 'doc1'
    || $created->source() !== 'Hello, World!'
    || $created->authorId() !== 'user1'
    || $created->summary() !== 'Initial content'
) {
    $failures[] = 'create()는 저장한 revision을 그대로 반환해야 한다.';
}
$fetched = $repository->get('rev1');
if ($fetched === null || $fetched->id() !== 'rev1' || $fetched->documentId() !== 'doc1') {
    $failures[] = 'get()은 create()로 저장한 revision을 id로 조회해야 한다.';
}

// test_returns_none_for_missing_id
if ($repository->get('nonexistent') !== null) {
    $failures[] = 'get()은 없는 id에 대해 null을 반환해야 한다.';
}

// test_can_list_revisions_for_document_in_creation_order
$repository = new InMemoryRepository();
$rev1 = $repository->create(new Revision('rev1', 'doc1', 'v1', 'user1', 'First revision'));
$rev2 = $repository->create(new Revision('rev2', 'doc1', 'v2', 'user2', 'Second revision', 'rev1'));
$rev3 = $repository->create(new Revision('rev3', 'doc1', 'v3', 'user1', 'Third revision', 'rev2'));
$listed = $repository->listByDocumentId('doc1');
if (count($listed) !== 3 || $listed[0] !== $rev1 || $listed[1] !== $rev2 || $listed[2] !== $rev3) {
    $failures[] = 'listByDocumentId()는 리비전을 생성 순서대로 반환해야 한다.';
}

// test_returns_empty_list_for_nonexistent_document
$repository = new InMemoryRepository();
if ($repository->listByDocumentId('nonexistent') !== []) {
    $failures[] = 'listByDocumentId()는 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

// test_can_store_multiple_revisions_for_different_documents
$repository = new InMemoryRepository();
$rev1Doc1 = $repository->create(new Revision('rev1_1', 'doc1', 'doc1_v1', 'user1', 'doc1 rev1'));
$rev1Doc2 = $repository->create(new Revision('rev1_2', 'doc2', 'doc2_v1', 'user1', 'doc2 rev1'));
$rev2Doc1 = $repository->create(new Revision('rev2_1', 'doc1', 'doc1_v2', 'user2', 'doc1 rev2', 'rev1_1'));
$doc1Revs = $repository->listByDocumentId('doc1');
$doc2Revs = $repository->listByDocumentId('doc2');
if (count($doc1Revs) !== 2 || $doc1Revs[0] !== $rev1Doc1 || $doc1Revs[1] !== $rev2Doc1) {
    $failures[] = 'listByDocumentId()는 doc1의 리비전만 순서대로 반환해야 한다.';
}
if (count($doc2Revs) !== 1 || $doc2Revs[0] !== $rev1Doc2) {
    $failures[] = 'listByDocumentId()는 doc2의 리비전만 순서대로 반환해야 한다.';
}

// test_preserves_revision_attributes
$repository = new InMemoryRepository();
$repository->create(new Revision('rev1', 'doc1', "Multi-line\ncontent\nhere", 'user1', 'Complex edit', 'rev0'));
$result = $repository->get('rev1');
if (
    $result === null
    || $result->id() !== 'rev1'
    || $result->documentId() !== 'doc1'
    || $result->source() !== "Multi-line\ncontent\nhere"
    || $result->authorId() !== 'user1'
    || $result->summary() !== 'Complex edit'
    || $result->parentRevisionId() !== 'rev0'
) {
    $failures[] = 'InMemoryRepository는 revision의 모든 속성을 보존해야 한다.';
}

// test_in_memory_repository_lists_in_insertion_order (5개)
$repository = new InMemoryRepository();
$expectedIds = [];
for ($i = 0; $i < 5; $i++) {
    $id = "rev{$i}";
    $repository->create(new Revision($id, 'doc1', "content {$i}", 'user1', "Revision {$i}"));
    $expectedIds[] = $id;
}
$listed = $repository->listByDocumentId('doc1');
$actualIds = array_map(fn (Revision $revision): string => $revision->id(), $listed);
if ($actualIds !== $expectedIds) {
    $failures[] = 'InMemoryRepository는 삽입 순서대로 리비전을 나열해야 한다.';
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
