# PHP Replacement Strategy

이 문서는 Python 으로 구현된 위키 엔진을 PHP 로 전환하는 전략을 고정한다.
전환은 앱 전체를 한 번에 재작성하는 것이 아니라, `docs/modules.md` 가 정의한
모듈 경계를 따라 **모듈 단위로 1:1 교체**하는 방식으로 진행한다. 실제 작업
순서는 `docs/php-db-ui-micro-job-prompts-0351-0670.md` 의 큐 정책
(`PHP 전환 기반 -> ANSI/MariaDB DB 모듈 -> 화면단 -> 웹호스팅 배포`)을 따른다.

이 문서는 그중 **Phase A: PHP Replacement Contract (0351-0390)** 가 만들
계약의 배경 원칙을 적는다. 개별 계약(manifest, fixture, error code 등)의
구체 형식은 이후 단계 태스크에서 정의한다.

## 배경

`AGENTS.md` 의 이식성 계층 규칙은 이미 도메인 계층
(`service.py`/`model.py` 등)이 `fastapi`/`starlette`/`sqlalchemy`/
`pydantic`/`asyncpg`/`uvicorn`/`alembic` 을 import 하지 못하게 강제하고
있다(`scripts/check_boundaries.py`). 이 문서는 그 규칙 위에서, "언제까지
Python 을 유지하는가", "무엇이 준비되면 PHP 전환을 시작할 수 있는가",
"어떤 결합을 만들면 안 되는가"를 명시한다.

## 전환 원칙: 모듈 단위 1:1 교체

- 교체 단위는 `src/modules/<module>` 디렉터리 하나이며, 앱 전체가 아니다.
- 각 모듈은 언어 독립 계약(manifest, 서비스 메서드 시그니처, 에러 코드,
  fixture)을 먼저 고정한 뒤에만 PHP 구현으로 교체한다. 계약 없이 PHP
  코드를 먼저 작성하지 않는다.
- PHP 구현은 Python 구현과 같은 공개 서비스 메서드 이름·입력·출력 의미를
  가져야 한다. 내부 구현 세부사항(자료구조, 알고리즘 선택)은 언어별로
  달라도 된다.
- 모듈은 `docs/modules.md` 의 Dependency Rules 를 그대로 따르며, 교체
  순서는 의존되는 모듈(leaf)부터 의존하는 모듈 순으로 진행한다.
- 한 모듈이 PHP 로 전환되었다고 해서 다른 모듈도 함께 전환되는 것은
  아니다. 앱은 한동안 Python 모듈과 PHP 모듈이 같은 배포 안에 공존할 수
  있다고 가정하지 않는다 — 대신 모듈별로 Python 전체 앱 또는 PHP 전체
  앱 중 하나로 완전히 전환하는 것을 목표로 하되, 계약과 fixture 는 전환
  전 기간 동안 두 언어가 공유한다.

## Python 유지 기간

- Python 구현은 각 모듈의 "PHP 전환 준비 체크리스트"(0388) 모든 항목이
  ready 로 표시되고, 동일 fixture 기반 parity 테스트(0387)를 PHP 구현이
  통과하기 전까지 정식 구현으로 유지한다. 준비되지 않은 상태에서 Python
  코드를 먼저 삭제하지 않는다.
- Phase A(0351-0390)와 Phase B(0391-0440) 동안 PHP 쪽에는 계약과 골격만
  추가되며, 두 언어의 실제 기능 parity 는 검증되지 않는다. 이 기간
  Python 구현은 유일한 운영 경로로 유지된다.
- 모듈별 판단이 원칙이다: 어떤 모듈의 PHP 판이 준비되었다고 다른 모듈의
  Python 유지 여부가 자동으로 바뀌지 않는다.
- 병행 기간 동안 두 언어는 같은 DB 스키마와 같은 fixture 를 공유해야
  하며, 각자 별도의 데이터 모델이나 별도의 정답 fixture 로 갈라지지
  않는다.

## PHP 전환 기준 (모듈별 readiness gate)

한 모듈의 PHP 전환을 시작하려면 아래가 모두 성립해야 한다.

1. 모듈 계약 manifest(0353 이후)가 존재하고 검증 스크립트(0365, 0366)를
   통과한다.
2. 모듈 도메인 계층이 `scripts/check_boundaries.py` 경계 검사를 통과한다
   (프레임워크 미결합).
3. 모듈의 핵심 동작이 언어 독립 JSON fixture(0369 이후)로 커버되어,
   Python 과 PHP 양쪽 러너가 같은 입력에 같은 출력을 내는지 검증할 수
   있다.
4. 모듈의 예외/오류가 메시지 문자열이 아니라 안정적인 error code
   상수(0373 이후)로 식별된다.
5. 모듈이 PostgreSQL 전용 기능에 의존하지 않는다(ANSI SQL + MariaDB
   호환, Phase B 의 DB 이식 조건).

전환 완료 기준: PHP 구현이 위 fixture 전부에 대해 Python 구현과 동일한
결과를 내고(parity test, 0387), readiness checklist(0388)에서 해당 모듈이
ready 로 표시되어야 한다. 완료 전까지는 Python 구현이 운영 경로로 남는다.

## 금지할 결합 (Forbidden Couplings)

- 도메인 계층(`service.py`/`model.py` 등 순수 로직)이 `fastapi`/
  `starlette`/`sqlalchemy`/`pydantic`/`asyncpg`/`uvicorn`/`alembic` 을
  import 하는 것. 기존 `AGENTS.md` 규칙이며 `scripts/check_boundaries.py`
  가 강제한다.
- 모듈 도메인 계층이 `src/app`(부트스트랩) 계층을 역참조하는 것.
- PHP 런타임이 Python 프로세스를 호출하거나 Python 런타임에 의존하는
  것. 두 언어는 DB 스키마와 fixture 만 공유하며, 서로의 런타임을
  호출하지 않는다.
- 비즈니스 규칙(제목 정규화, 중복/권한 판단 등)을 한쪽 언어의 정규식이나
  검증 로직에만 두고 다른 언어에서 별도로 재구현하며 fixture 로 결과를
  고정하지 않는 것. 정규식 문법은 Python `re` 와 PHP PCRE 가 다를 수
  있으므로 반드시 입력/기대출력 fixture 로 양쪽을 맞춘다.
- PostgreSQL 전용 SQL 기능(예: JSONB 연산자, PostgreSQL 전용 확장 함수
  등)을 기본 쿼리 경로에 사용하는 것. 기본 경로는 ANSI SQL + MariaDB
  호환을 우선한다.
- 예외 메시지 문자열 비교로 에러 종류를 식별하는 것. 반드시 안정적인
  error code 상수를 반환/비교한다.
- 모듈 계약(manifest)에 선언되지 않은 내부 필드나 비공개 메서드에 다른
  모듈이나 PHP 어댑터가 직접 의존하는 것.

## 관련 문서

- `docs/architecture.md` — 전체 런타임 구성과 요청 흐름.
- `docs/modules.md` — 모듈 책임과 의존 규칙.
- `docs/roadmap.md` — Python 구현 단계별 로드맵.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — PHP 전환 큐 정책과
  Phase A/B 태스크 목록.
- `AGENTS.md` — 이식성 계층 규칙과 경계 검사.
