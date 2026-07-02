# PHP No-Framework Domain Rule

이 문서는 PHP `php/src/Modules/` 도메인 계층이 지켜야 할 framework 금지
경계 규칙을 고정한다. Phase B: PHP Runtime Skeleton, 0391-0440 의
산출물이다(`docs/php-db-ui-micro-job-prompts-0351-0670.md`). Python
쪽에서 같은 목적으로 이미 강제되는 `scripts/check_boundaries.py`,
`scripts/check_no_app_import_in_modules.py` 와 동등한 원칙을 PHP 쪽
용어로 옮겨 적을 뿐이며, **이 규칙을 강제하는 자동 검사 스크립트 작성은
이 문서의 범위가 아니다** — `docs/php-static-analysis-plan.md` 의 도입
트리거 조건이 성립할 때 후속 태스크가 구현한다.

## 배경: Python 쪽 두 경계 검사기

Python 쪽은 도메인(`src/modules/`)의 PHP 이식 가능성을 지키기 위해 두
검사를 CI/QA(`scripts/qa.sh`)에서 강제한다.

- `scripts/check_boundaries.py`: 도메인 파일이 `fastapi`, `starlette`,
  `sqlalchemy`, `pydantic`, `pydantic_settings`, `asyncpg`, `uvicorn`,
  `alembic` 를 import 하지 못하게 막는다. 단, `router.py`(fastapi),
  `repository.py`(sqlalchemy), `schema.py`(pydantic) 는 파일명 단위
  예외로 해당 프레임워크 import 를 허용한다.
- `scripts/check_no_app_import_in_modules.py`: 도메인 파일이 UI/API
  부트스트랩 계층인 `app` 패키지를 역참조하지 못하게 막는다. 의존
  방향은 항상 `app -> modules` 여야 한다.

## PHP 쪽 대응 경계

### 도메인 루트

`php/src/Modules/` 가 도메인 루트다 — Python `src/modules/` 에 대응하고,
`php/composer.json` 의 classmap 예외(`docs/php-coding-standard.md` PSR-4
오토로딩 규칙 절 참고) 대상 디렉터리와도 같다.

### 검사 제외 계층 (어댑터)

아래 두 디렉터리는 Python `src/app`(부트스트랩)에 대응하는 어댑터
전용 계층이므로 이 규칙의 검사 대상에서 제외한다.

- `php/src/App/` — 설정 로더, error code registry 등 부트스트랩
  코드(Python `src/app` 대응).
- `php/src/Http/` — `Router`, `Request`/`Response`, route 등록 클래스 등
  HTTP 어댑터 코드. Python 쪽은 router 코드가 각 모듈 안(`router.py`)에
  있어 파일명 예외로 처리하지만, PHP 쪽은 애초에 `Router` 관련 클래스가
  `Modules/` 밖의 별도 namespace(`MintWiki\Http`)에 있으므로 파일명
  예외가 아니라 디렉터리 단위 제외로 대응한다.

### 규칙 1 — framework import 금지

`php/src/Modules/` 하위 모든 파일은 PHP 코어(내장 클래스, SPL, PDO 등
확장 모듈)를 넘어서는 어떤 3rd-party composer 패키지도 `use` 하거나
전체정규화 이름으로 참조할 수 없다.

- `php/composer.json` 의 `require` 는 현재 `php: ^8.1` 하나뿐이라 위반
  대상 자체가 존재하지 않는다 — 이 규칙은 향후 3rd-party 의존성이
  추가될 때를 대비해 경계를 미리 고정해 두는 것이다.
