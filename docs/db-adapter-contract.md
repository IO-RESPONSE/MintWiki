# DB Adapter Contract

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md),
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md),
[Migration Portability Checklist](migration-portability-checklist.md),
[Persistence Boundaries](persistence-boundaries.md), [Search Adapter
Design](search-adapter-design.md)이 이미 정한 규칙과 패턴을 바탕으로, 각
모듈 저장소(`DocumentRepository`, `RevisionRepository` 등)의 Database*
구현체가 공통으로 의존하는 **DB adapter**의 최소 계약을 정의한다. 이 문서는
새 코드를 만들지 않는다 — `repository.py`들이 이미 암묵적으로 따르는
패턴을 명문화해, 이후 골격 코드([0450](php-db-ui-micro-job-prompts-0351-0670.md))와
PHP 구현([0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후)이 같은
계약을 지키게 하는 것이 목적이다.

## 목적

지금 각 모듈은 Repository 포트(ABC) + 두 어댑터(InMemory, Database)로
구성된다([persistence-boundaries.md](persistence-boundaries.md#repository-pattern)의
Repository Pattern). Database 어댑터는 SQLAlchemy `AsyncSession`을 직접
감싸는데, 이 어댑터가 어디까지 SQLAlchemy 구체 타입에 의존해도 되고
어디부터 "DB 종류에 상관없이 지켜야 할 동작"인지는 문서 어디에도 명시돼
있지 않다. PHP 포팅 시점에는 `AsyncSession`이 존재하지 않고 PDO 기반
구현을 새로 써야 하므로, 지금 이 경계를 명확히 하지 않으면 각 Database
Repository가 SQLAlchemy 세부사항(예외 타입, flush/commit 순서 등)을
얼마나 노출해도 되는지 판단 기준이 없다.

이 문서는 **"Python/PHP 두 언어의 Repository 구현이 공통으로 의존할 수
있는 최소 동작 집합"**을 계약으로 고정한다. 계약이지 코드가 아니다 —
[0450](php-db-ui-micro-job-prompts-0351-0670.md)이 이 계약을 실제 Python
클래스 골격으로 옮기고, [0484](php-db-ui-micro-job-prompts-0351-0670.md)
이후 PHP 쪽 골격이 동일 계약을 PHP interface로 옮긴다.

## 적용 범위

적용 대상:

- `src/modules/*/repository.py`의 Database* 구현체(지금:
  `DatabaseDocumentRepository`, `DatabaseRevisionRepository` 등)가 내부적으로
  의존하는 세션/연결 계층.
- [0450](php-db-ui-micro-job-prompts-0351-0670.md) 이후 `src/persistence`에
  추가될 DB adapter skeleton.
- [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP 쪽 SQL
  repository 골격.

적용되지 않는 것:

- 모듈별 도메인 규칙(정규화된 제목 유일성, FK 존재 검증 등) — 각 모듈
  Repository/Service의 책임이며 [persistence-boundaries.md](persistence-boundaries.md)가
  이미 다룬다.
- InMemory* 구현체 — SQL을 전혀 거치지 않으므로 이 계약의 대상이 아니다.
- 커밋 시점과 크로스 모듈 트랜잭션 경계의 세부 규칙 —
  [0473 repository 트랜잭션 정책](php-db-ui-micro-job-prompts-0351-0670.md)이
  다룬다. 이 문서는 "어댑터가 commit/rollback을 노출해야 한다"는 존재만
  확정한다.
- 제약 위반의 구체적 식별 방법(에러 메시지 매칭 vs 제약 이름 vs SQLSTATE) —
  [0474 portable duplicate key handling](php-db-ui-micro-job-prompts-0351-0670.md)이
  다룬다.
- SQL 방언 분기(예: upsert)의 실제 구현과 드라이버 기능 차이 탐지 —
  [0450](php-db-ui-micro-job-prompts-0351-0670.md),
  [0472 DB driver capability model](php-db-ui-micro-job-prompts-0351-0670.md)이
  다룬다.
- ad hoc 문자열 SQL 금지와 쿼리 빌더 사용 규칙 —
  [0451 portable query builder policy](portable-query-builder-policy.md)가
  다룬다.

## 계약이 다루는 것

1. **연결/세션 소유권** — 누가 만들고 닫는가.
2. **최소 동작 집합** — Repository가 어댑터에 기대할 수 있는 것.
3. **통합 제약 위반 신호** — DB 에러를 어떻게 하나의 신호로 좁히는가.
4. **드라이버 타입이 새지 않게 막는 경계** — 기존 이식성 규칙과의 접점.

## 1. 연결/세션 소유권

**계약: 어댑터는 연결(세션)을 스스로 만들거나 닫지 않는다.** 애플리케이션
조립 계층(지금은 `app/database.py`, PHP 쪽은 이후 확정될 부트스트랩)이
연결을 만들어 Repository 생성자에 주입한다.

- 이미 만족: `DatabaseDocumentRepository.__init__(self, session: AsyncSession)`
  등 모든 Database* 구현체가 세션을 주입받는다
  ([persistence-boundaries.md](persistence-boundaries.md#session-lifecycle)의
  Session Lifecycle).
- PHP: PDO 연결 객체를 동일하게 주입받는 구조를 유지한다(구체 부트스트랩은
  [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후).

## 2. 최소 동작 집합

Repository가 어댑터에게 기대할 수 있는 것은 아래 다섯 가지뿐이다. 구체
메서드 이름·시그니처·문(statement) 표현 방식은
[0450](php-db-ui-micro-job-prompts-0351-0670.md)(Python skeleton)과
[0451](portable-query-builder-policy.md)(쿼리 빌더 정책)이 정한다 —
이 문서는 "이 다섯 가지 동작이 존재해야 한다"만 고정한다.

```python
class DbAdapter(ABC):
    """모든 모듈의 Database* 저장소 구현체가 감싸는 최소 연결/세션 포트.

    Python 쪽 구체 구현은 SQLAlchemy AsyncSession을 감싸고, PHP 쪽 구체
    구현은 PDO 연결을 감싼다. 이 인터페이스 자체는 SQLAlchemy도 PDO도
    아니다 — 두 언어가 공통으로 만족해야 하는 최소 동작만 규정한다.
    statement의 구체 타입은 이 문서의 범위 밖이다(0451).
    """

    @abstractmethod
    async def add(self, row: object) -> None:
        """새 행에 해당하는 객체를 이번 트랜잭션에 추가한다(아직 커밋 전)."""

    @abstractmethod
    async def fetch_one(self, statement: object) -> Optional[object]:
        """조회문을 실행해 첫 결과를 반환한다. 없으면 예외가 아니라 None."""

    @abstractmethod
    async def fetch_all(self, statement: object) -> list[object]:
        """조회문을 실행해 모든 결과를 반환한다. 없으면 빈 리스트."""

    @abstractmethod
    async def execute(self, statement: object) -> None:
        """조회 결과가 필요 없는 INSERT/UPDATE/DELETE 문을 실행한다."""

    @abstractmethod
    async def commit(self) -> None:
        """지금까지의 변경을 확정한다. 실패하면 §3의 통합 위반 신호를 던진다."""

    @abstractmethod
    async def rollback(self) -> None:
        """지금까지의 변경을 취소한다."""
```

| 지금 SQLAlchemy 대응 | 위 계약 동작 |
|---|---|
| `session.add(orm)` | `add` |
| `select()` + `scalar_one_or_none()` | `fetch_one` |
| `select()` + `.all()` / `.scalars()` | `fetch_all` |
| `update()` + `session.execute(stmt)` | `execute` |
| `session.commit()` | `commit` |
| `session.rollback()` | `rollback` |

- 정렬이 필요한 다건 조회(`list_by_document_id` 등)는 정렬 기준을 어댑터가
  아니라 호출자(Repository)가 statement에 지정한다 — 어댑터는 임의 정렬을
  기본값으로 삼지 않는다(이미 `RevisionRepository.list_by_document_id`가
  `created_at` 정렬을 명시).
- 삭제(delete)는 지금 어떤 Repository도 요구하지 않으므로 이 계약에
  포함하지 않는다 — 필요해지면 그 시점 태스크에서 계약을 확장한다.
- 삽입 후 DB가 채우는 값(자동증가 id, `RETURNING` 결과 등)을 어댑터가
  돌려준다고 가정하지 않는다 — id는
  [portable-id-column-policy.md](portable-id-column-policy.md)에 따라
  애플리케이션이 삽입 전에 이미 생성해 둔다.

## 3. 통합 제약 위반 신호

**계약: 어댑터는 DB가 던지는 제약 위반(UNIQUE, FK, NOT NULL, CHECK)을 하나의
통합된 신호로 Repository에 전달한다.** Repository는 이 신호를 받아 도메인
예외(`DuplicateNormalizedTitleError` 등)로 변환한다.

- 지금 상태: `DatabaseDocumentRepository.create`는 SQLAlchemy
  `IntegrityError`를 잡아 메시지 문자열에 `"normalized_title"`이
  포함되는지 검사해 도메인 예외로 바꾼다. 이 문자열 매칭은 PostgreSQL
  에러 메시지 형식에 의존하므로, 그대로 PHP `PDOException`으로 옮기면
  깨진다.
- 이 문서가 지금 확정하는 것: 어댑터는 드라이버별 제약 위반 예외(지금은
  SQLAlchemy `IntegrityError`, PHP는 `PDOException` 등)를 최소한 하나의
  통합 신호로 잡아 Repository에 전달할 수 있어야 한다는 존재 자체.
- 이 문서가 확정하지 않는 것: 위반된 제약을 식별하는 구체적인 방법(제약
  이름 파싱 vs 에러 메시지 매칭 vs DB별 SQLSTATE 코드 비교) —
  [0474 portable duplicate key handling](php-db-ui-micro-job-prompts-0351-0670.md)이
  다룬다. 다만 힌트는 남긴다:
  [portable-schema-naming-policy.md](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)가
  이미 모든 제약에 `uq_<table>_<column>` 같은 예측 가능한 이름을
  강제하므로, 0474는 에러 메시지 문자열 매칭 대신 이 이름을 활용할 여지가
  있다.

## 4. 드라이버 타입이 새지 않게 막는 경계

**계약: Repository보다 상위(Service, Domain) 계층에 어댑터가 SQLAlchemy
`Row`, PDO `PDOStatement` 같은 드라이버 전용 타입을 그대로 반환하지
않는다.** 어댑터 호출 결과는 항상 ORM 모델(Python)이나 그에 준하는 평범한
데이터 구조로 변환된 뒤 `to_domain()`을 거쳐야 한다.

- 이미 만족: [persistence-boundaries.md](persistence-boundaries.md#conversion-semantics)의
  Conversion Semantics(`from_domain`/`to_domain`)가 이미 이 경계를
  규정한다 — 이 문서는 새 규칙을 만들지 않고, 그 경계가 DB adapter
  계층까지 내려온다는 것만 재확인한다.
- [AGENTS.md](../AGENTS.md#이식성-계층-규칙-portability-layering) 이식성
  계층 규칙과의 관계: `repository.py`만 `sqlalchemy`를 import할 수 있다는
  규칙이 이미 `scripts/check_boundaries.py`로 강제되므로, 어댑터 타입이
  `service.py`/`model.py`로 새는 것은 이미 자동 검사 대상이다.

## 계약을 만족하는 구현체

| 구현체 | 시점 | 언어/드라이버 | 비고 |
|---|---|---|---|
| `DatabaseDocumentRepository`, `DatabaseRevisionRepository` 등 | 지금 | Python, SQLAlchemy `AsyncSession` | 이 계약을 암묵적으로 이미 만족(§3 제약 위반 매핑 방식은 미정 상태로 남아있음) |
| InMemory* 구현체 | 지금 | Python, dict | 이 계약 대상 아님(적용 범위 참고) |
| 0450 skeleton | [0450](php-db-ui-micro-job-prompts-0351-0670.md) | Python, SQLAlchemy | 이 계약을 처음으로 명시적 클래스로 옮긴다(ORM 동작 확장은 하지 않는다) |
| PHP SQL repository skeleton | [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 | PHP, PDO | 같은 계약을 PHP interface로 옮긴다 |

## 이 문서 이후 단계

- **0450**: 이 계약(1~4절)을 실제 Python 클래스 골격으로 옮긴다. ORM 동작
  확장은 하지 않는다.
- **0451**([portable-query-builder-policy.md](portable-query-builder-policy.md)):
  2절이 statement의 구체 표현을 열어 둔 지점을 이어받아, ad hoc 문자열
  SQL 금지와 쿼리 빌더 사용 규칙을 확정한다.
- **0452, 0453**: document/revision 저장소가 이 계약을 만족하는지
  portability 테스트로 검증한다.
- **0454-0458**: user/ACL/discussion/audit/jobs 각 모듈의 저장소
  portability 계획에서 이 계약을 참조한다.
- **0472**: DB driver capability model — 어댑터가 드라이버별로 다르게
  노출할 수 있는 기능 차이(예: `RETURNING` 지원 여부)를 다룬다.
- **0473**: repository 트랜잭션 정책 — 2절 commit/rollback의 정확한 시점과
  크로스 모듈 트랜잭션 경계를 확정한다.
- **0474**: portable duplicate key handling — 3절이 미정으로 남긴 제약
  식별 방법을 확정한다.
- **0484 이후**: PHP 쪽 PDO connection/transaction skeleton, SQL dialect
  enum, document/revision SQL repository skeleton이 이 계약을 PHP
  interface로 옮긴다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 금지 SQL
  feature 목록(upsert 등 방언 분기가 필요한 지점의 배경).
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 트랜잭션
  /DDL 커밋 매트릭스.
- [Migration Portability Checklist](migration-portability-checklist.md) —
  마이그레이션 작성 시점 체크리스트(이 문서는 쿼리 시점 계약).
- [Persistence Boundaries](persistence-boundaries.md) — Repository 패턴,
  세션 소유권, 변환 규칙의 원출처.
- [Search Adapter Design](search-adapter-design.md) — 같은 "포트/어댑터
  계약 문서" 형식의 선례.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
