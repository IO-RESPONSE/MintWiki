# php/src/Modules/Document

`MintWiki\Document` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었으며, 실제 구현은 이 모듈의 PHP 포팅이 진행되는 이후 태스크에서
채워진다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.document` → PHP `MintWiki\Document`). 대응하는 계약
manifest 는 `src/modules/document/manifest.json` 이다.

## 클래스

- `Document.php` (0400, 0401) — Python `Document`(`src/modules/document/model.py`)와
  필드를 맞춘 불변 value object. `id`/`title`/`normalizedTitle`/
  `currentRevisionId` 네 필드를 두며, `normalizedTitle`은 `Title::normalize()`
  가 계산한다.
- `Title.php` (0401) — Python `normalize_title`(`src/modules/document/title.py`)
  과 동작을 맞춘 제목 정규화 유틸리티. 주변 공백을 제거하고 내부 공백을
  단일 공백으로 축소하며, 결과가 빈 문자열이면 `EmptyTitleError`를 던진다.
- `EmptyTitleError.php` (0401) — Python `EmptyTitleError`와 안정적인 error
  code(`docs/portable-exception-code-policy.md`)를 맞춘 예외.
  `EmptyTitleError::CODE`가 `document.empty_title`을 노출한다.
- `Repository.php` (0402) — Python `DocumentRepository`
  (`src/modules/document/repository.py`)와 메서드 계약을 맞춘 저장소
  인터페이스(port). `docs/repository-port-contracts.md`의 document
  섹션이 정본이다. 구현 없이 시그니처만 두며, `create`/`get`/
  `getByNormalizedTitle`/`update` 네 메서드를 선언한다. 실제 구현체는
  이후 태스크(0435 등)에서 추가된다.
- `InMemoryRepository.php` (0435) — Python `InMemoryDocumentRepository`
  (`src/modules/document/repository.py`)와 동작을 맞춘 `Repository`의
  메모리 기반 구현체. id -> `Document` 맵과 normalizedTitle -> id 맵을
  함께 유지해 `create()`가 중복된 normalizedTitle을
  `DuplicateNormalizedTitleError`로 거부하고, `update()`는 없는 id에
  `NotFoundError`를 던진다. DB 전 단계의 테스트/개발용이다.
- `DuplicateNormalizedTitleError.php` (0402) — Python
  `DuplicateNormalizedTitleError`와 안정적인 error code를 맞춘 예외.
  `DuplicateNormalizedTitleError::CODE`가 `document.duplicate_title`을
  노출한다. `Repository::create()`가 던질 수 있다.
- `NotFoundError.php` (0402) — Python `DocumentNotFoundError`와 안정적인
  error code를 맞춘 예외. `NotFoundError::CODE`가 `document.not_found`를
  노출한다. `Repository::update()`가 던질 수 있다. 클래스 이름은
  `docs/php-namespace-mapping.md`가 고정한 규칙대로 `MintWiki\Document`
  namespace 안의 중복 `Document` 접두어를 뺀 것이다.
- `Service.php` (0403) — Python `DocumentService`
  (`src/modules/document/service.py`)의 `create`/`get` 계약만 옮긴 서비스
  골격. `docs/service-method-contracts.md`의 document 섹션이 정본이며,
  나머지 공개 메서드(`get_by_title`, `get_current_revision_read_model`)는
  revision 포트가 아직 없어(0404/0405 이후) 이 태스크 범위에서 제외했다.
  `create()`는 title로 새 `Document`를 만들어 `Repository::create()`에
  위임하고(`source`를 이용한 첫 리비전 생성은 다루지 않는다),
  `get()`은 `Repository::get()`에 위임한다. 클래스 이름은 `Repository.php`와
  같은 이유로 중복 `Document` 접두어를 뺀 것이다.
