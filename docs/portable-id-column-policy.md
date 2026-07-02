# Portable ID Column Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)가 금지한
`SERIAL`/`BIGSERIAL`/`gen_random_uuid()`/`uuid_generate_v4()` 대체 방식을
구체화하고, [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)의
"ID 문자열" 항목("0444에서 정책 확정")을 확정한다. 이 문서는 정책 선언이며,
기존 코드(`src/persistence/models.py`의 `document.id`/`revision.id`,
서비스 계층의 `str(uuid.uuid4())` 호출)를 지금 바꾸지 않는다 — 이미 이
정책을 만족하고 있고, 이 문서는 그 패턴을 새 테이블에도 적용할 규칙으로
명문화하는 것이다.

## 목적

기본키를 DB 시퀀스(`SERIAL`)나 DB 네이티브 UUID 생성 함수
(`gen_random_uuid()`, `uuid_generate_v4()`)로 만들면, ID 생성 책임이 DB
엔진에 있게 된다. PostgreSQL과 MariaDB는 시퀀스/자동증가 문법과 네이티브
UUID 지원 여부가 서로 달라서, 이 방식은 이식 시점에 ID 생성 전략 자체를
다시 설계해야 한다. 이 문서는 **ID를 애플리케이션 계층에서 생성해 문자열로
저장**하는 방식을 모든 테이블의 기본으로 확정해, DB를 바꿔도 ID 생성
코드가 그대로 남게 한다.

## 적용 범위

이 정책은 아래가 정의하는 기본키(및 기본키를 참조하는 외래키) 컬럼에
적용된다.

- `migrations/versions/` 아래 Alembic 마이그레이션이 만드는 PK/FK 컬럼.
- `src/persistence/models.py`의 `id` 및 `*_id` 컬럼.
- 도메인/서비스 계층에서 ID를 생성하는 코드
  (`src/modules/*/service.py`, `audit_recorder.py` 등).
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡).

적용되지 않는 것:

- 순수 애플리케이션 내부에서만 쓰이고 DB에 저장되지 않는 임시 식별자.
- 잡 큐 등 별도 정책 문서(0447 이후)가 다루는 비-PK 상관관계 ID.

## 1. 컬럼 타입: `VARCHAR(255)` (SQLAlchemy `String(255)`)

**정책: 모든 ID 컬럼(PK/FK)은 `String(255)`(DDL 기준 `VARCHAR(255)`)로
선언한다.** PostgreSQL 네이티브 `UUID` 타입, MariaDB 전용 확장 타입 등
DB별 전용 타입은 쓰지 않는다.

- PostgreSQL의 `UUID` 타입은 MariaDB에 동등한 타입이 없다(MariaDB는
  UUID를 `CHAR(36)`/`BINARY(16)` 등으로 흉내내야 한다). 처음부터 두 DB
  모두가 표준으로 지원하는 가변 길이 문자열 타입을 쓰면 이 차이 자체가
  사라진다.
- 길이는 UUID 정규 표현(하이픈 포함 36자)보다 넉넉한 **255**로 고정한다
  ([persistence-boundaries.md](persistence-boundaries.md)의 `document.id`,
  `revision.id`가 이미 쓰는 길이). 36자로 딱 맞추지 않는 이유는, ID
  형식을 UUID가 아닌 다른 문자열(예: 접두어를 가진 식별자)로 바꿔야 할
  경우에도 컬럼 길이 마이그레이션 없이 대응하기 위해서다. 실제 저장되는
  값은 2절 형식을 따른다.
