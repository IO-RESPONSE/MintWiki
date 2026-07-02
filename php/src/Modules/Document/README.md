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
