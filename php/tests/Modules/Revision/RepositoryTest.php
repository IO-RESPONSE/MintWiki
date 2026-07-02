<?php

declare(strict_types=1);

/**
 * MintWiki\Revision\Repository 포트의 시그니처와 계약을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0402 Document/RepositoryTest.php와
 * 동일한 방식).
 *
 * 태스크 0405는 구현 없이 port만 추가하므로, 이 테스트는 실제 저장소
 * 동작이 아니라 (1) 인터페이스가 계약대로 구현 가능한지 — 익명 클래스로
 * 구현해 본다 — 와 (2) listByDocumentId가 생성 순서를 유지하는지만
 * 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Revision\Repository;
use MintWiki\Revision\Revision;

$failures = [];

if (!interface_exists(Repository::class)) {
    $failures[] = 'MintWiki\\Revision\\Repository는 interface여야 한다.';
}

$repository = new class implements Repository {
    /** @var array<string, Revision> */
    private array $revisions = [];

    /** @var array<string, string[]> */
    private array $revisionIdsByDocumentId = [];

    public function create(Revision $revision): Revision
    {
        $this->revisions[$revision->id()] = $revision;
        $this->revisionIdsByDocumentId[$revision->documentId()][] = $revision->id();
        return $revision;
    }

    public function get(string $id): ?Revision
    {
        return $this->revisions[$id] ?? null;
    }

    public function listByDocumentId(string $documentId): array
    {
        $ids = $this->revisionIdsByDocumentId[$documentId] ?? [];
        return array_map(fn (string $id): Revision => $this->revisions[$id], $ids);
    }
};

$first = $repository->create(new Revision('rev-1', 'doc-1', 'Hello', 'user-1', 'Initial'));
if ($first->id() !== 'rev-1') {
    $failures[] = 'create()는 저장한 revision을 반환해야 한다.';
}
if ($repository->get('rev-1') === null) {
    $failures[] = 'get()은 create()로 저장한 revision을 조회해야 한다.';
}
if ($repository->get('missing') !== null) {
    $failures[] = 'get()은 없는 id에 대해 null을 반환해야 한다.';
}

$second = $repository->create(new Revision('rev-2', 'doc-1', 'Hello, updated', 'user-2', 'Second edit', 'rev-1'));
$repository->create(new Revision('rev-3', 'doc-2', 'Unrelated document', 'user-1', 'Other doc'));

$byDocument = $repository->listByDocumentId('doc-1');
if (count($byDocument) !== 2) {
    $failures[] = 'listByDocumentId()는 해당 문서의 리비전만 반환해야 한다.';
}
if (($byDocument[0] ?? null) !== $first || ($byDocument[1] ?? null) !== $second) {
    $failures[] = 'listByDocumentId()는 생성 순서대로 리비전을 반환해야 한다.';
}
if ($repository->listByDocumentId('missing-doc') !== []) {
    $failures[] = 'listByDocumentId()는 리비전이 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Repository 포트 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Repository 포트 테스트 통과.\n");
exit(0);
