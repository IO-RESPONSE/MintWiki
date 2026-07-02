# Portable Backup Format

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Portable Seed Fixtures](php-db-ui-micro-job-prompts-0351-0670.md#0490-add-db-portable-seed-fixtures)와
[Python Seed Loader](php-db-ui-micro-job-prompts-0351-0670.md#0491-add-python-seed-loader-for-portable-fixtures),
[PHP Seed Loader](php-db-ui-micro-job-prompts-0351-0670.md#0492-add-php-seed-loader-for-portable-fixtures)가
구현한 portable 데이터 백업 메커니즘의 원칙을 정리한다.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)와
[Portable Schema Naming Policy](portable-schema-naming-policy.md)가 전제하는
"양쪽 DB에서 동일하게 동작"이라는 원칙을 데이터 백업/복원 단계에
적용한다. 이 문서는 정책 선언이며, 현재 코드(
`tests/fixtures/seed/*.sql`, `src/persistence/seed_loader.py`,
`php/tests/Loaders/SeedLoader.php`)는 이미 이 정책을 구현하고 있다.

## 목적

완성된 엔진을 PHP + MariaDB로 이식할 때, 개발 환경의 테스트 데이터를
두 DB 환경에서 동일하게 재현해야 한다. 또한 운영 중 데이터 백업과
복원이 PostgreSQL/MariaDB 간 이식 가능성을 해치지 않아야 한다.
이 문서는 **SQL dump(직접 실행 가능한 DDL/DML)와 JSON export(구조화된
데이터 표현)의 용도를 구분**하고, 각각의 특성과 제약을 명시하여
이식 시 두 벌 도구를 유지하는 비용을 최소화한다.

## 적용 범위

이 정책은 아래 영역에 적용된다.

- `tests/fixtures/seed/*.sql` — 개발/테스트 단계 portable seed 데이터.
- `src/persistence/seed_loader.py` — Python seed 로더 구현.
- `php/tests/Loaders/SeedLoader.php` — PHP seed 로더 구현.
- 추후 추가될 운영 백업 도구(`0497` 이후 restore 도구, `0638` 이후
  백업 다운로드 기능).

적용되지 않는 것:

- `migrations/versions/` Alembic 마이그레이션이 생성하는 스키마
  정의 — 이는 이미 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의
  대상이다.
- 단일 DB 환경(PostgreSQL만, MariaDB만) 전용 내부 도구 — 이식
  계획이 없으면 벤더 전용 기능을 쓸 수 있다.
- 특정 ORM/프레임워크에만 의존하는 serialize 형식 — 도메인 모델
  자체는 이 정책의 대상이 아니다.

## 1. 용도에 따른 포맷 선택

### SQL Dump (ANSI SQL 기반)

**목적**: 두 DB에서 그대로 실행 가능한 데이터 최상 고속 로드.

**형태**: `INSERT INTO <table> (...) VALUES (...);` 또는 `SELECT` 기반
쿼리.

**특징**:
- PostgreSQL과 MariaDB 양쪽에서 동일하게 실행된다.
- 데이터베이스 연결만 있으면 도구 없이 쿼리 하나로 로드 가능.
- 텍스트 편집으로 테스트 데이터를 직접 수정 가능.
- 주석으로 의도(문서화)를 표현 가능.

**사용 시점**:
- `tests/fixtures/seed/` — 개발/테스트 단계 seed 데이터.
- 매번 테스트 실행 전 빠른 준비 단계 필요.
- Python/PHP 양쪽 테스트 런타임에서 같은 fixture를 재현.

**제약**:
- 복잡한 데이터 구조(`nested object`, 배열)는 정규화된 여러 테이블로
  분리해야 한다 ([persistence-boundaries.md](persistence-boundaries.md)
  참고).
- 바이너리 데이터, 매우 긴 텍스트는 파일 크기가 커진다.
- 스키마 버전 마이그레이션: seed 파일은 현재 스키마 기준이며, 스키마
  변경 후 이전 seed 파일을 수동으로 업데이트해야 한다.

### JSON Export (구조화된 데이터)

**목적**: 도메인 모델과 1:1 매핑 가능한 이식성 높은 데이터 표현.

**형태**: `{"entities": [{"id": "...", "title": "...", ...}], ...}` 등
계층화된 구조.

**특징**:
- 프로그래밍 언어나 라이브러리 없이 파싱 가능(`jq` 등 표준 JSON
  도구).
- ORM 도메인 모델과 자동 매핑 가능(Python `json.load()` + `dataclass`,
  PHP `json_decode()` + DTO).
- 임베디드 관계 표현: document와 그 revision을 한 JSON 객체 안에
  표현 가능 — SQL dump처럼 여러 테이블로 분리할 필요 없음.
- 버전 정보 포함 가능: JSON 루트에 스키마 버전, 로더 호환성 정보
  기록.

**사용 시점**:
- 운영 중 데이터 백업/복원 (사용자 데이터).
- 도메인 모델 변경 후에도 호환 가능한 형식이 필요한 경우.
- 관리 도구(`0598` 이후 백업 페이지, `0639` export 정책)가 제공하는
  다운로드 형식.

**제약**:
- 로더가 필요 — 생SQL 직접 실행 불가능.
- 테이블별 로드 순서가 정해져 있어야 함(FK 참조 일관성).
- JSON 직렬화 형식의 암묵적 합의가 필요 — 예: document의 revision을
  어떻게 표현할 것인가.

## 2. SQL Dump 정책 (Seed Fixtures)

### 2.1 ANSI SQL 제약

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의 금지
  기능을 따른다.
- `INSERT INTO ... VALUES (...);` 형태만 사용 — `INSERT ... SELECT`는
  의존성이 명확하지 않아 피한다.
- 각 INSERT 문은 완전해야 한다 — 다른 fixture를 읽어 완성하는 참조를
  하지 않는다.

### 2.2 파일 규칙

- **파일 하나에 테이블 하나**: `<table>.sql` (테이블 이름과 동일).
- **폴더**: `tests/fixtures/seed/` — Python 테스트, PHP 테스트 양쪽이
  참고.
- **테이블 순서**: FK 종속성을 고려 — 참조되는 테이블(부모)이 먼저 온다.
  파일 하나일 때는 lexicographic 순서가 자동으로 순서를 정한다
  (`sorted(glob("*.sql"))` 등).

### 2.3 데이터 결정론성 (Deterministic Data)

- 모든 값은 deterministic이어야 한다 — 같은 fixture를 여러 번 로드하면
  동일한 데이터가 되어야 한다.
- UUID/ID: 생성 함수(`gen_random_uuid()` 등) 사용 금지. 고정값
  문자열로 명시한다. 예: `'doc-00001-0000-0000-0000-000000000000'`.
- Timestamp: 현재 시각 함수(`NOW()`, `CURRENT_TIMESTAMP`) 사용 금지.
  ISO 8601 UTC 문자열로 명시한다. 예:
  `'2026-01-01T00:00:00Z'`.
- 임의값(random seed): fixture에 포함하지 않는다. 시간에 따라
  달라지는 값이면 테스트 재현성이 깨진다.

### 2.4 로더 책임

#### Python (src/persistence/seed_loader.py)

- `SeedLoader` 클래스로 fixture 파일을 파싱하고 실행.
- 주석(`--`, `/* */`) 제거, `INSERT` 문 추출, 순서대로 실행.
- AsyncSession을 통해 transaction 관리 (`commit()` 호출).

#### PHP (php/tests/Loaders/SeedLoader.php)

- `SeedLoader` 클래스로 동일한 파싱/로드 로직 구현.
- PDO 또는 동일한 DB adapter를 통해 실행.
- 트랜잭션 관리 (같은 원칙).

### 2.5 재실행 안전성 (Idempotency)

- 같은 fixture를 여러 번 로드할 때 충돌 방지:
  - **방법 1 (권장)**: 로더가 로드 전에 테이블 비우기 (`DELETE FROM
    <table>;` 또는 `TRUNCATE`). 이 경우 fixture 파일 자체는 순수
    `INSERT`만 포함.
  - **방법 2 (대안)**: fixture 파일에 `DELETE` 또는 `INSERT ... ON
    CONFLICT` 같은 조건부 삽입 포함 — MariaDB는 `ON CONFLICT` 미지원
    ([ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) 참고)이므로
    권장하지 않음.
- 현재 `seed_loader.py`와 `php/tests/Loaders/SeedLoader.php`는 사전
  DELETE를 로더 책임으로 남기고, fixture 파일은 순수 `INSERT`만
  포함한다. 호출자(테스트)가 적절한 시점에 DELETE를 수행하도록
  권장한다.

## 3. JSON Export 정책 (운영 백업)

### 3.1 구조 예시

```json
{
  "export_version": "1",
  "schema_version": "2026-01-10",
  "exported_at": "2026-01-15T14:30:00Z",
  "tables": {
    "document": [
      {
        "id": "doc-uuid-1",
        "title": "Home",
        "normalized_title": "Home",
        "current_revision_id": "rev-uuid-1",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T12:00:00Z"
      },
      ...
    ],
    "revision": [
      {
        "id": "rev-uuid-1",
        "document_id": "doc-uuid-1",
        "source": "# Home",
        "author_id": "user-uuid-1",
        "parent_revision_id": null,
        "created_at": "2026-01-01T00:00:00Z"
      },
      ...
    ],
    ...
  }
}
```

### 3.2 요구 사항

- **버전 정보 포함**:
  - `export_version`: export format 자체의 버전. 로더가 호환 가능한 형식을
    판단할 기준.
  - `schema_version`: 데이터가 대응하는 DB 스키마 버전. 복원 전 마이그레이션
    필요 여부를 판단.
  - `exported_at`: 백업 생성 시각 (UTC).

- **테이블별 분리**: `tables` 객체 아래 테이블명 키로 배열 형태.
  각 배열 원소는 테이블의 한 행(record).

- **FK 참조 일관성**: 외래키 컬럼(`document_id`, `author_id` 등)은
  실제 ID 문자열 그대로 포함. 로더가 순서를 맞춰 테이블별로 삽입.

- **선택적 임베딩**: 도메인 경계에 따라 document + revision을 한 객체
  안에 임베드할지 여부는 로더 구현과 운영 정책(0639 export directory
  policy)이 정한다. 이 정책은 최소 형식만 정의한다.

### 3.3 로더 책임

- JSON 파싱 후 스키마 버전 확인.
- 호환 가능하면 `tables` 아래 배열을 순서대로 삽입.
- 호환 불가능하면 사용자에게 마이그레이션 필요 알림.
- 실패 시 rollback하거나 부분 복원 정책 명시.

### 3.4 보안 고려

- JSON export 파일은 데이터베이스 전체 내용을 포함 — 민감한 정보
  (사용자 계정, 게시글, 토론)가 있으면 접근 제어 필수.
- 백업 다운로드 기능(`0598`)은 관리자 권한 강제.
- 파일 저장 위치(`0639` export directory policy)는 웹 공개 디렉터리
  밖으로 둔다.

## 4. SQL Dump vs JSON Export 선택 기준

| 상황 | SQL Dump | JSON Export | 사유 |
|---|---|---|---|
| 개발/테스트 seed 데이터 | ✓ | | 고속, 도구 불필요, 편집 용이 |
| 매번 테스트 재준비 | ✓ | | 매 실행마다 빠른 로드 |
| 관리자 수동 백업 | | ✓ | 버전/호환성 정보 포함, 도메인 모델과 매핑 용이 |
| 운영 데이터 복원 | | ✓ | 스키마 변경 후 호환성 확인 가능 |
| 개발 환경 ↔ 프로덕션 동기화 | | ✓ | 양쪽 DB 간 이식 가능 |
| 긴급 데이터 조작(SQL 직접 실행) | ✓ | | 쿼리문 직접 편집 가능 |
| 도메인 모델 import/export | | ✓ | JSON serialization 표준 |

## 5. 스키마 버전 관리

- `db/schema/schema_version.sql` 테이블(0493)은 현재 적용된 스키마
  버전을 기록한다.
- JSON export의 `schema_version` 필드는 이 값과 대응되어야 한다.
- 복원 로더는 두 버전을 비교:
  - 같으면 바로 삽입.
  - 다르면 마이그레이션 필요 알림 또는 자동 마이그레이션 시도 (운영
    정책에 따라).

## 6. 이 문서 이후 단계

- **0497**: [Portable Restore Plan](portable-restore-plan.md) — JSON export
  복원 절차와 에러 처리를 확정한다.
- **0598** ([PHP UI backup page placeholder](php-db-ui-micro-job-prompts-0351-0670.md)):
  사용자가 데이터를 JSON export로 다운로드할 수 있는 UI 기능.
- **0639** ([Export directory policy](php-db-ui-micro-job-prompts-0351-0670.md)):
  export 파일 저장 위치 정책 (public 밖).

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — SQL dump가
  따를 기본 제약.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — 테이블/컬럼
  이름 규칙.
- [Persistence Boundaries](persistence-boundaries.md) — 테이블 소유권과 FK
  관계 정의.
- [DB Portable Seed Fixtures](php-db-ui-micro-job-prompts-0351-0670.md#0490)
  — seed fixture 포맷 기준.
- [Python Seed Loader](php-db-ui-micro-job-prompts-0351-0670.md#0491),
  [PHP Seed Loader](php-db-ui-micro-job-prompts-0351-0670.md#0492) — 현재
  구현체.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
