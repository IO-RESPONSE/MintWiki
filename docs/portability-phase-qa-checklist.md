# Portability Phase (Phase A) QA Checklist

이 문서는 로드맵 **Phase A: PHP Replacement Contract, 0351-0390**
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`) 의 산출물 전체가
회귀 없이 유지되고 있는지 확인하기 위한 체크리스트다. Phase A에 속한
문서/스크립트/manifest/fixture를 새로 추가·수정한 뒤, 또는 커밋 전
`scripts/qa.sh`와는 별개로 "PHP로 1:1 교체 가능한 계약이 실제로 고정되어
있는가"를 사람이 다시 훑어볼 때 사용한다.

`docs/acl-phase-qa-checklist.md`와 동일한 형식을 따른다 — 각 항목은
"무엇을 확인하는가"와 "어떤 자동화가 이미 이를 커버하는가"를 함께 적는다.
자동화가 있다고 해서 항목을 건너뛰어도 된다는 뜻은 아니다.

## 사용법

```bash
.venv/bin/python scripts/check_module_manifests.py
.venv/bin/python scripts/check_boundaries.py
.venv/bin/python scripts/check_no_app_import_in_modules.py
.venv/bin/python scripts/check_contract_drift.py
.venv/bin/python -m pytest tests/modules -v
```

위 명령들로 아래 체크리스트가 참조하는 자동 검사를 한 번에 실행할 수
있다. 개별 실행 후에는 반드시 `scripts/test.sh`와 `scripts/qa.sh`도
통과해야 한다 — 이 체크리스트의 항목 대부분은 이미 `scripts/qa.sh`
안에 연결되어 있으므로, `scripts/qa.sh`가 통과하면 아래 1~3절은
사실상 자동으로 확인된다. 4절(문서 정합성)은 사람이 읽고 확인해야
하는 항목이 남아 있다.

## 1. Manifest 계약

- [ ] 12개 모듈(`document`, `revision`, `parser`, `render`, `acl`,
      `discussion`, `search`, `cache`, `jobs`, `user`, `admin`,
      `audit`, `docs/modules.md` 기준) 각각에
      `src/modules/<module>/manifest.json`이 존재한다. See
      `scripts/check_module_manifests.py`,
      `tests/test_check_module_manifests.py`.
- [ ] 모든 manifest가 `src/modules/module_manifest.schema.json`이
      요구하는 필수 필드(`schema_version`/`module`/`summary`/`port`/
      `service`/`repository`/`fixtures`)를 채우고 있다. See
      `tests/test_module_manifest_schema.py`,
      `docs/module-contract-manifest-schema.md`.
- [ ] 모듈별 manifest 테스트(`tests/modules/<module>/test_manifest.py`)
      가 그 모듈의 `port.status`, `service.public_methods`,
      `fixtures.path` 값이 실제 코드/디렉터리와 일치하는지 확인한다.
- [ ] Phase A 시점에는 모든 모듈의 `port.status`가 `not_started`다 —
      `docs/php-replacement-readiness-checklist.md`의 "Phase A 시점
      스냅샷" 표와 어긋나면 그 문서도 함께 갱신한다.

## 2. Fixture 계약

- [ ] 교차언어 fixture 파일은 `docs/fixture-directory-convention.md`가
      정한 두 위치(`tests/modules/<module>/fixtures/` 또는
      `tests/fixtures/`) 중 하나에만 존재한다.
- [ ] fixture 파일은 `docs/cross-language-fixture-schema.md`가 고정한
      `schema_version`/`input`/`expected`/`errors` 4개 최상위 필드
      구조를 따르며, `tests/fixtures/schema/cross_language_fixture.schema.json`
      기준으로 유효하다.
- [ ] document title/parser/render 등 fixture 기반으로 전환된 테스트가
      해당 디렉터리의 파일 전부를 통과한다. See
      `tests/modules/document/test_title_fixtures.py`,
      `tests/modules/acl/test_decision_code_fixtures.py`,
      `docs/php-parity-test-plan.md`("기준 패턴"으로 지목한 러너들).
- [ ] fixture의 `errors` 필드는 메시지 문자열이 아니라
      `docs/portable-exception-code-policy.md`가 정한
      `<module>.<reason>` 형식 코드이며, 러너는 코드만 비교한다(메시지
      문자열 비교 금지).

## 3. Boundary(경계) 검사

- [ ] 도메인 계층(`src/modules/**/model.py`, `service.py` 등)이
      `fastapi`/`starlette`/`sqlalchemy`/`pydantic`/`pydantic_settings`/
      `asyncpg`/`uvicorn`/`alembic`을 import하지 않는다 — 예외는
      `router.py`(fastapi만), `repository.py`(sqlalchemy만),
      `schema.py`(pydantic만)뿐이다. See `scripts/check_boundaries.py`.
- [ ] `src/modules/` 하위 어떤 파일도 `src/app`(UI/API 어댑터 부트스트랩
      계층)을 역참조하지 않는다. See
      `scripts/check_no_app_import_in_modules.py`.
- [ ] 위반이 있으면 종료 코드 1과 위반 목록이 출력되고, `scripts/qa.sh`
      전체가 실패한다 — 두 검사 모두 이미 `scripts/qa.sh`에 연결되어
      있다.

## 4. 문서(Docs) 정합성

- [ ] Phase A의 모든 정책 문서(`docs/portable-datetime-policy.md`,
      `docs/portable-id-policy.md`, `docs/portable-pagination-contract.md`,
      `docs/portable-sorting-contract.md`,
      `docs/portable-text-normalization-policy.md`,
      `docs/portable-exception-code-policy.md`,
      `docs/portable-exception-code-policy.md` 등)가
      `docs/portability-glossary.md`가 고정한 용어(Port/Adapter/
      Contract/Fixture)와 다른 의미로 같은 단어를 쓰지 않는다.
- [ ] `docs/php-namespace-mapping.md`의 Python 패키지 ↔ PHP namespace
      매핑이 `docs/modules.md`의 12개 모듈 목록과 1:1로 대응한다 —
      누락되거나 이름이 어긋난 모듈이 없다.
- [ ] `docs/php-parity-test-plan.md`의 parity 판정 기준(같은 fixture에
      대해 Python 러너와 PHP 러너 둘 다 통과)이
      `docs/php-replacement-readiness-checklist.md`의 Gate 3과 모순되지
      않는다.
- [ ] `docs/contract-drift-report.md`가 설명하는 `scripts/check_contract_drift.py`
      실행 결과가 실제로 종료 코드 0을 반환하고, `php/` 트리가 없는 동안
      모든 모듈이 `not_measurable`로 보고된다.
- [ ] 이 문서를 포함해 Phase A 문서들의 "관련 문서" 절이 가리키는 파일이
      실제로 존재한다(문서 간 링크 깨짐 없음).

## 이 체크리스트가 다루지 않는 것

- Phase B(PHP Runtime Skeleton, 0391-0440) 이후 실제 PHP 코드/러너의
  동작 검증 — `php/` 트리가 생긴 뒤 이 문서를 확장하거나 별도
  Phase B QA 체크리스트를 추가하는 것은 이후 태스크의 범위다.
- `docs/php-replacement-readiness-checklist.md`의 모듈별 ready/not-ready
  최신 판정 갱신 — 그 문서와 0433 module replacement matrix의 역할이며,
  이 체크리스트는 Phase A 산출물 자체의 무결성만 확인한다.
- 실제 배포 환경에서의 성능/부하 특성 — 이 체크리스트는 기능적
  정확성과 계약 정합성만 다룬다.

## 관련 문서

- `docs/acl-phase-qa-checklist.md` — 이 문서가 형식을 따른 선행 Phase
  QA 체크리스트.
- `docs/php-replacement-strategy.md` — Phase A 전체가 구체화하는 PHP
  전환 전략의 원본.
- `docs/module-contract-manifest-schema.md`,
  `docs/fixture-directory-convention.md`,
  `docs/cross-language-fixture-schema.md` — 1절/2절이 참조하는 계약
  형식.
- `docs/php-replacement-readiness-checklist.md`,
  `docs/php-parity-test-plan.md`,
  `docs/contract-drift-report.md` — 모듈별 준비도와 drift 판정의
  원본 문서.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase A(0351-0390)
  전체 태스크 목록.
