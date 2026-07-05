<?php

declare(strict_types=1);

/**
 * `MintWiki\Document\Service::create()`/`get()`이 Python
 * `DocumentService`(tests/modules/document/test_service.py의
 * `TestDocumentService`)와 같은 시나리오에서 같은 결과를 내는지 확인하는
 * parity 테스트(`docs/php-parity-test-plan.md`의 0434 항목).
 *
 * `ServiceTest.php`(0403)는 create/get 계약 자체(빈 title 예외, 중복 제목
 * 예외, id 발급)만 손으로 검증했다. 이 파일은 그 위에 Python 쪽 개별
 * 테스트 메서드 이름을 주석으로 나란히 적어, 두 언어의 시나리오가
 * 1:1로 대응하는지 추적 가능하게 하고, `ServiceTest.php`가 다루지 않은
 * `normalizedTitle`/`currentRevisionId` 필드도 함께 검증한다.
 *
 * document 모듈에는 create/get을 겨냥한 공유 JSON fixture
 * (`tests/modules/document/fixtures/`)가 없다 — 그 디렉터리는 Title
 * 정규화 시나리오 전용이다(TitleFixtureRunnerTest.php 참고). 그래서 이
 * 테스트는 TitleFixtureRunnerTest.php처럼 fixture 파일을 읽는 대신,
 * Python `test_service.py`의 어서션을 PHP로 그대로 옮겨 적는다.
 *
 * `get_by_title`/`get_current_revision_read_model`/`source` 파라미터는
 * revision 포트가 아직 없어(0404/0405) `Service.php`의 범위 밖이므로
 * 이 테스트도 다루지 않는다 — `ServiceTest.php`와 같은 제약이다.
 *
 * `InMemoryDocumentRepository` PHP 클래스는 아직 없다(0435가 추가한다).
 * `RepositoryTest.php`/`ServiceTest.php`와 마찬가지로 `Repository`
 * 인터페이스를 구현하는 익명 클래스로 대신한다.
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

/**
 * 매 시나리오가 독립된 저장소/서비스 쌍을 갖도록 하는 factory.
 * Python 쪽 각 테스트 메서드가 `InMemoryDocumentRepository()`를 새로
 * 만드는 것과 같은 격리를 재현한다.
 */
function makeService(): Service
{
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

    return new Service($repository);
}

$failures = [];

// test_create_document_with_title
$service = makeService();
$doc = $service->create('My Document');
if ($doc->id() === '') {
    $failures[] = 'create()는 비어있지 않은 id를 발급해야 한다.';
}
if ($doc->title() !== 'My Document') {
    $failures[] = "create()는 title을 그대로 보존해야 한다.";
}
if ($doc->normalizedTitle() !== 'My Document') {
    $failures[] = "create()는 이미 정규화된 title에 대해 normalizedTitle이 같아야 한다.";
}
if ($doc->currentRevisionId() !== null) {
    $failures[] = 'source 없이 create()하면 currentRevisionId는 null이어야 한다.';
}

// test_create_normalizes_title
$service = makeService();
$doc = $service->create('  My   Document  ');
if ($doc->title() !== '  My   Document  ') {
    $failures[] = 'create()는 원본 title 문자열을 그대로 보존해야 한다(정규화하지 않음).';
}
if ($doc->normalizedTitle() !== 'My Document') {
    $failures[] = "normalizedTitle은 공백을 트림/축소해야 한다. 실제: " . var_export($doc->normalizedTitle(), true);
}

// test_create_generates_unique_id
$service = makeService();
$doc1 = $service->create('Document One');
$doc2 = $service->create('Document Two');
if ($doc1->id() === $doc2->id()) {
    $failures[] = 'create()는 호출마다 서로 다른 id를 발급해야 한다.';
}

// test_create_delegates_to_repository / test_get_document_by_id
$service = makeService();
$doc = $service->create('My Document');
$retrieved = $service->get($doc->id());
if ($retrieved === null || $retrieved->title() !== 'My Document') {
    $failures[] = 'get()은 create()로 저장한 document를 id로 조회해야 한다.';
}

// test_create_raises_on_empty_title
$service = makeService();
try {
    $service->create('');
    $failures[] = 'create()는 빈 title에 대해 EmptyTitleError를 던져야 한다.';
} catch (EmptyTitleError $error) {
    // 정상 경로.
}

// test_create_raises_on_whitespace_only_title
$service = makeService();
try {
    $service->create('   ');
    $failures[] = 'create()는 공백만 있는 title에 대해 EmptyTitleError를 던져야 한다.';
} catch (EmptyTitleError $error) {
    // 정상 경로.
}

// test_create_raises_on_duplicate_normalized_title
$service = makeService();
$service->create('My Document');
try {
    $service->create('My Document');
    $failures[] = 'create()는 중복된 normalizedTitle에 대해 DuplicateNormalizedTitleError를 던져야 한다.';
} catch (DuplicateNormalizedTitleError $error) {
    // 정상 경로.
}

// test_create_raises_on_duplicate_normalized_title_with_spaces
$service = makeService();
$service->create('My Document');
try {
    $service->create('  My   Document  ');
    $failures[] = 'create()는 공백만 다른 중복 title도 DuplicateNormalizedTitleError로 감지해야 한다.';
} catch (DuplicateNormalizedTitleError $error) {
    // 정상 경로.
}

// test_create_allows_different_normalized_titles
$service = makeService();
$doc1 = $service->create('Document One');
$doc2 = $service->create('Document Two');
if ($doc1->normalizedTitle() === $doc2->normalizedTitle()) {
    $failures[] = 'normalizedTitle이 다른 title은 함께 생성될 수 있어야 한다.';
}
if ($service->get($doc1->id()) === null || $service->get($doc2->id()) === null) {
    $failures[] = '서로 다른 두 document 모두 get()으로 조회할 수 있어야 한다.';
}

// test_get_document_by_id_not_found
$service = makeService();
if ($service->get('nonexistent-id') !== null) {
    $failures[] = 'get()은 존재하지 않는 id에 대해 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Document Service Parity 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Document Service Parity 테스트 통과.\n");
exit(0);
