# Portable Restore Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[Portable Backup Format](portable-backup-format.md)에서 정의한 SQL dump(seed fixtures)와
JSON export(운영 백업) 형식을 PostgreSQL/MariaDB 양쪽에서 동일하게 복원하는 절차와
에러 처리 전략을 정의한다. 이 문서는 정책 선언이며, 향후 구현되는 restore 도구들
(`0598` 이후 백업 관리 UI, `0639` export 디렉토리 정책)이 따를 기준을 제공한다.

## 목적

완성된 엔진을 PostgreSQL과 MariaDB 환경에서 실행할 때, 백업 데이터의 복원 절차가
두 DB 간 이식 가능해야 한다. 복원 중 발생한 에러(스키마 호환성, 데이터 무결성,
외래키 제약)를 일관되게 처리해 양쪽 DB에서 예측 가능한 결과를 얻어야 한다.
또한 부분 복원, 재복원, 롤백 등 운영 시나리오에서 데이터 일관성을 보장해야 한다.

## 적용 범위

이 정책은 아래 영역에 적용된다.

- SQL dump(`tests/fixtures/seed/*.sql`) 복원 — `src/persistence/seed_loader.py`,
  `php/tests/Loaders/SeedLoader.php`가 구현하는 로더.
- JSON export 복원 — 운영 백업(0598 이후 백업 다운로드)에서 사용자가 업로드한 JSON
  파일을 받아 복원하는 로더 및 UI 핸들러.
- 마이그레이션 이후 백업 데이터 복원 — 스키마 버전이 다른 백업에서 복원할 때의
  호환성 검사 및 알림 절차.

적용되지 않는 것:

- 데이터베이스 연결 구성 및 DB 인스턴스 생성 — restore 도구는 기존 DB 연결이
  있다고 가정한다.
- 백업 파일의 암호화, 압축, 전송 — 이는 백업 저장소 정책(0639)이 담당한다.
- Alembic 마이그레이션 실행 — schema version 확인과 마이그레이션 필요성 알림만 정책이며,
  실제 마이그레이션 실행은 별도 절차이다.

## 1. 복원 절차의 공통 원칙

### 1.1 준비 단계

복원을 시작하기 전에 아래를 확인한다.

1. **DB 연결 확인**: 대상 PostgreSQL/MariaDB 인스턴스가 접속 가능한지 테스트.
   실패하면 "Cannot connect to database" 에러로 복원 중단.

2. **스키마 버전 확인**:
   - 현재 DB의 `schema_version` 테이블에서 schema version 조회.
   - 복원할 백업(SQL dump 또는 JSON export)의 버전과 비교.
   - **같은 버전**: 복원 진행.
   - **다른 버전**: 하단 "2절. 스키마 버전 호환성 검사" 참고.

3. **백업 파일 검증**:
   - SQL dump: 파일 포맷 (UTF-8 인코딩, 유효한 SQL 구문).
   - JSON export: JSON 파싱 가능 여부, 필수 필드(`export_version`,
     `schema_version`, `tables`) 존재 확인.
   - 실패하면 "Invalid backup file" 에러.

### 1.2 트랜잭션 및 격리

모든 복원 작업은 데이터베이스 트랜잭션 내에서 수행한다.

- **시작**: 복원 시작 직후 트랜잭션 시작 (`BEGIN;` 또는 ORM 트랜잭션).
- **커밋/롤백**:
  - 모든 테이블 삽입 완료 후 `COMMIT;`.
  - 중간에 에러 발생 시 `ROLLBACK;` (모든 변경 사항 취소).
- **격리 수준**: 기본값 사용 (PostgreSQL: READ COMMITTED, MariaDB: REPEATABLE READ).
  복원 중 다른 클라이언트의 읽기/쓰기는 격리 수준에 따라 처리.

### 1.3 테이블 로드 순서

SQL dump와 JSON export 모두 외래키 제약을 만족하도록 테이블을 순서대로 로드한다.

- [Persistence Boundaries](persistence-boundaries.md)에서 정의한 FK 종속성 순서 준용.
- 부모 테이블(참조되는 테이블)이 먼저 로드되어야 함.
- 예시:
  - `user` → `document` → `revision` → `revision_edit` 순서.
  - `acl_permission` → `acl_grant` 순서.

로더는 각 백업 형식에서 명시적으로 또는 암묵적으로 이 순서를 보장해야 한다.

## 2. 스키마 버전 호환성 검사

### 2.1 버전 비교

복원하기 전에 현재 DB 스키마 버전과 백업 파일의 버전을 비교한다.

```
현재 DB 버전: 2026-01-15
백업 버전: 2026-01-10
```

### 2.2 동일 버전 (버전 일치)

