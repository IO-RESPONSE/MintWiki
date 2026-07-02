<?php

declare(strict_types=1);

/**
 * `MintWiki\Document`와 `MintWiki\Revision`을 함께 구성했을 때, `source`가
 * 문서의 첫 리비전으로 정상 연결되는지 확인하는 통합 테스트 (태스크 0437).
 *
 * `Document\Service::create()`는 아직 `source` 파라미터를 받지 않는다
 * (`Service.php`의 0403 주석 — revision 연동은 이후 태스크에서 서비스 계층에
 * 배선된다). 이 테스트는 그 배선이 만족해야 할 계약을 `Document\Repository`
 * (0435 `InMemoryRepository`)와 `Revision\Repository`(0436
 * `InMemoryRepository`)를 애플리케이션 레벨에서 직접 조합해 미리 검증한다:
 * 문서 생성 후 `source`로 첫 리비전을 만들고, 그 리비전 id로 문서를
 * `update()`하면 `currentRevisionId`가 연결되고, 리비전은 `parentRevisionId`가
 * `null`인 "첫 리비전"으로 조회되어야 한다.
 *
 * phpunit 없이 `php` CLI만으로 실행된다(다른 Modules/Document 테스트와 동일한
 * 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Document\InMemoryRepository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Revision\InMemoryRepository as RevisionRepository;
use MintWiki\Revision\Revision;

$failures = [];

$documentRepository = new DocumentRepository();
$documentService = new DocumentService($documentRepository);
$revisionRepository = new RevisionRepository();

// source가 첫 리비전으로 연결되는지 검증한다.
$document = $documentService->create('Integration Document');
if ($document->currentRevisionId() !== null) {
    $failures[] = 'source 없이 create()한 직후에는 currentRevisionId가 null이어야 한다.';
}

$firstRevision = $revisionRepository->create(
    new Revision('rev-1', $document->id(), 'Initial source content', '', '')
);

$documentWithFirstRevision = $documentRepository->update(
    new Document($document->id(), $document->title(), $firstRevision->id())
);

if ($documentWithFirstRevision->currentRevisionId() !== $firstRevision->id()) {
    $failures[] = 'update()로 연결한 뒤 currentRevisionId는 첫 리비전의 id여야 한다.';
}
if ($documentRepository->get($document->id())?->currentRevisionId() !== $firstRevision->id()) {
    $failures[] = '저장소에서 다시 조회한 document도 첫 리비전으로 연결되어 있어야 한다.';
}
if ($firstRevision->documentId() !== $document->id()) {
    $failures[] = '첫 리비전의 documentId는 연결된 document의 id와 같아야 한다.';
}
if ($firstRevision->parentRevisionId() !== null) {
    $failures[] = '첫 리비전은 parentRevisionId가 null이어야 한다.';
}
if ($revisionRepository->get($firstRevision->id())?->source() !== 'Initial source content') {
    $failures[] = '리비전 저장소에서 조회한 첫 리비전의 source가 보존되어야 한다.';
}
$listedAfterFirst = $revisionRepository->listByDocumentId($document->id());
if (count($listedAfterFirst) !== 1 || $listedAfterFirst[0] !== $firstRevision) {
    $failures[] = 'listByDocumentId()는 첫 리비전 하나만 반환해야 한다.';
}

// 두 번째 리비전(수정)을 추가해도 첫 리비전과의 이력이 유지되는지 확인한다.
$secondRevision = $revisionRepository->create(
    new Revision('rev-2', $document->id(), 'Edited content', '', '', $firstRevision->id())
);

$documentWithSecondRevision = $documentRepository->update(
    new Document($document->id(), $document->title(), $secondRevision->id())
);

if ($documentWithSecondRevision->currentRevisionId() !== $secondRevision->id()) {
    $failures[] = '두 번째 리비전 연결 후 currentRevisionId는 최신 리비전의 id여야 한다.';
}
if ($secondRevision->parentRevisionId() !== $firstRevision->id()) {
    $failures[] = '두 번째 리비전의 parentRevisionId는 첫 리비전의 id를 가리켜야 한다.';
}
$listedAfterSecond = $revisionRepository->listByDocumentId($document->id());
if (
    count($listedAfterSecond) !== 2
    || $listedAfterSecond[0] !== $firstRevision
    || $listedAfterSecond[1] !== $secondRevision
) {
    $failures[] = 'listByDocumentId()는 첫 리비전과 두 번째 리비전을 생성 순서대로 반환해야 한다.';
}
if ($revisionRepository->get($firstRevision->id())?->source() !== 'Initial source content') {
    $failures[] = '두 번째 리비전을 추가해도 첫 리비전의 source는 그대로 남아 있어야 한다.';
}

// 다른 document의 리비전과 섞이지 않는지 확인한다.
$otherDocument = $documentService->create('Other Document');
$otherRevision = $revisionRepository->create(
    new Revision('rev-other-1', $otherDocument->id(), 'Other document source', '', '')
);
$documentRepository->update(
    new Document($otherDocument->id(), $otherDocument->title(), $otherRevision->id())
);

if ($documentRepository->get($document->id())?->currentRevisionId() !== $secondRevision->id()) {
    $failures[] = '다른 document를 갱신해도 첫 document의 currentRevisionId는 영향받지 않아야 한다.';
}
$otherListed = $revisionRepository->listByDocumentId($otherDocument->id());
if (count($otherListed) !== 1 || $otherListed[0] !== $otherRevision) {
    $failures[] = 'listByDocumentId()는 다른 document의 리비전과 섞이지 않아야 한다.';
}
$originalListed = $revisionRepository->listByDocumentId($document->id());
if (count($originalListed) !== 2) {
    $failures[] = '다른 document의 리비전 생성이 원래 document의 리비전 목록을 오염시키면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Document/Revision Integration 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Document/Revision Integration 테스트 통과.\n");
exit(0);
