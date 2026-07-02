# ANSI SQL Persistence Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 의 기반 문서다.
이후 DB 이식성 관련 잡(0442 호환성 매트릭스, 0447 금지 기능 검사 스크립트,
0450 SQL dialect abstraction 등)은 이 문서에 정의된 정책을 전제로 진행한다.
이 문서 자체는 정책 선언이며, 기존 코드(`src/app/database.py`,
`src/app/config.py`의 `postgresql+asyncpg` 드라이버)를 지금 당장 바꾸지 않는다.
드라이버·연결 계층 전환은 0442 이후 잡의 범위다.

## 목적

이 엔진은 완성 후 PHP + MariaDB 기반으로 이식될 계획이다
([README.md](../README.md), [search-adapter-design.md](search-adapter-design.md)
참고). 현재 Python 구현은 PostgreSQL을 사용하지만, `repository.py`가 실행하는
SQL과 ORM이 생성하는 SQL이 PostgreSQL 전용 기능에 의존하면 PHP/MariaDB 이식
시 쿼리를 다시 설계해야 한다. 이 문서는 그런 재설계를 피하기 위해 **DB 계층이
새로 작성하는 SQL은 ANSI SQL(주로 SQL-92/SQL-99 공통 부분집합)로 제한**하고,
PostgreSQL과 MariaDB 양쪽에서 동일하게 동작하는 것을 기본 경로로 삼는다는
규칙을 명시한다.

## 적용 범위

이 정책은 아래 코드가 생성/실행하는 SQL에 적용된다.

- `src/modules/*/repository.py` (저장소 어댑터 — SQLAlchemy 사용이 허용된
  유일한 계층. [AGENTS.md](../AGENTS.md)의 계층 규칙 참고)
- `src/persistence/` 아래 ORM 모델, 트랜잭션 헬퍼
- `migrations/versions/` 아래 Alembic 마이그레이션이 생성하는 DDL
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡)

적용되지 않는 것:

- 애플리케이션 연결 문자열/드라이버 선택(`database_url`,
  `postgresql+asyncpg://`) — 이는 "어떤 DB에 붙는가"의 문제이지 "어떤 SQL을
  쓰는가"의 문제가 아니다. DSN 이중화는 0470(MariaDB DSN placeholder) 이후
  잡의 범위다.
- `redis.py` 등 SQL을 쓰지 않는 캐시/세션 어댑터.
- 테스트에서만 쓰는 SQLite 인메모리 설정(포터블리티 검증 목적이면 허용,
  프로덕션 경로가 아니므로 이 정책의 대상이 아니다).

## 기본 원칙

1. **ANSI SQL 우선.** 표준 SQL로 표현 가능한 것은 표준 SQL로 쓴다. 벤더 확장
   문법은 두 DB에서 동시에 필요할 때만, 그리고 각 DB 전용 분기로 명시적으로
   격리했을 때만 예외로 허용한다.
2. **기능 대체가 없으면 기능을 쓰지 않는다.** PostgreSQL 전용 기능이
   MariaDB에서 동등한 표준 대체재를 갖지 못하면, 그 기능 자체를 요구하지 않는
   방향으로 도메인/저장소 설계를 바꾼다. "MariaDB용 코드를 나중에 따로
   작성"하는 것을 기본 해법으로 삼지 않는다 — 두 벌 유지비용이 이식 목표를
   무력화하기 때문이다.
3. **ORM이 몰래 벤더 SQL을 생성하지 않게 한다.** SQLAlchemy의 PostgreSQL
   전용 타입/구문(`sqlalchemy.dialects.postgresql.*`)은 저장소 코드에서
   import하지 않는다. 컬럼 타입은 [persistence-boundaries.md](persistence-boundaries.md)
   에 정의된 도메인 모델 매핑을 벗어나지 않는 표준 SQLAlchemy 타입만 쓴다.
4. **정책 위반은 도구로 잡는다.** 이 문서는 규칙을 선언만 하고, 실제 자동
   검사는 0447(SQL feature denylist 검사 스크립트/테스트)에서 구현한다.
   그때까지는 코드 리뷰가 유일한 강제 수단이다.

## PostgreSQL 전용 기능 금지 목록

아래 기능은 MariaDB에 표준 대응물이 없거나 문법/의미가 달라서, 기본 경로
SQL/ORM 코드에서 **사용을 금지**한다. 각 항목의 "대체" 열은 이 엔진이 대신
쓰는 portable 방식이다.