- **조건**: `현재 DB 버전 == 백업 버전`
- **조치**: 복원 진행.
- **설명**: 스키마가 동일하므로 데이터를 그대로 로드 가능.

### 2.3 불일치 버전 (버전 다름)

#### 2.3.1 백업이 더 오래된 경우 (구 버전 백업)

```
현재 DB 버전: 2026-01-15
백업 버전: 2026-01-10
```

- **조치**: 사용자에게 경고를 표시하고 계속 진행 여부 확인.
  ```
  경고: 백업이 구버전(2026-01-10)입니다.
  현재 스키마(2026-01-15)와 다릅니다.
  복원 후 데이터가 손실되거나 불완전할 수 있습니다.
  계속하시겠습니까? [Y/n]
  ```
- **복원 진행**: 사용자가 동의하면, 다음 절차 중 하나 선택:
  1. **자동 마이그레이션** (구현 기준에 따라):
     - Alembic 마이그레이션 자동 실행 후 데이터 로드.
     - 마이그레이션 실패 시 복원 중단 및 롤백.
  2. **수동 마이그레이션** (기본값):
     - 사용자에게 "먼저 스키마를 마이그레이션한 후 재시도하세요" 메시지.
     - 복원 중단 (롤백).

#### 2.3.2 백업이 더 최신인 경우 (신 버전 백업)

```
현재 DB 버전: 2026-01-10
백업 버전: 2026-01-15
```

- **조치**: 에러 메시지 출력, 복원 중단.
  ```
  에러: 백업이 현재 스키마보다 최신입니다.
  백업 버전: 2026-01-15
  현재 버전: 2026-01-10
  먼저 현재 스키마를 업그레이드하세요.
  ```
- **설명**: 신 버전 백업을 구 버전 DB로 복원할 수 없음 (데이터 손상 위험).

### 2.4 버전 정보 없는 경우

SQL dump(`tests/fixtures/seed/*.sql`)는 `schema_version` 필드가 없다.

- **조치**: 스키마 버전 검사 생략, 바로 복원 진행.
- **설명**: seed fixture는 개발/테스트 용도로 현재 스키마를 가정.

## 3. SQL Dump 복원 절차 (Seed Loader)

### 3.1 파일 로드

`seed_loader.py` 및 `php/tests/Loaders/SeedLoader.php`가 구현하는 절차.

1. **파일 읽기**: `tests/fixtures/seed/*.sql` 파일을 lexicographic 순서로 로드.
2. **SQL 파싱**:
   - 주석 제거 (`--`, `/* */`).
   - `INSERT INTO ...;` 문만 추출.
   - 다른 문(SELECT, UPDATE, DELETE 등)은 무시 (seed는 INSERT만 포함).
3. **문 실행**:
   - 트랜잭션 내에서 순서대로 실행 (`BEGIN ... COMMIT`).
   - 실패 시 롤백 (모든 변경 취소).

### 3.2 MariaDB vs PostgreSQL 차이

#### INSERT 문법

**PostgreSQL** (standard):
```sql
INSERT INTO document (id, title, created_at) VALUES ('doc-1', 'Home', '2026-01-01T00:00:00Z');
```

**MariaDB** (compatible):
```sql
INSERT INTO document (id, title, created_at) VALUES ('doc-1', 'Home', '2026-01-01T00:00:00Z');
```

→ 둘 다 동일. ANSI SQL 표준 형태 사용.

#### 다중 행 INSERT (Batch Insert)

**권장 형태** (양쪽 모두 지원):
```sql
INSERT INTO document (id, title) VALUES
  ('doc-1', 'Home'),
  ('doc-2', 'About');
```

**MariaDB 전용** (금지):
```sql
INSERT INTO document (id, title) VALUES ('doc-1', 'Home');
INSERT INTO document (id, title) VALUES ('doc-2', 'About');
```
→ 성능상 여러 문으로 나뉘어 좋지 않음. 다중 행 INSERT 사용.

### 3.3 에러 처리

| 에러 | PostgreSQL | MariaDB | 조치 |
|---|---|---|---|
| 유니크 제약 위반 (중복 ID) | UNIQUE violation | Duplicate entry | 롤백, 사용자 알림 |
| 외래키 제약 위반 | FK constraint violation | Cannot add or update child row | 롤백, 테이블 로드 순서 확인 |
| 컬럼 타입 불일치 | type mismatch | Data too long / Type error | 롤백, fixture 파일 검증 |
| 테이블 부재 | relation does not exist | Table doesn't exist | 롤백, 스키마 확인 |

## 4. JSON Export 복원 절차 (운영 백업)

### 4.1 파일 구조 검증

JSON export 파일을 파싱한 후 필수 구조를 확인한다.

```json
{
  "export_version": "1",
  "schema_version": "2026-01-10",
  "exported_at": "2026-01-15T14:30:00Z",
  "tables": {
    "document": [...],
    "revision": [...],
    ...
  }
}
```

