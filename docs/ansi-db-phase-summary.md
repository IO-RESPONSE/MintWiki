# ANSI DB Phase Summary

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 완료 요약.
이 문서는 Phase D (UI, 0521+) 개발자가 Phase C에서 구축한 DB 계층을 사용할 때
반드시 지켜야 할 경계, 제약, 보장을 한 곳에 정리한다. DB 계층의 세부 정책을
학습하기보다는 **UI 개발 시 의존할 수 있는 것과 금지된 것**을 빠르게 파악하기
위한 가이드다.

## 목적

Phase C에서는 PostgreSQL과 MariaDB 양쪽에서 동등하게 동작하는 ANSI SQL 기반
이식 가능한 DB 계층을 구축했다. Phase D부터 UI를 개발할 때, 개발자는:

1. **어떤 저장소 서비스를 호출할 수 있는가** (DocumentService, RevisionService 등)
2. **어떤 보장이 있는가** (트랜잭션, 원자성, 에러 신호)
3. **어떤 제약이 있는가** (SQL 기능, 타입, 이름 규칙)
4. **무엇을 피해야 하는가** (직접 SQL, ORM 세부사항, PostgreSQL 전용 기능)

…을 알아야 한다. 이 문서는 그 정보를 모두 담는다.

## 대상

- Phase D (UI) 개발자 — 애플리케이션 라우터, 뷰 모델, 서비스 계층
- 아키텍처 리뷰어 — DB 계층과 UI 계층 사이의 경계 검증
- 운영/QA — DB 계층 안정성 가정 확인

## 1. 호출 가능한 인터페이스

### 1.1 공개 서비스 (Public Services)

다음 서비스를 통해서만 DB에 접근한다. **직접 저장소나 ORM을 import하지 않는다.**

| 모듈 | 서비스 | 노출 인터페이스 |
|---|---|---|
| **document** | `DocumentService` | `create(title, source, author_id) -> Document`<br/>`get(id) -> Document \| None`<br/>`get_by_normalized_title(title) -> Document \| None`<br/>`update(document) -> Document`<br/>`list_recent(limit) -> list[Document]` |
| **revision** | `RevisionService` | `create(document_id, source, author_id, summary) -> Revision`<br/>`get(id) -> Revision \| None`<br/>`list_by_document(document_id) -> list[Revision]`<br/>`get_current_for_document(document_id) -> Revision \| None` |
| **user** | `UserService` | `create_user(username, password_hash) -> User`<br/>`get_user(user_id) -> User \| None`<br/>`authenticate(username, password) -> User \| None` |
| **acl** | `AclService` | `check(subject, document_id, action) -> bool`<br/>`add_rule(document_id, rule) -> None`<br/>`get_rules(document_id) -> list[Rule]` |
| **discussion** | `DiscussionService` | `create_thread(document_id, title, author_id) -> Thread`<br/>`add_comment(thread_id, text, author_id) -> Comment`<br/>`get_comments(thread_id, limit, offset) -> list[Comment]` |
| **jobs** | `JobService` | `enqueue(job_type, payload) -> Job`<br/>`get_status(job_id) -> JobStatus`<br/>`list_pending() -> list[Job]` |
| **audit** | `AuditService` | `append(event: AuditEvent) -> None` (append-only)<br/>`list_events(document_id, limit) -> list[AuditEvent]` |

**규칙:**
- 모든 서비스는 비동기(`async` 메서드)이다.
- 서비스 메서드는 도메인 모델(Python: dataclass, PHP: value object)을 반환한다.
- 서비스는 `errors` 모듈의 도메인 예외를 던진다(`DocumentNotFoundError`, `DuplicateNormalizedTitleError` 등).
- 서비스는 저장소 구현(`DatabaseDocumentRepository` 등)을 직접 노출하지 않는다.

### 1.2 금지된 임포트

**다음을 직접 import하지 말 것:**

```python
# ❌ 금지됨
from src.persistence.models import DocumentORM
from src.modules.document.repository import DatabaseDocumentRepository
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
```

**대신 서비스를 통해 호출:**

