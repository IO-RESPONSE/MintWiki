# PHP Module Replacement Matrix

이 문서는 `docs/modules.md` 가 정의한 12개 모듈 각각에 대해, **Python
구현 상태**와 **PHP 구현 상태**를 한 표로 보여주는 살아있는 matrix다.
Phase B: PHP Runtime Skeleton, 0391-0440 의 산출물(0433)이다.

`docs/php-replacement-readiness-checklist.md` 의 "모듈별 상태" 절은
Phase A 완료 시점(0390)의 스냅샷이며 이후 갱신 의무가 없다고 명시한다.
이 문서가 그 뒤를 이어 **모듈별 최신 상태를 계속 갱신하는 살아있는
matrix** 역할을 맡는다(`docs/php-parity-test-plan.md` 가 "PHP 모듈 교체
matrix(0433)"로 미리 가리키던 문서가 이것이다).

이 표의 정본(source of truth)은 항상 다음 두 가지다.

- 각 모듈의 `src/modules/<module>/manifest.json` 의 `port.status` 필드
  (Python 쪽 정본).
- `php/src/Modules/<Module>/`, `php/tests/Modules/<Module>/` 아래 실제
  존재하는 PHP 코드/테스트 (PHP 쪽 정본).

이 표는 그 정본들을 사람이 한눈에 읽을 수 있게 요약한 것이며, 정본과
표가 어긋나면 정본이 우선한다.

## 상태 정의 (4단계)

모듈별 PHP 구현 상태는 아래 4단계 중 하나로 표시한다. 단계는
`not-started < partial < parity < pass` 순으로 누적된다 — 상위 단계는
하위 단계 요구사항을 모두 포함한다.

- **not-started**: `php/src/Modules/<Module>/` 아래에 `README.md` 외에
  실제 도메인 클래스가 없다. 즉 그 모듈의 PHP 포팅이 아직 시작되지
  않았다.
- **partial**: `php/src/Modules/<Module>/` 아래에 하나 이상의 실제
  도메인 클래스(값 객체, 서비스, 저장소 인터페이스, 예외 등)가
  존재하지만, `docs/php-replacement-readiness-checklist.md` 의
  **Gate 3(fixture parity 커버리지)** 를 아직 만족하지 못한다 — manifest
  의 `service.public_methods` 전체가 아니라 그중 일부만 PHP 러너로
  fixture 비교가 되거나, 아예 fixture 비교 없이 구조만 있는 상태를
  포함한다.
- **parity**: 그 모듈의 fixture 디렉터리에 있는 **모든** `*.json`
  fixture 에 대해 Python 러너와 PHP 러너가 둘 다 통과한다
  (`docs/php-parity-test-plan.md` 의 "Parity 판정 기준"을 만족 =
  readiness checklist Gate 3 충족). 나머지 gate(1/2/4/5)는 아직
  충족하지 못했을 수 있다.
- **pass**: `docs/php-replacement-readiness-checklist.md` 의 5개 gate를
  모두 충족하고(`manifest.json` 의 `port.status` 가 `ready`), PHP
  구현이 운영 경로로 전환된 상태. 이 상태가 되어야
  `docs/php-replacement-strategy.md` 의 "Python 유지 기간" 조건에 따라
  Python 구현 제거를 검토할 수 있다.

Phase A/B(0351-0440) 기간에는 `docs/php-replacement-strategy.md` 와
`docs/php-replacement-readiness-checklist.md` 가 이미 명시한 대로 PHP
쪽 fixture 러너가 모듈 전체를 커버하지 못하므로, 이 기간 동안 어떤
모듈도 구조적으로 **parity**/**pass** 에 도달할 수 없다. 이는 결함이
아니라 Phase 구간이 정의한 정상 상태다.

## 모듈별 matrix

| 모듈 | Python 구현 | PHP 구현 | 근거 |
|---|---|---|---|
| acl | pass | partial | `php/src/Modules/Acl/Decision.php` 존재, `php/tests/Modules/Acl/DecisionCodeFixtureRunnerTest.php` 가 일부 fixture를 비교하지만 manifest의 `port.status`는 아직 `not_started`(Gate 3 전체 미충족) |
| admin | pass | partial | `php/src/Modules/Admin/Service.php` 존재, 대응 fixture parity 러너 없음 |
| audit | pass | partial | `php/src/Modules/Audit/AuditEvent.php` 등 값 객체·에러 클래스 존재, fixture parity 러너 없음 |
| cache | pass | partial | `php/src/Modules/Cache/Backend.php` 존재, fixture parity 러너 없음 |
| discussion | pass | partial | `php/src/Modules/Discussion/{Comment,Thread,ThreadState}.php` 등 존재, fixture parity 러너 없음 |
| document | pass | partial | `php/src/Modules/Document/{Document,Repository,Service,Title}.php` 존재, `php/tests/Modules/Document/TitleFixtureRunnerTest.php` 가 `Title::normalize()` 만 비교(서비스 공개 메서드 전체는 아님) |
| jobs | pass | partial | `php/src/Modules/Jobs/Runner.php` 존재, fixture parity 러너 없음 |
| parser | pass | not-started | `php/src/Modules/Parser/` 는 `README.md` 뿐, 도메인 클래스 없음. `php/tests/Modules/Parser/ParityPlaceholderTest.php`(0428)가 fixture 무결성만 확인하는 expected-failure placeholder로 남아 있음 |
| render | pass | not-started | `php/src/Modules/Render/` 는 `README.md` 뿐, 도메인 클래스 없음. `php/tests/Modules/Render/ParityPlaceholderTest.php`(0429)가 fixture 무결성만 확인하는 expected-failure placeholder로 남아 있음 |
| revision | pass | partial | `php/src/Modules/Revision/{Repository,Revision}.php` 존재, fixture parity 러너 없음 |
| search | pass | not-started | `php/src/Modules/Search/` 는 `README.md` 뿐, PHP 테스트 디렉터리도 아직 없음 |
| user | pass | partial | `php/src/Modules/User/{User,AnonymousIdentity,IpIdentity}.php` 등 존재, fixture parity 러너 없음 |

Python 구현은 모든 모듈에서 `pass` 다 — Python 쪽이 현재 유일한 운영
경로이며(`docs/php-replacement-strategy.md` 의 "Python 유지 기간"),
manifest 나 fixture 러너가 그 사실을 바꾸기 전까지 이 열은 갱신되지
않는다.

## 이 표를 최신으로 유지하는 방법

- 어떤 모듈의 `php/src/Modules/<Module>/` 에 처음으로 도메인 클래스가
  추가되면 그 모듈 행을 `not-started` → `partial` 로 갱신한다.
- 어떤 모듈의 fixture 디렉터리 전체가 PHP 러너로 커버되어
  `docs/php-replacement-readiness-checklist.md` Gate 3을 만족하면
  `partial` → `parity` 로 갱신한다.
- 어떤 모듈이 5개 gate를 모두 충족해 `manifest.json` 의 `port.status`
  가 `ready` 로 바뀌면 `parity` → `pass` 로 갱신하고, 근거 열에 해당
  근거(gate 충족 확인 방법)를 남긴다.
- 갱신은 항상 실제 코드/manifest 상태를 먼저 바꾼 뒤에 따라가는
  후행 기록이다 — 이 표를 먼저 바꾸고 코드가 뒤따르게 하지 않는다.

## 이 문서가 하지 않는 것

- readiness gate 판정 절차 자체를 새로 정의하지 않는다 — 5개 gate의
  정의와 확인 방법은 `docs/php-replacement-readiness-checklist.md` 의
  몫이다.
- Parity 판정 기준 자체를 새로 정의하지 않는다 —
  `docs/php-parity-test-plan.md` 를 그대로 참조한다.
- PHP 실제 구현이나 fixture parity 테스트 코드를 작성하지 않는다.
- 각 모듈의 `manifest.json` 내용을 바꾸지 않는다 — 이 표는 그 값을
  읽어 요약할 뿐이다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 전환 원칙과 readiness gate의
  원본.
- `docs/php-replacement-readiness-checklist.md` — 5개 gate의 구체적
  확인 절차와 Phase A 시점 스냅샷.
- `docs/php-parity-test-plan.md` — Parity 판정 기준과 fixture 실행
  방식.
- `docs/module-contract-manifest-schema.md` — `port.status` 필드 정의.
- `docs/modules.md` — 모듈 목록과 책임 경계.
- `docs/php-namespace-mapping.md` — 모듈 ↔ PHP namespace 매핑.
- `docs/contract-drift-report.md` — manifest와 PHP 구현 사이 drift를
  보고하는 별도 리포트(이 표와 역할이 다르다 — drift 리포트는
  manifest 선언과 실제 구현의 불일치를, 이 표는 구현 진행 단계를
  보여준다).
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 이 표가 참조하는
  PHP 골격 태스크(0394 이후) 목록.