검증 항목:
- `export_version` 필드 존재 및 값 확인 (현재 "1" 만 지원).
- `schema_version` 필드 존재 — 2절의 호환성 검사로 전달.
- `tables` 필드가 객체(object)이고 각 테이블이 배열(array) 형태.
- 각 배열 원소가 객체 형태 (record).

실패 시: "Invalid JSON export format" 에러.

### 4.2 로드 순서

`tables` 객체의 각 테이블을 FK 종속성 순서로 로드한다.

예시 로드 순서:
```
1. "user" (부모)
2. "document" (user를 참조)
3. "revision" (document를 참조)
4. "acl_grant" (user, document를 참조)
```

구현:
- 로더는 `[Persistence Boundaries](persistence-boundaries.md)`에서 정의한 FK 그래프를
  미리 계산해 저장.
- JSON의 `tables` 키를 이 순서대로 재배열 후 로드.
- 만약 정의되지 않은 테이블이 JSON에 포함되면, 로더는 어디에 삽입할지
  선택:
  1. **무시**: 알려지지 않은 테이블 건너뛰기 (기본).
  2. **에러**: 미지의 테이블은 restore 실패 (엄격 모드).

### 4.3 데이터 삽입 및 FK 검사

각 테이블을 순서대로 삽입한다.

```python
# 의사 코드 (Python)
for table_name in load_order:
    for record in json['tables'][table_name]:
        # record는 {"id": "...", "document_id": "...", ...} 형태
        INSERT INTO table_name VALUES (record.values)
```

**FK 검사 타이밍**:

PostgreSQL:
- 기본: `FOREIGN_KEY_CHECKS = on` (항상 활성).
- 로드 전 일시적으로 비활성화 불가 (표준 SQL은 지원 안 함).
- 단일 트랜잭션 내에서 로드, 완료 후 자동 검사.

MariaDB:
- 기본: `FOREIGN_KEY_CHECKS = on`.
- 로드 전: `SET FOREIGN_KEY_CHECKS = OFF;`로 임시 비활성화 가능.
- 모든 데이터 로드 후: `SET FOREIGN_KEY_CHECKS = ON;` 재활성화.
- **권장**: 로더는 MariaDB에서도 기본값 유지. 로드 순서가 올바르면 FK 검사를
  통과해야 한다. FK 비활성화는 예외 상황(손상된 백업 복구)에서만 사용.

### 4.4 MariaDB vs PostgreSQL 차이

#### JSON 파싱

**PostgreSQL**:
- `json` 또는 `jsonb` 타입 지원.
- 로더는 Python `json.load()` 또는 직접 SQL 함수 사용 가능.

**MariaDB**:
- `JSON` 타입 지원 (5.7.8+).
- 로더는 PHP `json_decode()` 또는 직접 SQL 함수 사용 가능.

→ 로더 구현체마다 다르므로, 양쪽 모두 표준 JSON 파싱 라이브러리 사용 권장.

#### 트랜잭션 대기 시간

**PostgreSQL**:
- 기본 statement timeout 없음 (무한 대기).
- 운영 환경에서는 `statement_timeout` 설정 권장.

**MariaDB**:
- 기본 `max_execution_time = 0` (무제한).
- 운영 환경에서는 `max_execution_time` 또는 `max_statement_time` 설정 권장.

→ 대용량 복원 시 양쪽에서 타임아웃 설정 확인.

#### 외래키 제약 비활성화 (예외)

**MariaDB**:
```sql
SET FOREIGN_KEY_CHECKS = OFF;
-- 데이터 로드
SET FOREIGN_KEY_CHECKS = ON;
```

**PostgreSQL**:
```sql
-- 표준 SQL에는 해당 기능 없음.
-- 트리거 비활성화 같은 임시 조치는 프로덕션에서 권장하지 않음.
```

→ FK 제약 비활성화는 예외 상황에서만 사용. 정상 복원은 로드 순서로 해결.

## 5. 에러 처리 전략

### 5.1 부분 실패 (Partial Failure)

복원 중 일부 테이블이 실패할 경우:

- **일반 정책**: 첫 에러에서 즉시 롤백. 모든 변경 사항 취소.
- **대안** (운영 정책에 따라):
  - "Continue on error": 실패한 테이블 건너뛰고 계속 로드.
    - 로더는 실패한 테이블 목록 기록.
    - 복원 완료 후 사용자에게 부분 복원 결과 보고.
    - 권장: 프로덕션에서는 "Continue on error" 미사용. 개발 환경에서만 사용.

### 5.2 재복원 (Idempotent Restore)

같은 백업을 여러 번 복원할 때 충돌 방지:

