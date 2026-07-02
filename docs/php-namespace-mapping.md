# Python to PHP Namespace Mapping

이 문서는 `docs/php-replacement-strategy.md` 가 정의한 모듈 단위 1:1 교체
원칙을 따라, Python 패키지(`src/modules/<module>`)를 PHP namespace 로
옮길 때 쓰는 이름 규칙을 고정한다. Phase A: PHP Replacement Contract,
0351-0390 의 산출물이며, 각 모듈 manifest(`src/modules/<module>/manifest.json`)
의 `port.target_namespace` 필드가 이 문서가 정의하는 후보값에서 정식
값으로 확정되었음을 표시한다.

## 이름 규칙

Python import 경로 `modules.<module>` 은 PHP namespace
`MintWiki\<Module>` 로 옮긴다.

- `<module>` 은 `src/modules/<module>` 디렉터리 이름(소문자, snake_case)
  이며, `<Module>` 은 그 이름을 PascalCase 로 바꾼 것이다. 이 저장소의
  모듈 이름은 모두 단일 단어(`document`, `acl` 등)이므로 PascalCase 변환은
  첫 글자만 대문자로 바꾸는 것과 같다.
- 최상위 접두사는 항상 `MintWiki` 로 고정한다. 이 값은 임의의 벤더/앱
  이름이 아니라 이 프로젝트가 선택한 단일 루트 namespace 다 — 모듈마다
  다른 접두사를 쓰지 않는다.
- 모듈 내부 파일(`service.py`, `repository.py`, `model.py` 등)은 PHP
  쪽에서 `MintWiki\<Module>\<ClassName>` 형태의 클래스로 대응시킨다.
  파일 이름이 아니라 그 파일이 정의하는 공개 클래스 이름을 기준으로
  PascalCase 서브 namespace 또는 클래스 이름을 붙인다.
- 대표 예시(Notes 에서 고정한 값): Python `modules.document.service` 의
  `DocumentService` 클래스는 PHP `MintWiki\Document\Service` 로 옮긴다.
  즉 Python 모듈 경로의 마지막 세그먼트(`service`)는 PHP 쪽 클래스 이름
  (`Service`)이 되고, 그 클래스가 속한 namespace 는 `MintWiki\<Module>`
  이다 — Python 파일 경로 세그먼트를 그대로 PHP namespace 세그먼트로
  누적하지 않는다.

## 모듈별 매핑 표

아래 표는 `docs/modules.md` 가 정의한 12개 모듈과 각 모듈 manifest 의
`port.target_namespace` 값을 그대로 옮긴 것이다. manifest 가 이 매핑의
정본(source of truth)이며, 이 표는 사람이 한눈에 보기 위한 요약이다 —
값이 어긋나면 manifest 를 기준으로 이 표를 고친다.

| Python 패키지 (`modules.<module>`) | PHP namespace | manifest 경로 |
|---|---|---|
| `modules.document` | `MintWiki\Document` | `src/modules/document/manifest.json` |
| `modules.revision` | `MintWiki\Revision` | `src/modules/revision/manifest.json` |
| `modules.parser` | `MintWiki\Parser` | `src/modules/parser/manifest.json` |
| `modules.render` | `MintWiki\Render` | `src/modules/render/manifest.json` |
| `modules.acl` | `MintWiki\Acl` | `src/modules/acl/manifest.json` |
| `modules.discussion` | `MintWiki\Discussion` | `src/modules/discussion/manifest.json` |
| `modules.search` | `MintWiki\Search` | `src/modules/search/manifest.json` |
| `modules.cache` | `MintWiki\Cache` | `src/modules/cache/manifest.json` |
| `modules.jobs` | `MintWiki\Jobs` | `src/modules/jobs/manifest.json` |
| `modules.user` | `MintWiki\User` | `src/modules/user/manifest.json` |
| `modules.admin` | `MintWiki\Admin` | `src/modules/admin/manifest.json` |
| `modules.audit` | `MintWiki\Audit` | `src/modules/audit/manifest.json` |

예시 확장 (서비스 클래스 수준):

| Python | PHP |
|---|---|
| `modules.document.service` (`DocumentService`) | `MintWiki\Document\Service` |
| `modules.acl.service` (`AclService`) | `MintWiki\Acl\Service` |
| `modules.user.block_check_service` (`BlockCheckService`) | `MintWiki\User\BlockCheckService` |

`user` 모듈의 `service.path` 는 `block_check_service.py` 를 가리키지만
(`docs/module-contract-manifest-schema.md` 의 필드 설명 참고), namespace
매핑 규칙 자체는 바뀌지 않는다 — 파일 이름이 무엇이든 최상위 namespace 는
여전히 `MintWiki\User` 다.

## 이 규칙이 적용되지 않는 범위

- `src/app`(부트스트랩) 계층은 모듈이 아니므로 이 매핑 대상이 아니다.
  PHP 쪽 애플리케이션 부트스트랩 namespace 는 이후 별도 태스크가 정한다.
- `manifest.json` 의 `port.status` 가 `not_started` 인 모듈도 이 문서의
  namespace 값은 확정값으로 취급한다 — namespace 확정과 실제 포팅 착수
  여부(`status`)는 별개다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 모듈 단위 1:1 교체 원칙과 readiness
  gate.
- `docs/portability-glossary.md` — Port/Adapter/Contract 용어 정의.
- `docs/module-contract-manifest-schema.md` — `port.target_namespace`
  필드가 정의된 manifest 스키마.
- `docs/modules.md` — 이 문서가 매핑하는 12개 모듈의 책임 목록.
