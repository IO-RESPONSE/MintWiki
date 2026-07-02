# PHP Replacement Readiness Checklist

이 문서는 `docs/php-replacement-strategy.md` 가 정의한 "PHP 전환 기준
(모듈별 readiness gate)" 5개 조건을, 모듈 담당자가 실제로 체크할 수 있는
**모듈별 ready/not-ready 판정 절차**로 구체화한다. Phase A: PHP Replacement
Contract, 0351-0390 의 산출물이다.

이 문서는 판정 **기준과 절차**만 고정하며, 모듈별 최신 상태를 계속
갱신하는 살아있는 표는 `docs/php-db-ui-micro-job-prompts-0351-0670.md`
0433(Add PHP module replacement matrix, not-started/partial/parity/pass
상태)의 범위다. 이 문서의 "모듈별 상태" 절은 Phase A 시점의 스냅샷이며,
정본(source of truth)은 항상 각 모듈의
`src/modules/<module>/manifest.json` 의 `port.status` 필드다.

## Gate 1: 모듈 계약 manifest 존재 + 검증 통과

- [ ] `src/modules/<module>/manifest.json` 이 존재한다.
- [ ] `scripts/check_module_manifests.py`(0365)가 요구하는 필수 필드
      (`schema_version`/`module`/`summary`/`port`/`service`/`repository`/
      `fixtures`)가 모두 채워져 있다.

확인 방법: `python scripts/check_module_manifests.py` 실행 결과 위반
목록에 해당 모듈이 없어야 한다. 이 검사는 이미 `scripts/qa.sh` 에
연결되어 있다(0366).

## Gate 2: 도메인 경계 검사 통과

- [ ] `src/modules/<module>/service.py`, `model.py` 등 도메인 계층이
      `fastapi`/`starlette`/`sqlalchemy`/`pydantic`/`asyncpg`/`uvicorn`/
      `alembic` 을 import 하지 않는다.
- [ ] 도메인 계층이 `src/app`(부트스트랩) 계층을 역참조하지 않는다.

확인 방법: `scripts/check_boundaries.py` 실행 결과 해당 모듈에 위반이
없어야 한다. 이 검사도 이미 `scripts/qa.sh` 에 연결되어 있다.

## Gate 3: fixture parity 커버리지

- [ ] manifest 의 `service.public_methods` 에 나열된 공개 메서드마다
      `tests/modules/<module>/fixtures/` 아래 관련 JSON fixture 가 최소
      1개 이상 존재한다.
- [ ] Python 쪽 fixture 러너(`docs/php-parity-test-plan.md` 가 기준
      패턴으로 지목한 `tests/modules/document/test_title_fixtures.py`,
      `tests/modules/acl/test_decision_code_fixtures.py` 와 같은 구조)가
      그 디렉터리의 파일 전부를 통과한다.
- [ ] `docs/php-parity-test-plan.md` 의 "Parity 판정 기준"을 만족한다 —
      같은 fixture 파일 전부에 대해 Python 러너와 **PHP 러너 둘 다**
      통과해야 한다. PHP 러너가 아직 없는 동안(0406/0425 이전)은 이
      조건이 구조적으로 미충족이므로 이 gate 는 not-ready 로 남는다.

확인 방법: `pytest tests/modules/<module>/` 실행, 그리고 manifest 의
`fixtures.path`/`fixtures.format` 이 실제 fixture 디렉터리와 일치하는지
확인.

## Gate 4: error code 상수화

- [ ] 모듈이 던지는 예외가 메시지 문자열이 아니라
      `docs/portable-exception-code-policy.md` 가 정한 `<module>.<reason>`
      형식의 안정적인 `code` 상수를 가진다.
- [ ] 해당 fixture 의 `errors` 필드가 그 `code` 값으로 채워져 있고,
      fixture 러너가 예외의 `code` 속성만 비교한다(메시지 문자열 비교
      아님).

확인 방법: 모듈의 예외 클래스 정의와 fixture 러너의 비교 로직을 읽고
메시지 문자열 비교(`str(exc) == ...`, `"..." in str(exc)` 등)가 없는지
확인한다.

## Gate 5: PostgreSQL 비의존 (ANSI SQL + MariaDB 호환)

- [ ] 모듈의 기본 쿼리 경로(저장소 adapter)가 JSONB 연산자 등
      PostgreSQL 전용 확장 기능을 쓰지 않는다.