- `PDO`(및 `pdo_*` 확장)는 PHP 코어 확장이지 composer 패키지가
  아니므로 이 규칙의 "framework" 범주에 포함하지 않는다. 즉 0435
  이후 추가되는 `Modules/Document/` 안의 Database 구현체가 `PDO` 를
  직접 쓰는 것은 이 규칙 위반이 아니다 — Python 쪽에서 `sqlalchemy`
  라는 3rd-party ORM이 필요했던 것과 달리, PHP 코어는 DB 접근 기능을
  이미 프레임워크 없이 제공하기 때문이다(`docs/php-replacement-strategy.md`
  가 고정한 shared hosting 의존성 최소화 원칙과도 맞는다).
  - 향후 별도 3rd-party HTTP 클라이언트/ORM/검증 라이브러리가 실제로
    필요해지면, Python `router.py`/`repository.py`/`schema.py` 예외
    패턴과 동일하게 이 문서에 파일명 단위 예외를 추가해야 그 의존성을
    도메인 파일에서 쓸 수 있다 — 예외 없이 새 의존성을 도메인에 바로
    끌어들이지 않는다.

### 규칙 2 — 어댑터 계층 역참조 금지

`php/src/Modules/` 하위 코드는 `MintWiki\App\`, `MintWiki\Http\` 로
시작하는 namespace 의 어떤 클래스도 `use` 할 수 없다. 의존 방향은
항상 `App -> Modules`, `Http -> Modules` 여야 한다(예:
`App/ErrorCodeRegistry.php` 가 `MintWiki\Document\...` 예외 클래스를
참조하는 것은 허용되는 방향이고, 그 반대는 금지된다).

현재 `php/src/Modules/` 전체를 확인하면 이 두 규칙 모두 위반 사례가
없다 — 이 문서는 지금의 상태를 그대로 고정할 뿐, 코드를 바꾸지 않는다.

## 시행 방법

지금은 이 문서를 코드 리뷰 기준으로만 삼아 사람이 확인한다. Python
쪽처럼 AST를 파싱해 위반을 자동으로 잡는 스크립트(`scripts/qa.sh` 에
연결된 `check_boundaries.py`/`check_no_app_import_in_modules.py` 의 PHP
버전)를 실제로 작성할지, 작성한다면 별도 스크립트로 만들지 정적 분석
도구(PHPStan 커스텀 규칙 등)로 구현할지는
`docs/php-static-analysis-plan.md` 의 도입 트리거 조건이 성립하는
시점의 후속 태스크가 판단한다.

## 이 문서가 하지 않는 것

- 이 규칙을 강제하는 자동 검사 스크립트나 PHPStan 커스텀 규칙을
  작성하지 않는다.
- `scripts/qa.sh`, `php/composer.json` 을 수정하지 않는다.
- `php/src/Modules/`, `php/src/App/`, `php/src/Http/` 의 기존 코드
  구조나 클래스를 바꾸지 않는다 — 현재 상태를 문서화할 뿐이다.
- 향후 3rd-party 의존성이 실제로 필요해졌을 때 어떤 예외를 추가할지
  구체적으로 정하지 않는다 — 그 시점의 태스크가 필요한 예외를
  판단한다.

## 관련 문서

- `docs/php-coding-standard.md` — PSR-4 오토로딩/namespace/클래스 선언
  규칙 정본이며, 이 문서가 다루는 framework 금지 규칙을 자신의 범위
  밖으로 명시해 이 문서를 가리킨다.
- `docs/php-static-analysis-plan.md` — 이 규칙을 자동 검사로 구현할지
  판단하는 도입 트리거 조건.
- `docs/php-namespace-mapping.md` — `php/src/Modules/` 도메인 namespace
  매핑 규칙.
- `docs/php-replacement-strategy.md` — shared hosting 의존성 최소화
  원칙과 모듈 단위 1:1 교체 전략.
- `docs/repository-port-contracts.md` — `Repository` 포트/구현 분리
  원칙(이 문서의 PDO 예외와 관련).
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 0424 태스크 정의와
  전후 태스크 목록.
- `scripts/check_boundaries.py`, `scripts/check_no_app_import_in_modules.py`
  — 이 문서가 원칙을 옮겨 적은 Python 원본 검사기.