- FK 컬럼(`document_id`, `parent_revision_id` 등)은 참조하는 PK와 동일한
  `String(255)`를 쓴다([portable-schema-naming-policy.md](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의
  FK 네이밍 규칙과 짝을 이룬다).

## 2. ID 생성 방식과 형식

**정책: ID는 애플리케이션(서비스) 계층에서 `uuid.uuid4()`로 생성하고,
`str()`로 변환한 표준 UUID 문자열(하이픈 포함 소문자 36자,
`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)을 저장한다.** DB가 값을 채우는
`server_default`/`AUTO_INCREMENT`/시퀀스는 ID 컬럼에 쓰지 않는다.

- 이미 `src/modules/document/service.py`, `src/modules/revision/service.py`,
  `src/modules/discussion/service.py`, `acl`/`discussion`의
  `audit_recorder.py`가 이 패턴(`id=str(uuid.uuid4())`)을 쓰고 있다 — 이
  문서는 이 패턴을 전체 프로젝트의 기본 정책으로 명문화한다.
- 애플리케이션이 INSERT 전에 ID 값을 알고 있으므로,
  [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)가
  금지한 `RETURNING` 절(PK를 돌려받기 위한 재조회) 없이도 코드가 그대로
  동작한다 — 이 문서가 그 금지 목록의 "대체" 방법을 구체화한 것이다.
- `uuid.uuid4()`(랜덤 UUID)를 기본으로 쓰고, 시간 정렬이 필요한 순차적
  UUID(UUIDv7 등)는 이 정책의 범위 밖이다 — 필요해지면 별도 잡에서 다룬다.
- 표준 라이브러리(Python `uuid` 모듈)로 생성한 값을 `str()`로 직렬화한
  형식(소문자 하이픈 포함 36자)을 그대로 저장한다. 대문자로 바꾸거나
  하이픈을 제거하는 등 추가 가공을 하지 않는다 — 두 DB 모두 이 형식을
  가공 없이 저장/조회할 수 있고, 가공 자체가 이식 시 재현해야 할 규칙을
  늘리기 때문이다.

## 3. DB 네이티브 자동 생성 기능 금지

**정책: PK 값을 DB가 자동으로 채우게 하는 기능(`SERIAL`/`BIGSERIAL`,
`AUTO_INCREMENT`, DB 함수 `gen_random_uuid()`/`uuid_generate_v4()`,
시퀀스 `nextval()`)은 ID 컬럼에 쓰지 않는다.**

- 정수 자동증가(`SERIAL`/`AUTO_INCREMENT`)는 애초에 이 정책의 대상이
  아니다 — ID 컬럼은 1절에 따라 항상 문자열이다.
- PostgreSQL `gen_random_uuid()`/`uuid_generate_v4()`, MariaDB `UUID()`
  함수처럼 DB가 UUID 값 자체를 생성하는 기능도 쓰지 않는다. 두 함수는
  이름과 반환 형식, 필요한 확장(`pgcrypto`/`uuid-ossp`) 여부가 달라서
  이식 시 DDL을 다시 써야 한다 — 이미
  [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)의
  금지 목록에 포함된 항목이며, 이 문서는 그 항목의 "애플리케이션 계층
  생성"이라는 대체 방식을 구체화한다.
- SQLAlchemy `Column` 정의에 이 기능들에 대응하는 `server_default`나
  `autoincrement=True`를 ID 컬럼에 설정하지 않는다. `created_at`/
  `updated_at`([0445 portable timestamp 정책](portable-timestamp-column-policy.md) 대상)처럼 DB가 값을 채우는
  `server_default=func.now()` 패턴은 ID 컬럼에는 적용되지 않는다 — ID는
  항상 애플리케이션이 INSERT 이전에 값을 정한다.

## 4. 예시

기존 두 테이블이 이미 이 정책을 만족한다.

| 테이블 | PK 컬럼 | 타입 | 값 생성 위치 |
|---|---|---|---|
| `document` | `id` | `String(255)` | `src/modules/document/service.py`의 `str(uuid.uuid4())` |
| `revision` | `id` | `String(255)` | `src/modules/revision/service.py`의 `str(uuid.uuid4())` |

새 테이블도 이 표와 같은 패턴(타입 `String(255)`, 생성 위치는 해당 모듈의
서비스 계층)을 따른다.

## 이 문서 이후 단계

- **0445**([portable-timestamp-column-policy.md](portable-timestamp-column-policy.md)):
  timestamp 컬럼 정책(`created_at`/`updated_at`의 타입과 타임존 처리)을
  이 문서와 별개로 확정한다 — ID는 항상 애플리케이션 생성이라는 원칙을
  timestamp에도 확장하되, `server_default` 의존은 신규 컬럼부터 최소화하는
  방향으로 정리한다.
- **0446**: text collation 정책. ID 문자열은 UUID 형식(소문자 hex +
  하이픈)만 쓰므로 대소문자 비교 이슈가 실질적으로 발생하지 않지만,
  0446이 그 전제를 명시적으로 확인한다.
- **0447**: 이 문서가 금지한 `gen_random_uuid()`/`uuid_generate_v4()`/
  `AUTO_INCREMENT` 등을 [ANSI SQL Persistence
  Policy](ansi-sql-persistence-policy.md)의 금지 목록과 함께 코드에서
  자동 검사하는 스크립트에 포함한다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 이 문서가
  구체화한 `SERIAL`/네이티브 UUID 함수 금지 목록의 원출처.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 이 문서가
  확정한 "ID 문자열: `VARCHAR(255)` 공통" 항목의 원출처.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — PK/FK
  컬럼 이름(`id`, `<table>_id`) 네이밍 규칙.
- [Persistence Boundaries](persistence-boundaries.md) — 이 정책의 실제
  적용 사례(`document.id`, `revision.id`).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
