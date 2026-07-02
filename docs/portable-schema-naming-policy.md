# Portable Schema Naming Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)와
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)가 전제하는
"양쪽 DB에서 동일하게 동작"이라는 원칙을, 테이블/컬럼/인덱스/제약 **이름**에
적용한다. 매트릭스 문서가 보류했던 "식별자 이름 길이" 항목을 이 문서가
확정한다. 이 문서 자체는 정책 선언이며, 기존 테이블(`document`, `revision`)
이름을 지금 바꾸지 않는다 — 둘 다 이미 이 정책을 만족한다.

## 목적

PHP + MariaDB로 이식할 때 테이블/컬럼/인덱스 이름이 그대로 옮겨가야
재작성 비용이 없다. PostgreSQL과 MariaDB는 식별자 길이 제한과 예약어
목록이 서로 달라서, 한쪽에서만 유효한 이름을 지으면 이식 시점에 스키마
전체를 리네이밍해야 한다. 이 문서는 **두 DB 모두에서 그대로 유효한
이름만 짓는다**는 규칙을 새 테이블/컬럼/인덱스를 설계할 때부터 적용하기
위한 기준을 정한다.

## 적용 범위

이 정책은 아래가 정의하는 식별자에 적용된다.

- `migrations/versions/` 아래 Alembic 마이그레이션이 만드는 테이블,
  컬럼, 인덱스, 제약(PK/FK/UNIQUE/CHECK) 이름.
- `src/persistence/models.py`의 `__tablename__`과 `Column` 이름.
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡).

적용되지 않는 것:

- Python 코드 식별자(변수명, 클래스명 등) — 언어 레벨 컨벤션은 별개다.
- 테스트 전용 SQLite 스키마의 임시 이름(프로덕션 스키마와 무관하면 예외).

## 1. 식별자 길이 제한

| DB | 한도 | 근거 |
|---|---|---|
| PostgreSQL | 63바이트 | `NAMEDATALEN`(64) - 1. 초과분은 조용히 잘려서, 서로 다른 두 이름이 같은 이름으로 충돌할 수 있다 |
| MariaDB | 64자 | 테이블/컬럼/인덱스 식별자 한도. 초과 시 에러(잘리지 않음) |