```python
# ✓ 허용됨
from src.modules.document.service import DocumentService
doc = await document_service.get(document_id)
```

## 2. 거래(Transaction) 보장

### 2.1 원자성 (Atomicity)

각 서비스 메서드 호출은 하나의 트랜잭션으로 실행된다.

- **쓰기 연산**: `create()`, `update()`, `delete()` — 성공하거나 전체 롤백.
- **읽기 연산**: `get()`, `list_*()` — 일관된 스냅샷 읽음.

**예시:**

```python
# DocumentService.create()의 보장:
# 1. 정규화된 제목 유일성 확인 (DB 제약)
# 2. 레코드 삽입
# 3. 커밋
# 모든 단계가 원자적으로 수행되거나 모두 롤백됨.
# 만약 제목이 이미 존재하면 DuplicateNormalizedTitleError 던짐.
```

### 2.2 격리 수준 (Isolation)

PostgreSQL: `READ COMMITTED` (기본값)  
MariaDB: `READ COMMITTED` 또는 호스팅 기본값

**의미:**
- 커밋되지 않은 데이터는 읽히지 않음.
- **동시 쓰기 충돌은 애플리케이션이 처리해야 함** (재시도, 낙관적 잠금 등).
- 읽기는 빠르고, 과도한 잠금 없음.

**영향:**
- 같은 문서를 동시에 편집하는 두 사용자는 후자의 업데이트가 이전 버전을 덮어쓸 수 있음.
- 이를 방지하려면 revision 체인 검증 또는 CAS(compare-and-swap) 패턴 사용.

### 2.3 에러 신호

DB 에러는 도메인 예외로 변환된다.

| DB 에러 | 도메인 예외 | 어디서 발생 |
|---|---|---|
| 유일성 제약 위반 (normalized_title 중복) | `DuplicateNormalizedTitleError` | DocumentService.create/update |
| 외래키 제약 위반 | `DocumentNotFoundError` | RevisionService.create (document_id FK) |
| 연결 실패 | `DatabaseConnectionError` | 모든 서비스 메서드 |
| 타임아웃 | `DatabaseTimeoutError` | 모든 서비스 메서드 |

**UI 개발자는 이 예외들을 `try/except`로 처리해야 한다.**

## 3. SQL 지원 범위 및 제약

### 3.1 지원되는 SQL 기능

다음은 PostgreSQL과 MariaDB 양쪽에서 동등하게 동작한다:

