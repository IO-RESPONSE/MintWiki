<?php

declare(strict_types=1);

/**
 * MintWiki\Modules\Revision\RevisionRepository의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 지금은 placeholder 구현 검증에 초점을 맞추고, 실제 SQL 실행은 이후 태스크에서
 * 구현된다. 이 테스트는 저장소 골격이 올바르게 만들어졌는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Modules\Revision\Revision;
use MintWiki\Modules\Revision\RevisionRepository;
use MintWiki\Persistence\PdoTransaction;

$failures = [];

// in-memory sqlite 연결 생성 (테스트 용도)
$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

// Revision 엔티티 생성
$revision = new Revision(
    id: 'rev-001',
    document_id: 'doc-001',
    source: '# Test Document\n\nThis is a test.',
    author_id: 'author-001',
    summary: 'Initial revision',
    parent_revision_id: null,
);

// Revision 엔티티 필드 검증
if ($revision->id !== 'rev-001') {
    $failures[] = 'Revision id가 올바르게 설정되지 않았다.';
}
if ($revision->document_id !== 'doc-001') {
    $failures[] = 'Revision document_id가 올바르게 설정되지 않았다.';
}
if ($revision->source !== '# Test Document\n\nThis is a test.') {
    $failures[] = 'Revision source가 올바르게 설정되지 않았다.';
}
if ($revision->author_id !== 'author-001') {
    $failures[] = 'Revision author_id가 올바르게 설정되지 않았다.';
}
if ($revision->summary !== 'Initial revision') {
    $failures[] = 'Revision summary가 올바르게 설정되지 않았다.';
}
if ($revision->parent_revision_id !== null) {
    $failures[] = 'Revision parent_revision_id가 null이어야 한다.';
}

// PdoTransaction 생성
$transaction = new PdoTransaction($connection);

// RevisionRepository 생성
$repository = new RevisionRepository($transaction, $connection);

// create() 메서드 반환값 검증 (placeholder)
$created = $repository->create($revision);
if ($created->id !== 'rev-001') {
    $failures[] = 'create()가 반환한 리비전의 id가 올바르지 않다.';
}
if ($created->document_id !== 'doc-001') {
    $failures[] = 'create()가 반환한 리비전의 document_id가 올바르지 않다.';
}
if ($created->source !== '# Test Document\n\nThis is a test.') {
    $failures[] = 'create()가 반환한 리비전의 source가 올바르지 않다.';
}

// get() 메서드 검증 (placeholder: null 반환)
$retrieved = $repository->get('rev-001');
if ($retrieved !== null) {
    $failures[] = 'get()이 null을 반환해야 한다 (placeholder 구현).';
}

// listByDocumentId() 메서드 검증 (placeholder: 빈 배열 반환)
$list = $repository->listByDocumentId('doc-001');
if ($list !== []) {
    $failures[] = 'listByDocumentId()이 빈 배열을 반환해야 한다 (placeholder 구현).';
}

// 다른 문서의 리비전 생성
$revision2 = new Revision(
    id: 'rev-002',
    document_id: 'doc-002',
    source: 'Different document',
    author_id: 'author-002',
    summary: 'Another document',
);

// 다른 문서의 리비전 생성 및 listByDocumentId() 검증
$created2 = $repository->create($revision2);
$list_doc001 = $repository->listByDocumentId('doc-001');
$list_doc002 = $repository->listByDocumentId('doc-002');

if ($list_doc001 !== []) {
    $failures[] = 'listByDocumentId("doc-001")이 빈 배열을 반환해야 한다 (placeholder 구현).';
}
if ($list_doc002 !== []) {
    $failures[] = 'listByDocumentId("doc-002")이 빈 배열을 반환해야 한다 (placeholder 구현).';
}

if ($failures !== []) {
    fwrite(STDERR, "RevisionRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "RevisionRepository 테스트 통과.\n");
exit(0);
