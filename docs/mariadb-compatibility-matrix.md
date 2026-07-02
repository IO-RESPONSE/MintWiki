# MariaDB Compatibility Matrix

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)가 선언한 금지
기능 목록을 전제로, 지금 PostgreSQL에서 쓰는 요소들이 MariaDB로 이식될 때
어떻게 대응되는지를 type / index / transaction / collation 네 축으로
정리한다. 이 문서는 매트릭스(비교표)이며, 각 항목의 상세 정책(naming,
ID, timestamp, collation)은 후속 문서(0443~0446)에서 확정한다.

## 목적과 범위

- 대상: [Persistence Boundaries](persistence-boundaries.md)에 정의된
  도메인 테이블이 사용하는 컬럼 타입, 인덱스, 트랜잭션 사용 패턴,
  문자열 정렬/비교 방식.
- 이 문서는 정책을 새로 만들지 않는다 — 이미 [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md)
  가 정한 "PostgreSQL 전용 기능 금지" 규칙을 지키는 한, 아래 매트릭스의
  "공통" 항목은 코드 변경 없이 양쪽 DB에서 그대로 동작한다.
- PHP/MariaDB 이식 시점까지 실제 드라이버 전환은 하지 않는다
  (드라이버 전환은 0470 이후 잡의 범위).

## 지원 버전

- **PostgreSQL**: 현재 개발 환경에서 쓰는 버전(`postgresql+asyncpg`,
  [config.py](../src/app/config.py)) 이상.