- **타입**: `VARCHAR(n)`, `TEXT`, `INTEGER`, `BIGINT`, `BOOLEAN`, `TIMESTAMP`
- **연산자**: `=`, `!=`, `<`, `>`, `<=`, `>=`, `LIKE`, `||` (문자열 접합)
- **집계**: `COUNT()`, `MAX()`, `MIN()`, `SUM()`, `AVG()`
- **조인**: `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `CROSS JOIN`
- **절**: `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`, `OFFSET`
- **트랜잭션**: `BEGIN`, `COMMIT`, `ROLLBACK`
- **제약**: `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`, `CHECK`, `DEFAULT`

### 3.2 지원되지 않는 기능 (PostgreSQL 전용)

다음을 사용하면 MariaDB에서 실패한다. **저장소 코드는 이를 피한다:**

| 기능 | 왜 금지 | 저장소 내 대체 |
|---|---|---|
| `RETURNING` 절 | MariaDB 미지원 | insert 후 별도 SELECT |
| `JSONB` / JSON 연산자 (`->`, `->>`) | 문법 차이 | 정규화된 컬럼 또는 애플리케이션 직렬화 |
| `ARRAY` 타입 | MariaDB 미지원 | 1:N 연결 테이블 |
| `ILIKE` | MariaDB 미지원 | 정규화된 소문자 컬럼 + `LIKE` |
| `SERIAL` / `gen_random_uuid()` | DB별 문법 차이 | 애플리케이션 UUID 문자열 생성 |
| `ON CONFLICT ... DO UPDATE` | MariaDB 미지원 | 존재 확인 후 분기 또는 각 DB별 분기 |
| `tsvector` / 전문 검색 | PostgreSQL 특화 | 외부 search 엔진 (adapter 패턴) |
| `DISTINCT ON` | MariaDB 미지원 | `GROUP BY` + 집계 함수 |
| `generate_series()` | PostgreSQL 특화 | 애플리케이션 루프 |

**UI 개발자는 이들을 신경 쓰지 않아도 된다** — 저장소가 이미 처리한다.

### 3.3 문자열 비교와 collation

문자열 비교는 **대소문자를 구분한다** (collation: `utf8mb4_bin`).

```python
# 저장소 내부 동작 (UI는 신경 쓸 필요 없음)
# SQL: SELECT * FROM document WHERE normalized_title = 'Home'
# "home"과 "HOME"은 일치하지 않음 (case-sensitive).
```

**UI 영향:**
- 사용자 입력 문자열을 서비스에 전달하기 전에 정규화하지 말 것.
- 서비스가 내부적으로 정규화 처리한다.

## 4. 데이터 모델 계약

### 4.1 ID 컬럼

모든 ID는 **문자열**이다. (UUID 형식, 예: `"550e8400-e29b-41d4-a716-446655440000"`)

| 엔티티 | ID 타입 | 생성 책임 |
|---|---|---|
| `Document.id` | String(255) UUID | DocumentService (애플리케이션) |
| `Revision.id` | String(255) UUID | RevisionService (애플리케이션) |
| `User.id` | String(255) UUID | UserService (애플리케이션) |
| `AclRule.id` | String(255) UUID | AclService (애플리케이션) |

**규칙:**
- ID를 생성하는 것은 애플리케이션의 책임이다.
- DB의 `SERIAL` / `AUTO_INCREMENT`는 사용하지 않는다.

### 4.2 timestamp 컬럼

모든 timestamp는 **타임존 정보를 포함**한다. (UTC 저장)

| 컬럼 | 타입 | 생성 | 갱신 |
|---|---|---|---|
| `created_at` | `DateTime(tz)` | 생성 시 설정 (DB `DEFAULT NOW`) | 불변 |
| `updated_at` | `DateTime(tz)` | 생성 시 설정 | 매번 갱신 (DB trigger 또는 애플리케이션) |

**UI에서의 사용:**
- 시간대 변환은 클라이언트(브라우저)에서 처리.
- 서버는 UTC ISO 8601 형식으로 반환.

### 4.3 정규화된 제목 (normalized_title)

Document 모델은 `title`과 `normalized_title` 두 컬럼을 가진다.

| 컬럼 | 내용 | 특성 |
|---|---|---|
| `title` | 사용자 입력 (그대로) | 공백 포함 가능, 길이 최대 500자 |
| `normalized_title` | 공백 정규화 후 소문자 | **UNIQUE 제약**, 검색 키로 사용 |

**정규화 규칙:**
- 연속 공백을 단일 공백으로 축약
- 양 끝 공백 제거
- 소문자 변환 (애플리케이션 계층)

**예시:**

```python
# UI에서 입력한 제목: "  Hello   World  "
# normalized_title: "hello world"  (UNIQUE 제약으로 보호됨)
```

**영향:**
- 같은 정규화된 제목을 두 번 생성할 수 없다.
- 이미 존재하면 `DuplicateNormalizedTitleError` 발생.

### 4.4 가능한 상태 필드

특정 엔티티는 제한된 상태 값만 가진다. (Enum, 저장소는 검증)

| 엔티티 | 상태 필드 | 가능한 값 | 의미 |
|---|---|---|---|
| `AclRule` | `effect` | `ALLOW`, `DENY` | 규칙 방향 |
| `Job` | `status` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` | 잡 상태 |
| `AuditEvent` | `event_type` | `CREATE`, `UPDATE`, `DELETE`, `LOGIN`, `BLOCK` | 감사 이벤트 종류 |

## 5. 모듈 경계 및 의존성

### 5.1 모듈 소유권 (Module Ownership)

각 모듈이 소유한 테이블과 API:

