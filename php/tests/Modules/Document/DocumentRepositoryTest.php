<?php

declare(strict_types=1);

/**
 * MintWiki\Modules\Document\DocumentRepository의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 지금은 placeholder 구현 검증에 초점을 맞추고, 실제 SQL 실행은 0488 이후에
 * 구현된다. 이 테스트는 저장소 골격이 올바르게 만들어졌는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Modules\Document\Document;
use MintWiki\Modules\Document\DocumentRepository;
use MintWiki\Persistence\PdoTransaction;

$failures = [];

// in-memory sqlite 연결 생성 (테스트 용도)
$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

// Document 엔티티 생성
$doc = new Document(
    id: 'doc-001',
    title: 'Test Document',
    normalized_title: 'test document',
    current_revision_id: null,
);

// Document 엔티티 필드 검증
if ($doc->id !== 'doc-001') {
    $failures[] = 'Document id가 올바르게 설정되지 않았다.';
}
if ($doc->title !== 'Test Document') {
    $failures[] = 'Document title이 올바르게 설정되지 않았다.';
}
if ($doc->normalized_title !== 'test document') {
    $failures[] = 'Document normalized_title이 올바르게 설정되지 않았다.';
}
if ($doc->current_revision_id !== null) {
    $failures[] = 'Document current_revision_id가 null이어야 한다.';
}

// PdoTransaction 생성
$transaction = new PdoTransaction($connection);

// DocumentRepository 생성
$repository = new DocumentRepository($transaction, $connection);

// create() 메서드 반환값 검증 (placeholder)
$created = $repository->create($doc);
if ($created->id !== 'doc-001') {
    $failures[] = 'create()가 반환한 문서의 id가 올바르지 않다.';
}
if ($created->title !== 'Test Document') {
    $failures[] = 'create()가 반환한 문서의 title이 올바르지 않다.';
}

// get() 메서드 검증 (placeholder: null 반환)
$retrieved = $repository->get('doc-001');
if ($retrieved !== null) {
    $failures[] = 'get()이 null을 반환해야 한다 (placeholder 구현).';
}

// getByNormalizedTitle() 메서드 검증 (placeholder: null 반환)
$retrieved_by_title = $repository->getByNormalizedTitle('test document');
if ($retrieved_by_title !== null) {
    $failures[] = 'getByNormalizedTitle()이 null을 반환해야 한다 (placeholder 구현).';
}

// update() 메서드 반환값 검증 (placeholder)
$updated = $repository->update($doc);
if ($updated->id !== 'doc-001') {
    $failures[] = 'update()가 반환한 문서의 id가 올바르지 않다.';
}

if ($failures !== []) {
    fwrite(STDERR, "DocumentRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "DocumentRepository 테스트 통과.\n");
exit(0);
