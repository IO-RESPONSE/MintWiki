# php/src/Modules/Acl

`MintWiki\Acl` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.acl` → PHP `MintWiki\Acl`). 대응하는 계약
manifest 는 `src/modules/acl/manifest.json` 이다.

- `Decision.php` (태스크 0408) — ACL 권한 검사 결과를 표현하는 불변
  value object. permission/allowed/reason/matchedRuleId 네 필드로 Python
  `Decision`(src/modules/acl/decision.py)과 계약을 맞춘다. 권한 평가
  로직(AclService)은 이후 태스크의 범위다.
