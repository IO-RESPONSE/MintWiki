# Portable Timestamp Column Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)와
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)가 "대체
필요"로 표시한 타임스탬프(tz) 항목을 구체화하고,
[Portable ID Column Policy](portable-id-column-policy.md)가 예고한
`created_at`/`updated_at` 정책을 확정한다. 이 문서는 정책 선언이며, 기존
코드(`src/persistence/models.py`의 `DocumentORM`/`RevisionORM`,
`server_default=func.now()`)를 지금 바꾸지 않는다 — 이 정책은 **새로
추가되는** timestamp 컬럼부터 적용하고, 기존 두 컬럼은 별도 마이그레이션
잡 없이는 소급 변경하지 않는다.

## 목적

PostgreSQL의 `TIMESTAMP WITH TIME ZONE`은 값을 항상 UTC로 정규화해 저장하고
조회 시 세션 타임존으로 변환해 보여주지만, MariaDB의 `TIMESTAMP`는 오프셋을
저장하지 않고 **세션 `time_zone` 설정**에 따라 같은 SQL이 다른 실제 시각을
저장할 수 있다([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#1-타입-매트릭스)의
"타임스탬프(tz)" 항목). 여기에 더해, DB가 값을 채우는
`server_default=func.now()`/`onupdate=func.now()`는 PostgreSQL과 MariaDB가
각각 다른 함수(`now()` vs `CURRENT_TIMESTAMP()`)로 번역되고, 그 결과가
서버/세션 설정에 의존한다는 점에서 [portable-id-column-policy.md](portable-id-column-policy.md)가
피하려 했던 "DB 엔진에 책임이 있는 값 생성"과 같은 문제를 갖는다. 이 문서는
**모든 timestamp 값을 애플리케이션이 UTC로 생성**해, DB 세션 설정이나
엔진별 함수 차이가 저장되는 값에 영향을 주지 않게 한다.

## 적용 범위

이 정책은 아래가 정의하는 timestamp 컬럼에 적용된다.

- `migrations/versions/` 아래 Alembic 마이그레이션이 만드는 `created_at`,
  `updated_at`, 그 외 시각을 저장하는 컬럼(`occurred_at`, `closed_at` 등).
- `src/persistence/models.py`의 `DateTime` 컬럼.
- 도메인/서비스 계층에서 시각 값을 만드는 코드
  (`src/modules/*/service.py`, `audit_recorder.py` 등).
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡).

적용되지 않는 것:

- 순수 애플리케이션 내부 로깅/메트릭 타임스탬프로, DB에 저장되지 않는 값.
- 기존 `document.created_at`/`document.updated_at`/`revision.created_at`
  (`server_default=func.now()`) — 4절에서 다룬다.

## 1. 컬럼 타입: `DateTime(timezone=True)` (SQLAlchemy)

**정책: 모든 timestamp 컬럼은 SQLAlchemy `DateTime(timezone=True)`(DDL 기준
PostgreSQL `TIMESTAMP WITH TIME ZONE`, MariaDB `TIMESTAMP`)로 선언한다.**

- MariaDB `TIMESTAMP`는 PostgreSQL `TIMESTAMP WITH TIME ZONE`처럼 오프셋을
  함께 저장하지 않는다 — 저장되는 값 자체가 "그 값이 UTC라는 애플리케이션
  차원의 약속"으로만 성립한다. 2절이 이 약속을 강제하는 규칙이다.
- MariaDB `DATETIME`(타임존 개념 자체가 없는 타입)은 쓰지 않는다.
  `TIMESTAMP`를 쓰는 이유는 두 DB 모두에서 "시각"이라는 의미가 있는 표준
  타입 이름을 유지하기 위해서다 — 실제 tz 오프셋 저장 여부의 차이는 2절의
  UTC 정규화로 흡수한다.
- MariaDB `TIMESTAMP`는 연도 범위가 1970~2038(전통적 32비트 유닉스 타임)로
  제한될 수 있다(버전/설정에 따라 다름). 이 프로젝트 도메인(문서 작성
  시각)은 이 범위를 벗어나지 않으므로 지금은 별도 대응을 두지 않는다 —
  범위를 벗어나는 값이 필요해지면 별도 잡에서 다룬다.

## 2. UTC 정규화 저장

**정책: 애플리케이션이 다루는 모든 datetime 값은 timezone-aware이며 항상
UTC(`timezone.utc`)로 정규화한다.** naive datetime(tzinfo 없는 값)을
timestamp 컬럼에 쓰지 않는다.

- 이미 `src/modules/discussion/service.py`, `acl`/`discussion`의
  `audit_recorder.py`, `acl/router.py`가 `datetime.now(timezone.utc)`
  패턴을 쓰고 있다 — 이 문서는 이 패턴을 전체 프로젝트의 기본 정책으로
  명문화한다.
- 로컬 타임존(`datetime.now()`, `datetime.utcnow()`)은 쓰지 않는다.
  `datetime.now()`는 서버 로컬 타임존에 의존해 환경마다 다른 값을 만들고,
  `datetime.utcnow()`는 UTC 값이지만 naive datetime을 반환해 tz 정보가
  없다는 점에서 이 정책이 요구하는 "명시적으로 UTC임을 아는 값"이 아니다.
- 조회한 값을 사용자에게 보여줄 때 로컬 타임존으로 변환하는 것은 UI/표현
  계층의 책임이며, 이 정책이 다루는 저장/전달 값은 항상 UTC로 유지한다.

## 3. DB 서버 사이드 default 의존 최소화