**방법 1: 사전 DELETE (권장)**
- 복원 전에 모든 테이블 TRUNCATE.
- 백업 데이터로 깨끗한 상태부터 시작.
- 구현: 로더가 각 테이블마다 `DELETE FROM <table>;` 실행 후 INSERT.

**방법 2: UPSERT (MariaDB 미지원)**
- PostgreSQL: `INSERT ... ON CONFLICT ... DO UPDATE;`
- MariaDB: 미지원 (`INSERT ... ON DUPLICATE KEY UPDATE` 있음,
  하지만 다르게 동작).
- 권장하지 않음: ANSI SQL 표준이 아님.

→ 현재 구현: 로더가 사전 DELETE 책임.

### 5.3 복구 불가능한 에러

다음의 경우 복원 불가능:

| 에러 | 원인 | 사용자 조치 |
|---|---|---|
| 데이터베이스 연결 실패 | DB 인스턴스 미실행 | DB 시작 후 재시도 |
| 스키마 버전 불일치 (신 버전 백업) | 백업이 너무 최신 | 현재 스키마 업그레이드 후 재시도 |
| JSON 파싱 실패 | 손상된 파일 | 백업 파일 복구 또는 재생성 |
| 유니크 제약 위반 | 데이터가 이미 DB에 있음 | 테이블 TRUNCATE 후 재시도 |

## 6. 운영 시나리오

### 6.1 정상 복원 흐름

```
사용자 업로드 (JSON 또는 SQL dump)
  ↓
파일 검증 (형식, 스키마 버전)
  ↓
스키마 버전 호환성 검사
  ↓
트랜잭션 시작
  ↓
테이블 로드 (FK 순서)
  ↓
트랜잭션 커밋
  ↓
복원 완료 알림
```

### 6.2 롤백 시나리오

복원 중 에러 발생:

```
트랜잭션 롤백 (모든 변경 사항 취소)
  ↓
에러 메시지 사용자에게 표시
  ↓
DB 상태: 복원 전과 동일
```

### 6.3 부분 복원 (선택 사항)

"Continue on error" 모드 활성화:

```
실패한 테이블 A 건너뜀
  ↓
테이블 B, C, D 로드 진행
  ↓
트랜잭션 커밋
  ↓
경고: 테이블 A는 실패했습니다. (부분 복원 상태)
```

→ 이 모드는 개발/테스트 환경 전용. 프로덕션에서는 사용 금지.

## 7. 복원 확인 및 검증

복원 완료 후 데이터 무결성을 검증한다.

### 7.1 행 개수 확인

```sql
-- 각 테이블의 행 개수가 백업과 일치하는지 확인
SELECT COUNT(*) FROM document;  -- 예: 42개
SELECT COUNT(*) FROM revision;  -- 예: 128개
```

### 7.2 외래키 무결성 검사

```sql
-- PostgreSQL: 모든 FK 참조가 유효한지 확인
SELECT COUNT(*) FROM revision
  WHERE document_id NOT IN (SELECT id FROM document);  -- 0이어야 함

-- MariaDB: 동일
SELECT COUNT(*) FROM revision
  WHERE document_id NOT IN (SELECT id FROM document);  -- 0이어야 함
```

### 7.3 고유값 검사

```sql
-- 모든 ID가 유일한지 확인
SELECT id, COUNT(*) FROM document GROUP BY id HAVING COUNT(*) > 1;
-- 결과: 없음
```

## 8. 이 문서 이후 단계

- **0598** ([PHP UI backup page placeholder](php-db-ui-micro-job-prompts-0351-0670.md)):
  사용자가 JSON export를 업로드하고 복원할 수 있는 UI 페이지.
  이 문서의 복원 절차와 에러 처리를 UI로 구현.

- **0639** ([Export directory policy](php-db-ui-micro-job-prompts-0351-0670.md)):
  백업 export 파일의 저장 위치 및 접근 제어 정책.
  복원 중 파일 로드 경로도 이 정책을 따름.

- **마이그레이션 복원 자동화** (번호 미배정):
  버전 불일치 시 자동 마이그레이션 실행 여부, 조건 등을 정의하는
  추후 작업. 이 문서는 "버전 불일치 시 경고 및 사용자 확인"을 기본으로
  정의했고, 자동화는 운영 요구사항에 따라 구현.

## 관련 문서

- [Portable Backup Format](portable-backup-format.md) — 이 문서가 복원하는
  SQL dump와 JSON export 형식의 정의.
- [Persistence Boundaries](persistence-boundaries.md) — 테이블 FK 종속성 및
  로드 순서 기준.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — SQL 기능 제약
  (이미 만족하는 상태에서 복원).
- [DB Portable Seed Fixtures](php-db-ui-micro-job-prompts-0351-0670.md#0490)
  — seed fixture 형식.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
