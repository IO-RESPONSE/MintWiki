# php/src/Modules/Document

`MintWiki\Document` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었으며, 실제 구현은 이 모듈의 PHP 포팅이 진행되는 이후 태스크에서
채워진다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.document` → PHP `MintWiki\Document`). 대응하는 계약
manifest 는 `src/modules/document/manifest.json` 이다.

## 클래스

- `Document.php` (0400) — Python `Document`(`src/modules/document/model.py`)와
  필드를 맞춘 불변 value object. `id`/`title`/`normalizedTitle`/
  `currentRevisionId` 네 필드를 두되, `normalizedTitle`은 현재 `title`을
  그대로 복사하는 임시 동작이다 — 실제 정규화 규칙은 0401(PHP 제목
  정규화기 추가)에서 연결된다.