| 금지 기능 | 왜 금지인가 | 대체 |
|---|---|---|
| `RETURNING` 절 | MariaDB(비-Galera 일반 배포)는 `INSERT/UPDATE/DELETE ... RETURNING`을 표준 지원하지 않는다 | insert 후 별도 `SELECT`로 재조회 |
| `JSONB` / `JSON` 연산자(`->`, `->>`, `@>` 등) | PostgreSQL의 `JSONB`와 연산자는 MariaDB `JSON`(TEXT 별칭)과 문법이 다르다 | 구조화된 컬럼으로 정규화하거나, 필요 시 애플리케이션에서 직렬화한 `TEXT`로 저장하고 조건 검색은 하지 않는다 |
| `ARRAY` 타입, 배열 연산자 | MariaDB에 배열 컬럼 타입이 없다 | 연결 테이블(1:N)로 정규화 |
| `ILIKE` | MariaDB에는 대소문자 무시 전용 연산자가 없다 | [정규화된 소문자 컬럼](persistence-boundaries.md) + `LIKE`, 또는 collation 기반 대소문자 무시 비교(0446 정책 참고) |
| `SERIAL` / `BIGSERIAL` / `gen_random_uuid()` / `uuid_generate_v4()` | 시퀀스/네이티브 UUID 생성 함수는 DB마다 이름과 동작이 다르다 | 애플리케이션 계층에서 문자열 ID(UUID 문자열)를 생성해 저장 ([portable-id-column-policy.md](portable-id-column-policy.md), `String(255)` PK — [persistence-boundaries.md](persistence-boundaries.md) 참고) |
| `ON CONFLICT ... DO UPDATE` (upsert) | MariaDB는 `INSERT ... ON DUPLICATE KEY UPDATE` 문법을 쓴다 (`rate-limit-design.md` 참고) | 존재 확인 후 분기(`get` 후 `create`/`update`), 또는 각 DB 전용 upsert 구문을 어댑터 내부에서 분기 |
| `SKIP LOCKED` | MariaDB 표준 배포는 `FOR UPDATE SKIP LOCKED`를 지원하지 않거나 버전 의존적이다 | 폴링 기반 잡 상태 컬럼 + 짧은 타임아웃 (0516 jobs polling 정책에서 확정) |
| `tsvector` / `tsquery` / GIN·GiST 전문 검색 인덱스 | PostgreSQL 전용 전문 검색 엔진 | `search` 모듈 어댑터가 엔진을 캡슐화 ([search-adapter-design.md](search-adapter-design.md)) — DB 전문 검색에 의존하지 않는다 |
| `DISTINCT ON` | MariaDB에 대응 구문 없음 | `GROUP BY` + 집계 함수, 또는 서브쿼리로 재작성 |
| `generate_series()` | PostgreSQL 전용 집합 반환 함수 | 애플리케이션 코드에서 시퀀스 생성 |
| `LISTEN` / `NOTIFY` | PostgreSQL 전용 pub/sub | 폴링 또는 애플리케이션 레벨 큐 (`jobs` 모듈) |
| 테이블 상속(`CREATE TABLE ... INHERITS`), 선언적 파티셔닝 전용 문법 | MariaDB 파티셔닝 문법이 다름 | 필요 시 기본키 범위 기반 애플리케이션 분할 |
| 부분 인덱스(`CREATE INDEX ... WHERE ...`), `EXCLUDE` 제약 | MariaDB 미지원 | 일반 인덱스 + 애플리케이션/서비스 계층 검증 |
| 네이티브 `ENUM` 타입(PostgreSQL `CREATE TYPE ... AS ENUM`) | PostgreSQL `ENUM` 타입과 MariaDB `ENUM` 컬럼은 생성·변경 방식이 다르다 | `VARCHAR` + 애플리케이션 레벨 값 검증(도메인 계층의 `Enum`/상수) |
| `||` 이외의 PostgreSQL 전용 문자열/날짜 함수(`age()`, `date_trunc()` 등) | MariaDB에 동일 함수 없음 | ANSI 표준 함수 또는 애플리케이션 계층 계산 |

문자열 접합 연산자 `||`, `LIMIT`/`OFFSET`(엄밀히는 ANSI 표준이 아니지만 두 DB
모두 지원하는 사실상 표준)처럼 **양쪽 DB에서 동일하게 동작하는 항목은
금지하지 않는다.** 이 목록의 기준은 "PostgreSQL 전용 문법인가"이지
"엄밀한 ANSI 표준인가"가 아니다 — 두 DB가 실질적으로 호환되면 실용적으로
허용한다.

## 허용되는 기본 SQL 표현

- 표준 타입: `VARCHAR(n)`, `TEXT`, `INTEGER`, `BIGINT`, `BOOLEAN`,
  `TIMESTAMP` (타임존 처리는 [persistence-boundaries.md](persistence-boundaries.md)
  의 `DateTime(tz)` 규칙과 0445 portable timestamp 정책을 따른다).
- 표준 제약: `PRIMARY KEY`, `FOREIGN KEY ... REFERENCES`, `UNIQUE`,
  `NOT NULL`, `CHECK`.
- 표준 조인: `INNER JOIN`, `LEFT JOIN`, 서브쿼리.
- 표준 트랜잭션 제어: `BEGIN`/`COMMIT`/`ROLLBACK`, 표준 격리 수준
  (`READ COMMITTED` 등). SQLAlchemy `AsyncSession`을 통한 사용은 계속
  허용된다 — 이는 SQL 문법이 아니라 드라이버 계층이다.
- 비재귀 `WITH` 공통 테이블 표현식. `WITH RECURSIVE`는 MariaDB 최신 버전에서
  지원하지만 최소 지원 버전을 0442 호환성 매트릭스에서 확정하기 전까지는
  새로 도입하지 않는다.

## 이 문서 이후 단계

- **0442**: 이 금지 목록을 타입/인덱스/트랜잭션/collation 차이까지 포함한
  전체 호환성 매트릭스로 확장한다.
- **0447**: 이 목록에 있는 키워드(`RETURNING`, `ILIKE`, `JSONB` 등)를 코드에서
  탐지하는 자동 검사 스크립트와 테스트를 추가해 `scripts/qa.sh`에 편입한다.
  그 전까지 이 정책은 코드 리뷰로만 강제된다.
- **0450**: 어댑터가 DB별 분기가 불가피한 지점(예: upsert)을 다룰 SQL dialect
  abstraction의 skeleton을 둔다.

## 관련 문서

- [Persistence Boundaries](persistence-boundaries.md) — 모듈별 테이블 소유권과
  저장소 패턴.
- [Search Adapter Design](search-adapter-design.md) — DB 전문 검색을 피하고
  엔진을 어댑터 뒤로 숨기는 동일한 원칙.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
