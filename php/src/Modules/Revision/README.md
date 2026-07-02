# php/src/Modules/Revision

`MintWiki\Revision` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었으며, 실제 구현은 이 모듈의 PHP 포팅이 진행되는 이후 태스크에서
채워진다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.revision` → PHP `MintWiki\Revision`). 대응하는 계약
manifest 는 `src/modules/revision/manifest.json` 이다.

## 클래스

- `Revision.php` (0404) — Python `Revision`(`src/modules/revision/model.py`)와
  필드를 맞춘 불변 value object. `id`/`documentId`/`source`/`authorId`/
  `summary`/`parentRevisionId` 여섯 필드를 두며, `parentRevisionId`는 첫
  리비전의 경우 `null`이다. Document의 `Title`과 달리 정규화 로직은 없다.
- `Repository.php` (0405) — Python `RevisionRepository`
  (`src/modules/revision/repository.py`)와 메서드 계약을 맞춘 저장소
  인터페이스(port). `docs/repository-port-contracts.md`의 revision
  섹션이 정본이다. 구현 없이 시그니처만 두며, `create`/`get`/
  `listByDocumentId` 세 메서드를 선언한다. 리비전은 append-only이므로
  Document\Repository와 달리 `update`/`delete`가 없다. 실제 구현체는
  이후 태스크(0436 등)에서 추가된다.
- `InMemoryRepository.php` (0436) — Python `InMemoryRevisionRepository`
  (`src/modules/revision/repository.py`)와 동작을 맞춘 `Repository`의
  메모리 기반 구현체. id -> `Revision` 맵과 documentId -> id 목록 맵을
  함께 유지해 `listByDocumentId()`가 생성 순서를 보존한다. append-only
  계약에 맞춰 `update`는 두지 않는다. DB 전 단계의 문서/리비전 통합
  테스트용이다.