**정책: 새로 추가하는 timestamp 컬럼은 `server_default=func.now()` /
`onupdate=func.now()`에 의존하지 않는다. 대신 애플리케이션(서비스) 계층이
INSERT/UPDATE 이전에 `datetime.now(timezone.utc)` 값을 채워 전달한다.**
이는 [portable-id-column-policy.md](portable-id-column-policy.md#2-id-생성-방식과-형식)가
ID 컬럼에 이미 적용한 "애플리케이션이 값을 정하고 DB는 그 값을 그대로
저장한다"는 원칙을 timestamp 컬럼에도 확장한 것이다.

- **왜 최소화하는가.** `func.now()`는 SQLAlchemy가 각 방언(dialect)의
  네이티브 함수로 번역한다 — PostgreSQL은 `now()`(트랜잭션 시작 시각,
  `TIMESTAMPTZ`라 오프셋 포함), MariaDB는 `CURRENT_TIMESTAMP()`(세션
  `time_zone` 설정 기준 시각, 오프셋 미포함)로 각각 다르게 동작한다. 두
  DB의 세션 타임존 설정이 항상 UTC로 맞춰져 있다는 보장이 없으므로(특히
  [mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#지원-버전)가
  전제하는 공용 웹호스팅 환경), 같은 DDL이 배포 환경에 따라 다른 실제
  시각을 저장할 위험이 있다. 애플리케이션이 값을 직접 생성하면 이 위험이
  사라진다 — DB 세션 설정과 무관하게 저장되는 값이 결정된다.
- **적용 방법.** 도메인/서비스 계층에서 엔티티를 생성할 때
  `created_at=datetime.now(timezone.utc)`처럼 값을 명시적으로 채우고,
  ORM `Column` 정의에는 `server_default`/`onupdate`를 두지 않는다. `updated_at`
  갱신도 서비스 계층이 새 값을 계산해 전달한다(SQLAlchemy `onupdate=` 콜백에
  위임하지 않는다).
- **"최소화"이지 "전면 금지"가 아닌 이유.** 마이그레이션이 기존 행을
  채우는 backfill(`server_default`로 과거 데이터에 값을 한 번 채우는 경우)처럼,
  애플리케이션 계층이 관여하지 않는 좁은 시나리오에서는 `server_default`
  사용이 여전히 실용적일 수 있다. 이런 예외는 사용하는 잡에서 그 근거를
  명시하고, 저장되는 값이 실제로 UTC인지(세션 타임존 확인)를 함께
  검증한다.

## 4. 기존 컬럼과의 관계

`document.created_at`/`document.updated_at`/`revision.created_at`은 현재
`server_default=func.now()`(및 `document.updated_at`은 `onupdate=func.now()`)를
쓴다. 이 정책은 이 세 컬럼을 지금 변경하지 않는다.

- PostgreSQL 단일 엔진으로 운영 중인 현재 시점에는 이 컬럼들이 관찰 가능한
  버그를 만들지 않는다 — 위험은 MariaDB로 이식할 때 세션 타임존이
  UTC가 아니면 드러난다.
- 이 컬럼들을 3절 정책에 맞게 애플리케이션 값 생성 방식으로 옮기는 작업은
  별도 마이그레이션 잡(스키마 변경 없이 `server_default` 제거 + 서비스
  계층에 값 채우기 추가)으로 다룬다 — 이 문서는 정책만 확정하고 코드
  변경은 범위 밖이다.
- 새 테이블/컬럼은 이 컬럼들을 참고 삼지 않는다 — 3절이 신규 컬럼의
  기준이다.

## 5. 예시

| 테이블 | 컬럼 | 타입 | 값 생성 방식 | 이 정책 적용 여부 |
|---|---|---|---|---|
| `document` | `created_at`/`updated_at` | `DateTime(timezone=True)` | `server_default=func.now()`(`updated_at`은 `onupdate=func.now()` 추가) | 기존 컬럼 — 4절에 따라 지금 변경하지 않음 |
| `revision` | `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` | 기존 컬럼 — 4절에 따라 지금 변경하지 않음 |
| (신규 테이블) | `created_at`/`updated_at` | `DateTime(timezone=True)` | 서비스 계층의 `datetime.now(timezone.utc)` | 3절 정책 적용 대상 |

## 이 문서 이후 단계

- **0446**([portable-text-collation-policy.md](portable-text-collation-policy.md)):
  text collation 정책. timestamp는 문자열 비교/collation 대상이 아니므로
  이 문서와 독립적이지만, 두 문서 모두
  [mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md)의
  "대체 필요" 항목을 구체화한다는 점에서 짝을 이룬다.
- **0447**: 이 문서가 최소화 대상으로 지정한 `server_default=func.now()`/
  `onupdate=func.now()` 신규 사용, naive datetime 저장 등을 코드에서
  자동 검사하는 스크립트에 포함한다.
- 기존 `document`/`revision` timestamp 컬럼을 3절 방식으로 전환하는 작업은
  후속 스키마 정리 잡(번호 미정)에서 다룬다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 이 문서가
  구체화한 `TIMESTAMP WITH TIME ZONE` 허용 표현의 원출처.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 이 문서가
  확정한 "타임스탬프(tz): UTC 정규화" 항목의 원출처.
- [Portable ID Column Policy](portable-id-column-policy.md) — "애플리케이션이
  INSERT 이전에 값을 정한다"는 원칙을 timestamp 컬럼까지 확장한 근거.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) —
  `created_at`/`updated_at` 컬럼 이름 규칙(타입/타임존 규칙은 이 문서가 정함).
- [Persistence Boundaries](persistence-boundaries.md) — 이 정책이 다루는
  기존 timestamp 컬럼의 실제 적용 사례.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