| 모듈 | 소유 테이블 | 공개 서비스 | 의존하는 모듈 |
|---|---|---|---|
| **document** | `document` | DocumentService | (없음) |
| **revision** | `revision` | RevisionService | document (읽기) |
| **user** | `user`, `session` | UserService | (없음) |
| **acl** | `acl_rule`, `acl_namespace_default` | AclService | user (읽기) |
| **discussion** | `discussion_thread`, `discussion_comment`, `discussion_state` | DiscussionService | document, user (읽기) |
| **jobs** | `job_definition`, `job_run` | JobService | (없음) |
| **audit** | `audit_event` | AuditService | user (읽기) |
| **search** | (외부 엔진) | SearchService | (adapter 패턴) |

**규칙:**
- UI 개발자는 각 모듈의 공개 서비스를 통해서만 접근한다.
- 모듈은 다른 모듈의 테이블을 직접 수정하지 않는다.
- 읽기 의존성(예: revision 모듈이 document 모듈 읽기)은 서비스 조합으로 표현.

### 5.2 교차 모듈 트랜잭션

문서 생성 시 동시에 초기 revision도 생성되어야 하는 경우:

```python
# ✓ 올바른 방법: 서비스가 원자성을 보장
document, revision = await document_service.create_with_revision(
    title="New Doc",
    source="Initial content",
    author_id=user_id
)
# 내부적으로 document와 revision이 원자적으로 생성됨
# 하나 실패하면 둘 다 롤백됨
```

## 6. 이름 규칙 (Naming Conventions)

### 6.1 데이터베이스 객체 이름

모든 테이블, 컬럼, 인덱스 이름은:

- 소문자 ASCII만 사용
- 숫자와 언더스코어 허용
- 예약어 회피
- 길이 제한: 64자 이하 (MariaDB)

**예시:**

```sql
-- ✓ 허용됨
CREATE TABLE document (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    normalized_title VARCHAR(500) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_document_normalized_title ON document(normalized_title);

-- ❌ 금지됨
CREATE TABLE Document (  -- 대문자
    Id VARCHAR(255),      -- 대문자
    title JSONB,          -- PostgreSQL 전용 타입
    `group` TEXT          -- 예약어
);
```

## 7. 마이그레이션 안정성

### 7.1 스키마 버전 관리

마이그레이션은 Alembic(`migrations/versions/`)으로 관리된다.

- **순방향**: 새 변경 적용 (UP)
- **역방향**: 이전 버전으로 롤백 (DOWN)

**UI 개발 시:**
- 새 DB 기능이 필요하면 마이그레이션을 먼저 작성.
- 마이그레이션은 PHP 포팅 가능해야 함 (ANSI SQL).

### 7.2 기존 데이터 보호

마이그레이션은:

- 기존 데이터를 파괴하지 않음
- 롤백 가능해야 함
- MariaDB와 PostgreSQL 양쪽에서 동작

## 8. 검사 및 검증

### 8.1 자동 검사

커밋 전에 다음을 실행:

```bash
scripts/test.sh    # 모든 테스트
scripts/qa.sh      # SQL 금지 목록, 모듈 경계, 마이그레이션 검사
```

### 8.2 마이그레이션 검증

새 마이그레이션 추가 시:

- [ ] ANSI SQL 기능만 사용 (PostgreSQL 전용 기능 없음)
- [ ] 이름 규칙 준수
- [ ] 역방향(downgrade) 구현
- [ ] 테스트 추가

## 9. 다음 단계 (Phase D+)

Phase D (UI, 0521+)에서는 위 계약을 기반으로:

1. **서비스 호출 확장**: 새로운 UI 기능에 필요한 서비스 메서드 추가.
2. **DB 기능 확장**: 새로운 테이블/마이그레이션 필요 시 ANSI SQL 기준 준수.
3. **PHP 포팅 준비**: Python 저장소의 계약을 PHP로 동등하게 구현.
4. **성능 최적화**: 쿼리 최적화, 인덱스 추가 (Phase D 후반/Phase E).

모든 추가 기능은 이 문서의 경계와 보장을 벗어나지 않아야 한다.