- **MariaDB**: 최소 지원 버전은 **10.6 LTS**로 확정한다. 이유:
  - `WITH RECURSIVE` 공통 테이블 표현식을 지원한다(MariaDB 10.2부터).
    [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#허용되는-기본-sql-표현)
    가 "0442 매트릭스에서 최소 지원 버전을 확정하기 전까지 도입하지 않는다"고
    보류했던 조건이 이 문서로 충족된다.
  - 윈도우 함수(`ROW_NUMBER()`, `RANK()` 등)를 지원한다(10.2부터).
  - `utf8mb4`가 기본 문자셋으로 쓰이는 시점 이후 버전이라 한글 저장에
    별도 설정이 필요 없다.
  - 공용 웹호스팅(README/search-adapter-design.md가 전제하는 배포 환경)에서
    LTS로 흔히 제공되는 버전이다.
  - 10.6 이후 버전(10.11 LTS 등)도 호환 대상이며, 10.6 미만 버전은
    지원하지 않는다.

## 1. 타입 매트릭스

[Persistence Boundaries](persistence-boundaries.md)에서 실제 쓰는 타입
기준. "공통"은 두 DB에서 동일한 ANSI 타입 이름과 의미로 동작한다는 뜻이다.

| 도메인 타입 | PostgreSQL | MariaDB (10.6+) | 상태 | 비고 |
|---|---|---|---|---|
| ID 문자열 | `VARCHAR(255)` | `VARCHAR(255)` | 공통 | 애플리케이션 생성 UUID 문자열 저장([portable-id-column-policy.md](portable-id-column-policy.md)에서 확정) |
| 제목/이름 | `VARCHAR(n)` | `VARCHAR(n)` | 공통 | `n` 값은 두 DB의 바이트 제한(MariaDB 행 크기 상한)을 함께 고려해 정한다 |
| 본문/장문 텍스트 | `TEXT` | `TEXT` | 공통 | MariaDB `TEXT`는 기본 인덱스 길이 제한이 있어 인덱스 컬럼으로는 쓰지 않는다(2절 참고) |
| 정수 | `INTEGER` | `INTEGER` | 공통 | |
| 큰 정수 | `BIGINT` | `BIGINT` | 공통 | |
| 불리언 | `BOOLEAN` | `BOOLEAN`(`TINYINT(1)` 별칭) | 대체 필요 | MariaDB `BOOLEAN`은 `TINYINT(1)`의 별칭일 뿐 진짜 불리언 타입이 아니다. `True`/`False` 리터럴은 양쪽에서 동작하므로 SQLAlchemy 표준 `Boolean` 타입만 쓰면 이식에 문제 없다 |
| 타임스탬프(tz) | `TIMESTAMP WITH TIME ZONE` | `TIMESTAMP`(세션 타임존 기준, 별도 tz 오프셋 저장 안 함) | 대체 필요 | MariaDB는 타임존을 컬럼에 저장하지 않는다. 애플리케이션이 항상 UTC로 정규화해 저장/조회한다(0445 portable timestamp 정책에서 확정) |
| JSON 문서 | `JSONB` | `JSON`(`LONGTEXT` 기반, 자체 연산자 없음) | 금지(정책) | [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록) 금지 목록의 `JSONB` 항목 참고 — 구조화 컬럼 또는 비질의 `TEXT`로 대체 |
| 배열 | `ARRAY` | 없음 | 금지(정책) | 연결 테이블로 정규화 |
| 열거형 | `ENUM`(네이티브 타입) | `ENUM`(컬럼 속성, 타입 아님) | 금지(정책) | `VARCHAR` + 애플리케이션 검증으로 대체 |

## 2. 인덱스 매트릭스

| 항목 | PostgreSQL | MariaDB (10.6+) | 상태 | 비고 |
|---|---|---|---|---|
| 기본 B-tree 인덱스 | `CREATE INDEX` | `CREATE INDEX` | 공통 | |
| UNIQUE 제약 | `UNIQUE` 컬럼/인덱스 | `UNIQUE` 컬럼/인덱스 | 공통 | |
| 외래키에 대한 인덱스 | 자동 생성 안 함(수동 인덱스 권장) | InnoDB가 FK 컬럼에 인덱스를 **자동 생성** | 차이(정보성) | 동작에 영향 없음 — MariaDB가 더 관대하므로 이식 시 문제 없다. Postgres 쪽에서도 FK 컬럼에 인덱스를 명시적으로 두는 걸 기본으로 삼는다 |
| 부분 인덱스(`WHERE` 절) | 지원 | 미지원 | 금지(정책) | 일반 인덱스 + 서비스 계층 검증으로 대체 |
| 함수 기반/표현식 인덱스 | 지원 | 제한적 지원(10.2+ generated column 경유) | 회피 | 저장소 코드에서 새로 도입하지 않는다. 대소문자 무시 검색은 [persistence-boundaries.md](persistence-boundaries.md)의 정규화된 컬럼 패턴을 쓴다 |
| 긴 TEXT/VARCHAR 컬럼 인덱스 | 컬럼 전체 인덱싱 가능 | InnoDB는 인덱스 prefix 길이 제한(기본 `innodb_large_prefix`로 3072바이트, `utf8mb4`에서는 문자 수 기준 더 작아짐) | 대체 필요 | `TEXT` 컬럼을 직접 인덱싱하지 않는다. 조회가 필요하면 별도 정규화된 `VARCHAR(n)` 컬럼을 두고 그 컬럼에 인덱싱한다(`document.normalized_title` 패턴) |
| 인덱스/제약 이름 길이 | 63바이트 식별자 제한 | 64자 식별자 제한 | 대체 필요 | 두 한도 중 더 짧은 63바이트를 기준으로 이름을 짓는다([portable-schema-naming-policy.md](portable-schema-naming-policy.md)에서 확정) |
| `SKIP LOCKED` | 지원 | 표준 배포 미지원/버전 의존 | 금지(정책) | 폴링 기반 폴백 (0516) |

## 3. 트랜잭션 매트릭스

| 항목 | PostgreSQL | MariaDB (10.6+, InnoDB) | 상태 | 비고 |
|---|---|---|---|---|
| 기본 격리 수준 | `READ COMMITTED` | `REPEATABLE READ` | 차이(주의) | 두 DB 모두 `READ COMMITTED`를 명시적으로 지원하므로, 저장소 코드는 격리 수준을 애플리케이션에서 명시하거나 기본값 차이를 전제로 재조회 패턴(`RETURNING` 대신 `SELECT`)을 쓴다 — [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md) 참고 |
| DDL의 트랜잭션 포함 여부 | `CREATE TABLE`/`ALTER TABLE`도 트랜잭션 안에서 롤백 가능 | DDL은 대부분 **암묵적 커밋**을 유발하며 롤백되지 않음 | 대체 필요 | Alembic 마이그레이션을 "DDL은 각 스텝이 즉시 커밋된다"는 전제로 작성한다. 여러 DDL을 하나의 논리적 트랜잭션으로 묶어 되돌릴 수 있다고 가정하지 않는다(0448 migration portability checklist에서 확정) |
| `BEGIN`/`COMMIT`/`ROLLBACK` | 표준 지원 | 표준 지원 | 공통 | SQLAlchemy `AsyncSession`을 통한 사용은 드라이버 계층이라 정책 대상 아님 |
| 행 잠금(`SELECT ... FOR UPDATE`) | 지원 | 지원(InnoDB) | 공통 | `SKIP LOCKED`/`NOWAIT` 확장 문법은 위 인덱스 표의 금지 항목 참고 |
| Deadlock 처리 | 자동 감지 후 하나의 트랜잭션을 중단 | 자동 감지 후 하나의 트랜잭션을 중단 | 공통 | 애플리케이션은 재시도 로직을 DB 특정 오류 메시지가 아닌 표준 오류 클래스로 판단한다(0474 duplicate key 처리 정책과 동일한 원칙) |
| Upsert | `INSERT ... ON CONFLICT DO UPDATE` | `INSERT ... ON DUPLICATE KEY UPDATE` | 금지(정책) | 존재 확인 후 분기, 또는 어댑터 내부 DB별 분기 |

## 4. Collation 매트릭스

상세 정책은 0446(portable text collation policy)에서 확정한다. 이 절은
그 정책이 다뤄야 할 차이를 매트릭스로 미리 정리한다.

| 항목 | PostgreSQL | MariaDB (10.6+) | 상태 | 비고 |
|---|---|---|---|---|
| 기본 문자열 비교 | 기본적으로 대소문자 구분(`LIKE`, `=`) | collation에 따라 다름 — 흔한 기본값(`utf8mb4_general_ci`, `utf8mb4_unicode_ci`)은 **대소문자 비구분** | 대체 필요 | 대소문자 구분 비교가 필요한 컬럼(예: ID, 코드값)은 명시적으로 `_bin`/`_cs` collation 또는 정규화된 컬럼을 쓴다. 반대로 `ILIKE`가 필요했던 자리는 MariaDB의 대소문자 비구분 기본 collation으로 대체 가능(정책 확정은 0446) |
| 한글 정렬 순서 | ICU/locale collation(`ko-KR-x-icu` 등) 설정 가능 | `utf8mb4_unicode_ci`/`utf8mb4_0900_ai_ci`류의 유니코드 기반 정렬, ICU locale collation은 없음 | 차이(주의) | 완전히 동일한 정렬 순서를 보장하지 않는다. 한글 제목 정렬은 "완전한 사전순 일치"가 아니라 "유니코드 코드포인트 기반 안정적 정렬"을 목표로 삼는다. 실제 fixture 검증은 0511(MariaDB collation fixture tests)에서 진행 |
| 대소문자 무시 검색(`ILIKE`) | 네이티브 연산자 | 없음 — collation 또는 `LOWER()` 비교로 대체 | 금지(정책) | [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록) 참고. portable LIKE 정책은 0512에서 확정 |
| 문자셋 | `UTF8`(PostgreSQL 인코딩) | `utf8mb4` (4바이트 UTF-8, 이모지/일부 한자 포함) | 대체 필요 | MariaDB 쪽은 반드시 `utf8mb4`를 쓴다(3바이트 `utf8`은 일부 유니코드 문자를 저장하지 못한다). 스키마 생성 시 데이터베이스/테이블 기본 문자셋을 `utf8mb4`로 명시한다 |
| 중복키 오류 시 대소문자 취급 | collation과 무관하게 바이트 단위 UNIQUE 위반 | UNIQUE 인덱스가 대소문자 비구분 collation이면 대소문자만 다른 값도 중복으로 판정 | 대체 필요 | `normalized_title`처럼 애플리케이션이 정규화한 컬럼에 UNIQUE를 걸 때, MariaDB 기본 collation에서는 대소문자 차이만으로는 별도 값으로 취급되지 않을 수 있다는 점을 전제로 정규화 규칙을 설계한다 |

## 이 문서 이후 단계

- **0443**([portable-schema-naming-policy.md](portable-schema-naming-policy.md)),
  **0444**([portable-id-column-policy.md](portable-id-column-policy.md))**~0446**:
  이 매트릭스의 개별 항목(naming, ID, timestamp, collation)을 실행 가능한
  정책으로 확정한다.
- **0447**: 금지 목록(타입/인덱스/트랜잭션 표의 "금지(정책)" 항목)을
  코드에서 자동 탐지하는 스크립트를 추가한다.
- **0511**: 이 매트릭스의 "차이(주의)" 항목 중 한글 정렬/collation을
  fixture 테스트로 검증한다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 이 매트릭스가
  전제하는 금지 기능 목록과 허용 SQL 표현.
- [Persistence Boundaries](persistence-boundaries.md) — 이 매트릭스가 기준으로
  삼은 실제 도메인 테이블 타입 정의.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