- [ ] Phase B(DB 이식 조건)의 ANSI SQL + MariaDB 호환 요구와 모순되지
      않는다.

확인 방법: 모듈 저장소 adapter 코드 리뷰. 이 gate 를 자동 검사하는
스크립트를 만드는 것은 이 태스크의 범위 밖이다 — 필요해지면 Phase B
태스크가 다룬다.

## Ready 판정 규칙

모듈이 **ready** 로 표시되려면 아래가 모두 성립해야 한다.

1. 위 5개 gate 를 **전부** 체크한다. 일부만 충족한 상태는 ready 가
   아니다 — 부분 충족에 대한 별도 등급(예: "80% ready")은 두지 않는다.
2. `docs/php-replacement-strategy.md` 의 "전환 완료 기준"대로, PHP
   구현이 그 모듈의 fixture 전부에 대해 Python 구현과 동일한 결과를
   내는 parity test(0387 이 계획하고 이후 태스크가 구현)를 통과한다.
   PHP 코드 자체가 아직 없는 Phase A(0351-0390)/Phase B(0391-0440)
   기간에는 이 조건이 성립할 수 없으므로, 모든 모듈은 이 기간 동안
   구조적으로 not-ready 다.
3. ready 판정은 모듈별로 독립이다. 한 모듈이 ready 여도 다른 모듈의
   Python 유지 여부나 ready 상태는 자동으로 바뀌지 않는다
   (`docs/php-replacement-strategy.md` 의 "Python 유지 기간" 참고).

**not-ready** 로 표시할 때는 "not ready" 단독 표기가 아니라, 5개 gate
중 어떤 것이 실패했는지(예: "Gate 3, Gate 4 미충족")를 함께 남긴다 —
다음에 무엇을 해야 ready 가 되는지가 표기만 보고 바로 드러나야 한다.

## 모듈별 상태 (Phase A 시점 스냅샷)

Phase A(0351-0390) 시점에는 모든 모듈의 `manifest.json` 의 `port.status`
가 `not_started` 이고 PHP 러너/구현이 존재하지 않으므로(Gate 3 미충족),
아래 모든 모듈이 not-ready 다.

| 모듈 | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Gate 5 | 판정 |
|---|---|---|---|---|---|---|
| acl | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| admin | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| audit | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| cache | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| discussion | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| document | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| jobs | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| parser | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| render | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| revision | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| search | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |
| user | 충족 | 충족 | 미충족 (PHP 러너 없음) | - | - | not ready |

이 표는 갱신 의무가 있는 살아있는 문서가 아니다 — 실제 최신 상태를
알고 싶으면 각 모듈의 `manifest.json` 의 `port.status` 와, 존재한다면
0433 module replacement matrix 를 참고한다. 이 표는 Phase A 완료
시점(0390)에 "모든 모듈이 not-ready 로 시작했다"는 기준선(baseline)을
남기기 위한 것이다.

## 이 문서가 하지 않는 것

- 모듈별 최신 ready/not-ready 상태를 계속 갱신하는 살아있는 matrix를
  만들지 않는다(0433 의 범위).
- Gate 3(PHP 러너), Gate 4(error code 상수), Gate 5(ANSI SQL 자동 검사)
  스크립트의 실제 구현을 만들지 않는다 — 이후 Phase B 태스크(0406, 0407,
  0425-0429 등)의 범위다.
- 모듈 자체의 manifest, fixture, 저장소 adapter 내용을 바꾸지 않는다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 이 체크리스트가 구체화하는 5개
  readiness gate 와 전환 완료 기준의 원본.
- `docs/php-parity-test-plan.md` — Gate 3 이 참조하는 parity 판정 기준과
  fixture 실행 방식.
- `docs/module-contract-manifest-schema.md` — Gate 1 이 검사하는
  manifest 필드(`port.status` 포함).
- `docs/portable-exception-code-policy.md` — Gate 4 가 요구하는 error
  code 형식.
- `docs/modules.md` — 모듈 목록과 책임 경계.
- `docs/portability-glossary.md` — Port/Contract/Fixture 용어 정의.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 0433(module
  replacement matrix), 0406/0407/0425-0429(PHP 러너 구현) 등 후속 태스크
  목록.