**정책: 모든 식별자는 63바이트 이하로 짓는다.** 두 한도 중 더 짧은 쪽을
기준으로 삼아, 이식 시점에 어느 쪽도 다시 손댈 필요가 없게 한다
([MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md#2-인덱스-매트릭스)의
"인덱스/제약 이름 길이" 항목이 이 문서에서 확정하기로 보류했던 항목).

- PostgreSQL의 63바이트는 **바이트** 단위, MariaDB의 64자는 **문자** 단위다.
  식별자를 ASCII 영문 소문자/숫자/밑줄로만 지으면(2절 참고) 1문자 = 1바이트라
  이 차이가 실제로 문제되지 않는다. 한글 등 멀티바이트 문자를 식별자에
  쓰지 않는 것이 이 정책이 ASCII만 허용하는 이유이기도 하다.
- 63바이트를 넘길 위험이 가장 큰 대상은 자동 생성되는 인덱스/제약 이름이다
  (4절 네이밍 패턴 참고). 컬럼/테이블 이름 자체를 짧게 지으면 조합 이름도
  대체로 한도 안에 든다.
- 조합 이름이 그래도 63바이트를 넘으면, 마지막 구성요소(주로 컬럼명)를
  축약하거나 여러 컬럼을 나열하는 대신 인덱스 목적을 나타내는 짧은 태그로
  대체한다. 해시를 덧붙여 억지로 유일성만 맞추는 방식은 쓰지 않는다 —
  이름만 보고 무엇을 위한 인덱스인지 알 수 없게 되기 때문이다.

## 2. 문자·대소문자 규칙

**정책: 테이블/컬럼/인덱스 이름은 소문자 ASCII, 숫자, 밑줄(`_`)만 쓴다.
대문자, 공백, 하이픈, 멀티바이트 문자는 쓰지 않는다.**

이유는 길이 문제보다 크다 — MariaDB는 `lower_case_table_names` 서버 설정에
따라 테이블 이름의 대소문자 구분 여부가 **운영체제/서버 설정 의존적**이다
(Linux 기본은 대소문자 구분, 다른 환경 설정에서는 비구분으로 동작할 수
있다). PostgreSQL은 따옴표 없는 식별자를 항상 소문자로 접어서(fold) 다룬다.
두 DB 모두에서 항상 동일하게 동작하는 유일한 선택은 **애초에 소문자만
쓰는 것**이다. 컬럼/인덱스 이름도 동일한 이유로 소문자로 통일한다(MariaDB는
컬럼/인덱스 이름을 항상 대소문자 구분하지만, 정책을 테이블 이름과
일관되게 유지하기 위해 전체를 소문자로 고정한다).

## 3. 테이블·컬럼 네이밍 규칙

기존 테이블(`document`, `revision`, [Persistence Boundaries](persistence-boundaries.md)
참고)이 이미 따르고 있는 패턴을 명문화한다.

- **테이블 이름은 단수형**을 쓴다 (`document`, `revision` — `documents`,
  `revisions` 아님). 새 테이블도 이 패턴을 따른다.
- **기본키 컬럼은 `id`**로 짓는다. 접두사(`document_id` 등)를 테이블
  자기 자신의 PK에는 붙이지 않는다.
- **외래키 컬럼은 `<참조 테이블 단수형>_id`**로 짓는다 (`document_id`,
  `parent_revision_id`처럼 관계의 의미가 필요하면 관계명을 접두어로 추가).
- **타임스탬프 컬럼은 `created_at` / `updated_at`**로 통일한다
  ([ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md)와
  0445 portable timestamp 정책이 다루는 타입/타임존 규칙과 별개로, 이름
  자체는 이 정책이 정한다).
- **불리언 컬럼은 `is_`/`has_` 접두어**를 쓴다 (예: `is_deleted`,
  `has_conflict`). 접두어 없는 동사형 이름(`deleted`, `locked`)은 쓰지 않는다.
- **정규화된 조회용 컬럼은 `normalized_`/`_normalized` 같은 명시적 접두/접미어**로
  원본 컬럼과 구분한다 (`document.normalized_title` 패턴,
  [persistence-boundaries.md](persistence-boundaries.md) 참고).
- 약어보다 온전한 단어를 쓴다. 단, 이미 도메인 전반에서 쓰이는 짧은 이름
  (`id`)은 예외로 유지한다.

## 4. 인덱스·제약 이름 패턴

Alembic이 이름을 자동 생성하게 두면 DB마다 규칙이 달라 예측할 수 없는
이름이 나온다. 이를 막기 위해 아래 접두어 기반 패턴을 **명시적으로** 쓴다.

| 종류 | 패턴 | 예시 |
|---|---|---|
| Primary Key | `pk_<table>` | `pk_document` |
| Foreign Key | `fk_<table>_<column>` | `fk_revision_document_id` |
| Unique 제약/인덱스 | `uq_<table>_<column>` | `uq_document_normalized_title` |
| 일반 인덱스 | `ix_<table>_<column>` | `ix_revision_document_id` |
| Check 제약 | `ck_<table>_<의도를 나타내는 짧은 태그>` | `ck_revision_summary_not_blank` |

- `<column>`이 여러 컬럼으로 구성된 복합 인덱스면 밑줄로 이어 붙인다
  (`ix_<table>_<col1>_<col2>`). 이 조합이 63바이트(1절)를 넘으면 컬럼
  나열 대신 인덱스 목적을 나타내는 짧은 태그로 줄인다.
- 이 패턴은 SQLAlchemy `MetaData(naming_convention={...})`로 자동화할 수
  있으나, 실제 적용(`src/persistence/base.py`의 `metadata` 객체 변경)은
  이 문서의 범위가 아니다 — 코드 변경 없이 정책만 확정한다. 적용 시점은
  0447(금지 기능 자동 검사 스크립트) 또는 이후 스키마 정리 잡에서 다룬다.
- 기존 두 테이블(`document`, `revision`)은 현재 명시적 제약 이름을 쓰지
  않고 SQLAlchemy/DB 기본 생성 이름에 의존한다. 이 정책은 **새로 추가되는**
  제약/인덱스부터 적용하며, 기존 제약을 소급 리네이밍하지 않는다.

## 5. 예약어 회피

**정책: 테이블/컬럼/인덱스 이름으로 PostgreSQL 또는 MariaDB의 예약어를
쓰지 않는다.** 두 DB 중 하나에서만 예약어이더라도 회피 대상이다 — 지금
PostgreSQL에서 문제없이 동작해도 MariaDB 이식 시점에 깨지는 이름을 새로
만들지 않기 위해서다.

두 DB 모두에서 특히 자주 부딪히는 이름(도메인 설계 시 흔히 떠올리기 쉬운
단어들)을 예시로 남긴다 — 전체 예약어 목록은 각 DB 공식 문서를 기준으로
삼고, 아래는 그중 이 프로젝트 도메인(문서/리비전/토론/ACL/잡 큐)과 겹칠
가능성이 높은 항목만 추린 것이다.

| 회피해야 할 이름 | 대체 예시 |
|---|---|
| `user` | `account`, `author`(이미 `revision.author_id`가 쓰는 패턴) |
| `order` | `sort_order`, `display_order` |
| `group` | `namespace_group`, `permission_group` |
| `key` | `cache_key`, `api_key`처럼 접두어를 붙여 구체화 |
| `condition` | `acl_condition`처럼 구체화, 또는 `rule` |
| `check` | `validation_check` 대신 의미를 드러내는 이름(`is_valid` 등) |
| `role` | `acl_role`, `permission_role` |
| `level` | `access_level`, `severity_level` |
| `value` / `values` | `payload_value`, `setting_value` |
| `table` | `table` 자체를 컬럼/테이블 이름으로 쓰지 않는다 — 메타 개념 이름은 항상 회피 |
| `read` / `write` | `Permission` enum 값(`read`, `write`류)은 애플리케이션 문자열 값으로만 저장하고, 컬럼/테이블 이름으로는 쓰지 않는다 |
| `timestamp` | `created_at`/`updated_at`(3절 패턴)으로 대체하므로 원천적으로 등장하지 않는다 |
| `default` | `default_value`, `is_default` |

- 이 표는 회피 대상 전수 목록이 아니라 자주 나오는 함정 예시다. 새 이름을
  지을 때 의심되면 PostgreSQL/MariaDB 예약어 목록을 확인하고, 확실치 않으면
  접두어를 붙여 구체화하는 쪽(3절의 컬럼 네이밍 규칙과 동일한 원칙)을
  기본으로 삼는다.
- 예약어라도 따옴표(PostgreSQL `"order"`, MariaDB `` `order` ``)로 감싸면
  기술적으로는 쓸 수 있다. 이 정책은 그 방식을 **금지**한다 — 매 쿼리마다
  방언별 인용 문자를 다르게 다뤄야 해서 [ANSI SQL Persistence
  Policy](ansi-sql-persistence-policy.md)가 지향하는 "SQL을 그대로 이식"
  원칙과 어긋난다.

## 이 문서 이후 단계

- **0444**([portable-id-column-policy.md](portable-id-column-policy.md))**~0446**:
  ID, timestamp, collation 컬럼 정책을 이 네이밍 규칙 위에서 확정한다.
- **0447**: 이 문서의 예약어 회피 규칙과 [ANSI SQL Persistence
  Policy](ansi-sql-persistence-policy.md)의 금지 기능 목록을 함께 코드에서
  자동 검사하는 스크립트를 추가한다.
- 새 테이블/컬럼/인덱스를 추가하는 이후 모든 DB 관련 잡은 이 문서의
  1~5절 규칙을 전제로 이름을 짓는다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 이 정책이
  전제하는 "SQL을 그대로 이식" 원칙.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 이 문서가
  확정한 63바이트 식별자 길이 한도를 인용한 원출처.
- [Persistence Boundaries](persistence-boundaries.md) — 이 정책이 명문화한
  기존 테이블/컬럼 네이밍 패턴의 실제 사례.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
