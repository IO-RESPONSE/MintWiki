# php/src/Modules/Acl

`MintWiki\Acl` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.acl` → PHP `MintWiki\Acl`). 대응하는 계약
manifest 는 `src/modules/acl/manifest.json` 이다.

- `Decision.php` (태스크 0408) — ACL 권한 검사 결과를 표현하는 불변
  value object. permission/allowed/reason/matchedRuleId 네 필드로 Python
  `Decision`(src/modules/acl/decision.py)과 계약을 맞춘다.
- `Permission.php`/`SubjectType.php`/`Effect.php`(태스크 0687) — Python
  `Permission`/`SubjectType`/`Effect`(src/modules/acl/permission.py,
  rule.py)와 값을 맞춘 enum.
- `Rule.php`/`EmptyRuleIdError.php`/`MissingSubjectIdError.php`(태스크
  0687) — 하나의 ACL 규칙을 표현하는 도메인 모델. Python
  `Rule`(src/modules/acl/rule.py)과 계약을 맞춘다.
- `DocumentAcl.php`/`EmptyDocumentIdError.php`(태스크 0687) — 문서 하나에
  결부된 규칙 목록. Python `DocumentAcl`(src/modules/acl/document_acl.py)과
  계약을 맞춘다.
- `NamespaceAclDefaults.php`(태스크 0687) — 네임스페이스별 기본 규칙
  저장/조회. Python
  `NamespaceAclDefaults`(src/modules/acl/namespace_defaults.py)와 계약을
  맞춘다.
- `DefaultPolicy.php`(태스크 0687) — `acl_namespace_rule`에 아직 규칙이
  없는 네임스페이스에 적용할 기본 정책(공개 읽기 허용/익명 편집 거부/로그인
  사용자 편집 허용). Python
  `default_policy`(src/modules/acl/default_policy.py)와 계약을 맞춘다.
- `AclService.php`(태스크 0687) — 문서별 규칙이 있으면 그것만, 없으면
  네임스페이스 기본값을 first-match-wins로 검사해 `Decision`을 만든다.
  Python `AclService`(src/modules/acl/service.py)와 계약을 맞춘다.
- `PdoRepository.php`(태스크 0687) — `db/schema/acl_rule.sql`/
  `acl_namespace_rule.sql`의 `acl_rule`/`acl_namespace_rule` 테이블을
  `sort_order` 순으로 읽어 `DocumentAcl`/`Rule[]`을 만든다. `GET
  /wiki/{title}`, `GET`/`POST /wiki/{title}/edit`이 이 규칙으로 현재
  사용자의 읽기/편집 권한을 확인한다(`public/index.php` 참고).
