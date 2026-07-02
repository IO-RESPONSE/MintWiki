# Contract Drift Report (Placeholder)

이 문서는 Python 모듈 계약(manifest)과 PHP 구현 사이의 **drift(계약
불일치)** 를 보고하는 리포트의 골격을 고정한다. Phase A: PHP Replacement
Contract, 0351-0390 의 산출물이다.

이 태스크는 리포트의 **형식과 실행 방법만** 고정하는 placeholder 다 —
`php/` 트리 자체가 아직 존재하지 않는 시점(Phase A/B, 0351-0440)이므로
실제 drift 비교 로직은 만들지 않는다.

## Contract drift 정의

**Contract drift** 는 `src/modules/<module>/manifest.json` (정본,
`docs/module-contract-manifest-schema.md` 참고)이 선언한 내용과, 실제
PHP 구현이 어긋나는 상태를 가리킨다. 예:

- manifest 의 `service.public_methods` 에 나열된 메서드가 PHP
  `MintWiki\<Module>\Service` (`docs/php-namespace-mapping.md` 의
  네이밍 규칙)에 존재하지 않는다.
- manifest 의 `port.status` 가 `ready` 인데 해당 모듈의 PHP 구현이
  `docs/php-parity-test-plan.md` 의 parity fixture 를 통과하지 못한다.
- manifest 의 `repository.interface` 가 바뀌었는데 PHP 어댑터가 옛
  이름을 그대로 참조한다.

drift 보고 대상은 항상 manifest 를 정본으로 삼는다 — PHP 코드가
manifest 와 다르면 PHP 코드 쪽을 고치는 것이 기본이며, 의도적으로
계약을 바꾸는 경우에만 manifest 를 먼저 고친다
(`docs/portability-glossary.md` 의 Contract 정의 참고).

## 현재 상태: 측정 불가 (php/ 트리 없음)

이 리포트를 생성하는 `scripts/check_contract_drift.py` 는 각 모듈에
대해 아래 세 값만 출력한다.

- `module`: `src/modules/<module>` 디렉터리 이름.
- `manifest_status`: 해당 모듈 manifest 의 `port.status` 값.
- `php_tree_present`: 저장소 루트에 `php/` 디렉터리가 있는지 여부.

`php/` 디렉터리가 없는 동안(Phase A/B, 0351-0440)은 모든 모듈의 drift
판정이 구조적으로 `not_measurable` 이다 — PHP 구현 자체가 없으므로
"drift 없음"과 "drift 있음"을 구분할 근거가 없기 때문이다. 이 스크립트는
`php/` 가 없다는 이유로 실패(비정상 종료)하지 않는다 — 아직 PHP 골격이
없는 것은 Phase A/B 의 정상 상태이므로, drift 리포트는 그 사실을
정보성으로만 보고한다.

## 실행 방법

```
python scripts/check_contract_drift.py
```

표준 출력으로 모듈별 한 줄짜리 표를 출력하고, 항상 종료 코드 0 을
반환한다. 이 스크립트는 판정(pass/fail)을 내리는 게이트가 아니라 현재
상태를 보여주는 리포트이므로 `scripts/qa.sh` 에는 연결하지 않는다 —
`docs/module-contract-manifest-schema.md` 검증(`check_module_manifests.py`)
과 달리, drift 리포트는 아직 비교할 PHP 구현이 없어 실패시킬 기준
자체가 없다.

## 이후 확장 (이 태스크의 범위 밖)

`php/` 트리가 생기기 시작하면(0394 이후) 아래 항목이 채워질 수 있다 —
실제 구현은 후속 태스크가 담당하며, 이 문서는 그 방향만 남긴다.

- 모듈별로 `php/src/Modules/<Module>/Service.php` 같은 실제 파일 존재
  여부와, manifest 의 `service.public_methods` 각각에 대응하는 PHP
  메서드 존재 여부 비교.
- `docs/php-parity-test-plan.md` 의 parity fixture 통과 여부를 모듈별
  drift 판정에 반영.
- drift 가 발견된 모듈을 `scripts/qa.sh` 게이트로 승격할지 여부(이
  문서는 승격하지 않는다는 현재 방침만 고정하며, 승격 여부 자체는
  후속 태스크가 결정한다).

## 이 문서가 하지 않는 것

- 실제 PHP 코드와 manifest 를 비교하는 로직을 구현하지 않는다 — `php/`
  트리가 없는 동안은 비교 대상 자체가 없다.
- `scripts/qa.sh` 에 이 스크립트를 연결하지 않는다.
- `docs/php-replacement-readiness-checklist.md` 의 Gate 판정을 대신하지
  않는다 — drift 리포트는 참고 정보이며, ready/not-ready 판정 기준은
  그 문서가 고정한다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 모듈 단위 1:1 교체 원칙과 Python
  유지 기간.
- `docs/module-contract-manifest-schema.md` — 이 리포트가 읽는
  manifest 의 `port.status` 필드.
- `docs/php-namespace-mapping.md` — PHP 구현 위치를 찾을 때 쓰는
  namespace 규칙.
- `docs/php-parity-test-plan.md` — 향후 drift 판정에 반영할 parity
  기준.
- `docs/php-replacement-readiness-checklist.md` — drift 리포트가 참고
  정보로 쓰이는 readiness 판정 문서.
- `docs/portability-glossary.md` — Port/Contract 용어 정의.
