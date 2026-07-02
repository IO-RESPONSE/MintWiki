# DB Phase Risk Register

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
이 문서는 PostgreSQL과 MariaDB 간 이식성을 보장하는 과정에서 발생할 수 있는
주요 위험 요소들을 식별하고, 각 위험에 대한 영향 범위와 완화 전략을 정의한다.
기존 정책 문서들([Portable Text Collation Policy](portable-text-collation-policy.md),
[Repository Transaction Policy](repository-transaction-policy.md),
[Migration Portability Checklist](migration-portability-checklist.md))이
개별 영역의 규칙을 제시했다면, 이 문서는 각 규칙이 필요한 이유와 규칙을
지키지 않았을 때의 실제 위험을 통합적으로 기술한다.

## 목적

Phase C 동안 도입되는 이식성 정책 중 중요도 높은 위험들을 사전에 문서화해,
개발 중 정책 위반으로 인한 버그를 조기에 발견하고, 코드 리뷰 때 확인 항목을
명확히 한다. 또한 각 위험의 **구체적인 재현 시나리오**를 기술해, 테스트와
QA가 검증해야 할 케이스를 지정한다.

## 적용 범위

이 문서가 다루는 위험들:

- PostgreSQL과 MariaDB 간 **문자 비교 방식의 차이**로 인해 발생하는
  데이터 무결성 위반 (collation 위험).
- PostgreSQL과 MariaDB의 **다른 트랜잭션 격리 수준과 DDL 커밋 동작**으로 인한
  데이터 불일치와 부분 실패 (transaction 위험).
- 마이그레이션 도구들(Alembic, PHP 포팅 이후 PHP 마이그레이션) 간
  **스키마 버전 호환성 문제**와 DDL 실행 순서 (migration 위험).

적용되지 않는 것:

- 네트워크, 배포 인프라, CI/CD 파이프라인 위험 — 별도 운영 정책이 담당.
- 성능 최적화(쿼리, 인덱싱 튜닝) — Phase D 이후 잡의 범위.
- 애플리케이션 로직 버그 (예: 비즈니스 규칙 위반) — 도메인 모듈 테스트 책임.

---

## 1. Collation 위험

### 1.1 위험: 문자 비교 방식 불일치

#### 1.1.1 상황

PostgreSQL은 기본적으로 모든 문자열 비교를 **바이트 단위 대소문자 구분**
(`=`, `LIKE`, UNIQUE 제약 모두)으로 수행한다.
MariaDB는 컬럼에 지정된 **collation**에 따라 비교 방식이 정해지며,
기본값(`utf8mb4_general_ci`, `utf8mb4_unicode_ci`)은
**대소문자를 구분하지 않는다**.

#### 1.1.2 영향 범위

- **UNIQUE 제약 위반**: PostgreSQL에서는 "Test"와 "test"가 서로 다른 값이지만,
  MariaDB (`utf8mb4_general_ci`)에서는 같은 값으로 취급되어,
  PostgreSQL에서 성공한 삽입이 MariaDB에서는 제약 위반으로 실패한다.
  ```
  # PostgreSQL: 성공
  INSERT INTO document (normalized_title) VALUES ('Test');
  INSERT INTO document (normalized_title) VALUES ('test');  -- 다른 값, 성공
  
  # MariaDB (utf8mb4_general_ci): 실패
  INSERT INTO document (normalized_title) VALUES ('Test');
  INSERT INTO document (normalized_title) VALUES ('test');  -- 제약 위반, 실패
  ```

- **쿼리 결과 차이**: `WHERE title = 'Test'`가 PostgreSQL에서는
  정확히 "Test"만 조회하지만, MariaDB에서는 "test", "TEST" 등도 조회한다.

- **데이터 마이그레이션 실패**: 기존 PostgreSQL DB를 MariaDB로 이전할 때,
  collation이 명시되지 않아 기본값을 사용하면, 대소문자 차이로 인한
  UNIQUE 제약 위반이 발생해 일부 행이 로드되지 않을 수 있다.

- **API 응답 불일치**: 사용자 ID, 문서 제목 등 고유 식별자 검색에서
  두 DB 간 결과가 달라질 수 있다.

#### 1.1.3 완화 전략

[Portable Text Collation Policy](portable-text-collation-policy.md)가
정책 수준에서 제시한 완화 방법:

1. **명시적 collation 지정**:
   - MariaDB의 모든 문자열 컬럼(`VARCHAR`, `TEXT`)에
     `COLLATE utf8mb4_bin` 을 명시해서 대소문자 구분 비교를 강제한다.
   - 마이그레이션 파일과 ORM 모델에서 이를 일관되게 적용한다.

2. **애플리케이션 계층 정규화**:
   - 대소문자 무시 검색(`ILIKE` 대체)이 필요한 경우,
     별도 정규화 컬럼(예: `normalized_title`)을 두고
     애플리케이션이 검색 입력을 정규화한 뒤 이 컬럼으로 조회한다.
   - 이 방식은 DB 차이를 드러내지 않으면서도 검색 유연성을 제공한다.

#### 1.1.4 검증 방법

**자동 검사**:
- `scripts/check_collation.py` (미정): 모든 `VARCHAR`/`TEXT` 컬럼이
  `utf8mb4_bin`을 명시하는지 검사 (향후 추가 가능).

**수동 리뷰**:
- 마이그레이션 파일: 새 `VARCHAR`/`TEXT` 컬럼의 `COLLATE` 절 확인.
- ORM 모델: `String`/`Text` 컬럼에 collation 인자 확인.

**테스트 케이스**:
```python
# tests/persistence/test_collation.py
def test_document_title_collation_case_sensitive():
    """PostgreSQL과 MariaDB 모두 문서 제목 대소문자를 구분한다."""
    repo = DatabaseDocumentRepository(db_session)
    
    # "Test"를 삽입
    doc1 = repo.create(
        user_id="user1", 
        title="Test", 
        content="content"
    )
    
    # "test"를 삽입 (별개의 값으로 취급되어야 함)
    doc2 = repo.create(
        user_id="user1",
        title="test",
        content="content"
    )
    
    # 양쪽 문서가 저장되어야 함
    assert len(repo.list_by_user_id("user1")) == 2
    
    # 정확한 대소문자로 조회하면 각각 하나씩만 조회
    assert repo.find_by_title("Test").id == doc1.id
    assert repo.find_by_title("test").id == doc2.id
    
    # 대소문자 무시 검색이 필요하면 애플리케이션에서 정규화
    normalized_title = "test".lower()
    results = repo.list_by_normalized_title(normalized_title)
    assert len(results) == 2  # "Test"도 "test"도 포함
```

### 1.2 위험: 한글/이모지 문자셋 오류

#### 1.2.1 상황

MariaDB의 기본 `utf8` 문자셋은 3바이트만 지원해서
한글의 일부(조합형), 이모지, 일부 한자를 저장하지 못한다.

#### 1.2.2 영향 범위

- **데이터 손실**: `utf8`을 사용한 MariaDB에 한글 또는 이모지를 저장하면
  **변환 오류** 또는 **문자 손실**이 발생한다.
  ```
  # MariaDB (utf8): "한글" 저장 실패
  INSERT INTO document (title) VALUES ('한글');  -- 변환 오류
  
  # MariaDB (utf8mb4): 성공
  INSERT INTO document (title) VALUES ('한글');
  ```

- **마이그레이션 실패**: 한글/이모지가 있는 기존 PostgreSQL DB를
  `utf8`이 기본인 MariaDB로 이전할 때 데이터 손실.

#### 1.2.3 완화 전략

[Portable Text Collation Policy](portable-text-collation-policy.md) §1:

1. **명시적 문자셋 지정**:
   - 모든 마이그레이션에서 CREATE TABLE 시 `CHARACTER SET utf8mb4`를 명시.
   - ORM 모델 생성 시 `charset='utf8mb4'`를 명시.

2. **DB 초기화 시점 확인**:
   - 새 MariaDB 인스턴스는 초기화 스크립트에서
     `SET NAMES utf8mb4; SET CHARACTER SET utf8mb4;`를 실행.

#### 1.2.4 검증 방법

**자동 검사**:
- `scripts/check_sql_denylist.py`: 마이그레이션 파일이
  `CHARACTER SET utf8mb4` 또는 `CHARSET utf8mb4`를 빠뜨렸는지 검사.

**테스트 케이스**:
```python
# tests/persistence/test_text_encoding.py
def test_korean_text_storage():
    """한글 텍스트가 양쪽 DB에서 손실 없이 저장된다."""
    repo = DatabaseDocumentRepository(db_session)
    
    doc = repo.create(
        user_id="user1",
        title="한글 제목",
        content="한글 본문 내용 🎉"
    )
    
    retrieved = repo.get(doc.id)
    assert retrieved.title == "한글 제목"
    assert retrieved.content == "한글 본문 내용 🎉"
```

---

## 2. Transaction 위험

### 2.1 위험: DDL 암묵적 커밋

#### 2.1.1 상황

PostgreSQL은 `CREATE TABLE`, `ALTER TABLE` 등 DDL을
**트랜잭션 내에서 롤백 가능**하게 처리한다.
MariaDB는 대부분의 DDL이 **암묵적 COMMIT을 유발**해,
한 번 실행되면 되돌릴 수 없다.

#### 2.1.2 영향 범위

- **부분 마이그레이션**: 마이그레이션 함수가 여러 DDL을 실행할 때,
  중간에 실패하면 이미 실행된 앞쪽 DDL은 자동으로 롤백되지 않는다.
  ```
  # PostgreSQL: 하나의 마이그레이션, 중간 실패 시 모두 롤백
  BEGIN;
  CREATE TABLE foo (...);      -- 실행됨
  CREATE TABLE bar (...);      -- 실행됨
  ALTER TABLE foo ADD ...;     -- 실패! ← 모든 변경 롤백
  COMMIT;
  
  # MariaDB: 각 DDL이 즉시 커밋되므로 부분 롤백 불가
  CREATE TABLE foo (...);      -- 자동 커밋, 되돌릴 수 없음
  CREATE TABLE bar (...);      -- 자동 커밋, 되돌릴 수 없음
  ALTER TABLE foo ADD ...;     -- 실패! ← foo, bar는 여전히 존재
  ```

- **스키마 불일치**: PostgreSQL에서는 정상 실행되던 마이그레이션이
  MariaDB에서 부분 실패하면, 운영 DB의 스키마가 예상과 다를 수 있다.

- **재실행 불가**: `upgrade()` 함수가 멱등성을 보장하지 않으면,
  실패 후 재실행 시 이미 생성된 테이블/컬럼으로 인해 다시 실패한다.

#### 2.1.3 완화 전략

[Migration Portability Checklist](migration-portability-checklist.md) §3:

1. **마이그레이션 분산**:
   - 논리적으로 독립된 스키마 변경을 **가능한 한 별도 파일**로 쪼갠다.
   - 하나의 파일 = 하나의 논리적 변경 원칙.
   - 예: "테이블 생성"과 "외래키 추가"는 별도 마이그레이션.

2. **멱등성 확보**:
   - `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD ... IF NOT EXISTS`를 사용.
   - 부분 실패 후 재실행할 수 있게 함.

3. **수동 정리 절차 문서화**:
   - 각 마이그레이션의 주석에 "MariaDB에서 부분 실패 시 수동 정리" 항목 추가.

#### 2.1.4 검증 방법

**수동 리뷰**:
- 마이그레이션 파일의 `upgrade()` 함수가 여러 독립된 DDL을 포함하면,
  각각을 별도 파일로 분리했는지 확인.

**테스트 케이스**:
```python
# tests/migrations/test_ddl_portability.py
def test_migration_idempotence_mariadb():
    """마이그레이션을 여러 번 실행해도 멱등성을 보장한다."""
    # MariaDB에서 부분 실패를 시뮬레이션하기 위해
    # 의도적으로 이미 생성된 테이블/컬럼에 대해 재실행
    migration = Alembic('0451_create_user_table')
    
    # 첫 실행
    migration.up()
    assert table_exists('user')
    
    # 두 번째 실행 (부분 실패 후 재실행 시뮬레이션)
    migration.up()  # IF NOT EXISTS 때문에 성공해야 함
    assert table_exists('user')
    assert table_row_count('user') == 0  # 데이터는 변하지 않음
```

### 2.2 위험: 격리 수준 차이

#### 2.2.1 상황

PostgreSQL의 기본 격리 수준은 `READ COMMITTED`.
MariaDB (InnoDB)의 기본은 `REPEATABLE READ`.
두 수준 간 **동시성 보장 정도**가 다르다.

#### 2.2.2 영향 범위

- **Phantom read**: MariaDB `REPEATABLE READ`에서는
  트랜잭션 도중 새로운 행이 나타나지 않지만
  (phantom read 방지), PostgreSQL `READ COMMITTED`에서는 나타날 수 있다.
  ```
  # PostgreSQL (READ COMMITTED): Phantom read 가능
  BEGIN;
  SELECT * FROM document WHERE user_id = 'u1';  -- 3개 조회
  -- (다른 트랜잭션이 user_id='u1' 문서 1개 추가)
  SELECT * FROM document WHERE user_id = 'u1';  -- 4개 조회 (phantom!)
  COMMIT;
  
  # MariaDB (REPEATABLE READ): Phantom read 방지
  BEGIN;
  SELECT * FROM document WHERE user_id = 'u1';  -- 3개 조회
  -- (다른 트랜잭션이 user_id='u1' 문서 1개 추가)
  SELECT * FROM document WHERE user_id = 'u1';  -- 3개 조회 (동일)
  ```

- **테스트 실패**: PostgreSQL 환경에서는 성공하던 동시성 테스트가
  MariaDB 환경에서는 다른 동작을 할 수 있다.

#### 2.2.3 완화 전략

[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md),
[Repository Transaction Policy](repository-transaction-policy.md):

1. **명시적 격리 수준 설정**:
   - 애플리케이션 또는 어댑터 초기화 시
     `SET TRANSACTION ISOLATION LEVEL READ COMMITTED`를 실행.
   - 양쪽 DB가 같은 수준으로 동작하게 강제.

2. **재조회 패턴**:
   - PostgreSQL의 `RETURNING` 절 대신
     쓰기 후 다시 `SELECT`로 조회하는 패턴.
   - 이 방식은 두 DB 모두에서 최신 값을 보장.

3. **낙관적 잠금**:
   - 동시성 문제가 우려되는 경우 버전 컬럼과
     `UPDATE ... WHERE version = ?` 패턴 사용.

#### 2.2.4 검증 방법

**자동 검사**:
- `scripts/check_isolation_level.py` (미정):
  DB 세션 초기화 시 `READ COMMITTED` 설정 여부 검사.

**테스트 케이스**:
```python
# tests/persistence/test_isolation_level.py
def test_isolation_level_consistency():
    """모든 DB 연결이 READ COMMITTED 격리 수준을 사용한다."""
    from src.persistence.adapter import get_isolation_level
    
    assert get_isolation_level() == 'READ COMMITTED'
    # PostgreSQL과 MariaDB 모두 같은 수준

def test_phantom_read_handling():
    """재조회 패턴으로 phantom read 문제를 해결한다."""
    repo = DatabaseDocumentRepository(db_session)
    
    with db_session.begin():
        doc = repo.create(user_id='u1', title='Test', content='...')
        
        # RETURNING 대신 재조회
        retrieved = repo.get(doc.id)
        assert retrieved.id == doc.id
        assert retrieved.created_at is not None
```

### 2.3 위험: 트랜잭션 경계 위반

#### 2.3.1 상황

[Repository Transaction Policy](repository-transaction-policy.md)에서
"저장소 메서드 하나 = 트랜잭션 하나"로 정의했지만,
개발자가 이 경계를 모르면 여러 저장소 메서드를 호출한 후
마지막에 한 번에 커밋하려고 시도할 수 있다.

#### 2.3.2 영향 범위

- **예상치 못한 커밋**: 저장소 메서드가 반환되면 그 변경은
  이미 커밋되어 있으므로, 호출자가 나중에 커밋/롤백을 시도하면
  효과가 없다.
  ```python
  # 잘못된 사용
  doc = repository.create(...)  # 이미 커밋됨
  rev = revision_repo.create(...)  # 이미 커밋됨
  if some_error:
      db_session.rollback()  # 효과 없음! 위의 커밋은 되돌릴 수 없다
  
  # 올바른 사용
  with DocumentRevisionTransaction(db_session) as txn:
      doc = repository.create(...)  # 커밋 대기
      rev = revision_repo.create(...)  # 커밋 대기
      if some_error:
          raise  # txn이 자동으로 롤백함
  # 전체 커밋
  ```

- **데이터 불일치**: 여러 테이블에 걸친 원자성이 보장되지 않아
  중간 실패 시 일부만 변경될 수 있다.

#### 2.3.3 완화 전략

[Repository Transaction Policy](repository-transaction-policy.md) §3:

1. **크로스 모듈 트랜잭션 헬퍼 사용**:
   - 여러 모듈 테이블에 쓸 때는
     `DocumentRevisionTransaction` 같은 헬퍼를 사용.
   - 헬퍼가 전체 원자성을 보장.

2. **저장소 메서드 규약 명시**:
   - 각 저장소 메서드의 docstring에
     "이 메서드는 스스로 커밋한다"는 명시.

3. **타입 힌트와 검증**:
   - 향후 정적 검증 도구로
     "트랜잭션 경계 내에서만 저장소 메서드 호출" 제약 강제 (0520 이후).

#### 2.3.4 검증 방법

**수동 리뷰**:
- 저장소 메서드를 호출하는 코드가
  여러 메서드를 동시에 호출 후 커밋하려는 패턴이 없는지 확인.

**테스트 케이스**:
```python
# tests/persistence/test_transaction_boundary.py
def test_repository_method_is_atomic():
    """저장소 메서드는 스스로 커밋하므로 호출자가 다시 커밋할 필요 없다."""
    repo = DatabaseDocumentRepository(db_session)
    
    # 메서드 호출
    doc = repo.create(user_id='u1', title='Test', content='...')
    
    # 메서드가 반환되면 이미 커밋됨
    # 다른 세션에서 즉시 조회 가능
    other_session = create_db_session()
    retrieved = other_session.query(Document).filter_by(id=doc.id).first()
    assert retrieved is not None

def test_cross_module_transaction_atomic():
    """여러 모듈에 걸친 쓰기는 트랜잭션 헬퍼로 원자성을 보장한다."""
    doc_repo = DatabaseDocumentRepository(db_session)
    rev_repo = DatabaseRevisionRepository(db_session)
    
    with DocumentRevisionTransaction(db_session) as txn:
        doc = doc_repo.create(user_id='u1', title='Test', content='...')
        rev = rev_repo.create(document_id=doc.id, content='v1')
        
        # 중간에 강제 실패
        raise RuntimeError("Simulated failure")
    
    # txn이 자동으로 롤백했으므로 양쪽 모두 저장되지 않음
    other_session = create_db_session()
    assert other_session.query(Document).filter_by(id=doc.id).first() is None
    assert other_session.query(Revision).filter_by(id=rev.id).first() is None
```

---

## 3. Migration 위험

### 3.1 위험: 스키마 버전 불일치

#### 3.1.1 상황

PostgreSQL 쪽에는 Alembic 마이그레이션이 이미 다수 존재하지만,
PHP 포팅 이후 PHP 쪽에도 마이그레이션이 생긴다.
두 마이그레이션이 같은 스키마 상태를 만들지 못하면
**양쪽 DB 스키마가 수렴되지 않는다**.

#### 3.1.2 영향 범위

- **이식 불가**: PostgreSQL의 완성된 DB를 MariaDB로 이전할 때,
  스키마가 다르면 이식 실패.
  ```
  # PostgreSQL (Alembic 마이그레이션 0451까지 적용)
  CREATE TABLE document (id VARCHAR(255) PRIMARY KEY);
  
  # MariaDB (PHP 마이그레이션 누락)
  -- document 테이블 자체가 없음
  ```

- **운영 중 혼선**: 개발/테스트 환경과 운영 환경의 스키마가 다르면
  로컬 테스트는 통과하지만 운영에서 실패.

- **양쪽 포팅**: PHP로 포팅한 후 양쪽 엔진(Python, PHP)이
  함께 실행될 때, 각각 다른 스키마를 기대하면 충돌.

#### 3.1.3 완화 전략

[Migration Portability Checklist](migration-portability-checklist.md):

1. **체크리스트 기반 리뷰**:
   - 모든 마이그레이션이 체크리스트(이름, collation, DDL 경계, ...)를
     통과하는지 확인.
   - PHP 마이그레이션도 같은 기준 적용.

2. **스키마 다이제스트 검증**:
   - Python/PHP 양쪽이 생성한 스키마를
     `DESCRIBE` 또는 information_schema로 추출해 비교.
   - 공통 스키마 정의(0461 `db/schema/*.sql`)에서 소스 오브.

3. **버전 추적**:
   - 모든 마이그레이션(Python, PHP)이
     `schema_version` 테이블의 버전을 동일하게 갱신.
   - 버전 불일치 발생 시 경고.

#### 3.1.4 검증 방법

**자동 검사**:
- `scripts/check_schema_consistency.py` (미정):
  각 마이그레이션 단계에서 PostgreSQL과 MariaDB (도커 컨테이너)의
  스키마를 자동 비교.

**테스트 케이스**:
```python
# tests/migrations/test_schema_consistency.py
def test_schema_consistency_after_migrations():
    """PostgreSQL과 MariaDB가 같은 최종 스키마를 생성한다."""
    pg_schema = extract_schema(pg_session, 'postgresql')
    maria_schema = extract_schema(maria_session, 'mariadb')
    
    # 테이블 이름, 컬럼, 인덱스, 제약이 모두 동일
    assert pg_schema.tables == maria_schema.tables
    assert pg_schema.indexes == maria_schema.indexes
    assert pg_schema.constraints == maria_schema.constraints

def test_schema_version_consistency():
    """양쪽 DB의 schema_version이 일치한다."""
    pg_version = get_schema_version(pg_session)
    maria_version = get_schema_version(maria_session)
    
    assert pg_version == maria_version
```

### 3.2 위험: 외래키 제약 순서 위반

#### 3.2.1 상황

마이그레이션 또는 seed fixture가 테이블을 생성할 때,
**외래키 참조 순서**를 무시하고 임의로 정하면
참조되는 부모 행이 아직 없어서 제약 위반이 발생한다.

#### 3.2.2 영향 범위

- **마이그레이션 실패**: 새 마이그레이션이 FK를 포함한 테이블을 생성할 때,
  부모 테이블이 이미 존재하지 않으면 실패.

- **데이터 로드 실패**: Seed fixture나 백업 복원 시,
  자식 테이블을 부모보다 먼저 로드하면 FK 제약 위반.
  ```sql
  # 잘못된 순서
  INSERT INTO revision (...) VALUES (...);  -- document가 없음! 실패
  INSERT INTO document (...) VALUES (...);
  
  # 올바른 순서
  INSERT INTO document (...) VALUES (...);
  INSERT INTO revision (...) VALUES (...);
  ```

- **복원 불가**: [Portable Restore Plan](portable-restore-plan.md)에서
  정의한 복원 절차가 외래키 순서를 지키지 않으면,
  JSON export나 SQL dump 복원에 실패.

#### 3.2.3 완화 전략

[Migration Portability Checklist](migration-portability-checklist.md),
[Portable Restore Plan](portable-restore-plan.md) §1.3:

1. **의존성 그래프 정의**:
   - [Persistence Boundaries](persistence-boundaries.md)에서
     정의한 FK 종속성 순서를 절대 규칙으로 삼음.
   - 예: user → document → revision → revision_edit

2. **마이그레이션 순서**:
   - 새 테이블 생성 시 부모 테이블이 먼저 생성되도록 배치.
   - FK 제약 추가는 부모 테이블이 이미 존재한 후.

3. **Seed/복원 로더**:
   - `SeedLoader`, JSON 복원 로더가
     의존성 순서대로 테이블을 순회하고 로드.

#### 3.2.4 검증 방법

**수동 리뷰**:
- 새 마이그레이션이 FK를 포함하면,
  [Persistence Boundaries](persistence-boundaries.md)의 종속성을
  따르는지 확인.

**테스트 케이스**:
```python
# tests/migrations/test_fk_ordering.py
def test_foreign_key_order_in_migration():
    """마이그레이션이 외래키 종속성 순서를 따른다."""
    migration = Alembic('0455_add_new_entity_table')
    
    # document가 이미 존재
    assert table_exists('document')
    
    # 마이그레이션 실행
    migration.up()
    
    # 새 테이블이 외래키를 정상적으로 참조
    new_table_schema = get_table_schema('new_entity')
    assert new_table_schema.foreign_keys[0].referenced_table == 'document'

def test_seed_fixture_fk_order():
    """Seed fixture가 외래키 순서대로 행을 로드한다."""
    loader = SeedLoader(db_session)
    
    # user → document → revision 순서로 로드
    loader.load('tests/fixtures/seed/complete.sql')
    
    # 모든 외래키 제약이 만족됨
    assert db_session.query(Document).count() > 0
    assert db_session.query(Revision).count() > 0
```

### 3.3 위험: 마이그레이션 파일 네이밍 충돌

#### 3.3.1 상황

Python과 PHP 마이그레이션이 각각 별도 디렉토리에서
버전 번호를 관리하면, 같은 번호의 파일이
두 쪽에서 다른 변경을 정의할 수 있다.

#### 3.3.2 영향 범위

- **스키마 불일치**: 0451 마이그레이션이
  PostgreSQL에서는 "컬럼 A 추가"를 하고
  PHP에서는 "컬럼 B 추가"를 하면,
  최종 스키마가 다름.

- **충돌 및 혼선**: 코드 리뷰 시 "0451은 뭘까?"하는
  혼선 발생.

#### 3.3.3 완화 전략

[Migration Portability Checklist](migration-portability-checklist.md),
포팅 시점(0459 이후) 정책:

1. **공통 마이그레이션 원본**:
   - 0461부터 `db/schema/*.sql`에서
     **공통 portable SQL 스키마 원본**을 정의.
   - Python, PHP 마이그레이션은 이 원본을 각각 파싱/변환해 적용.

2. **버전 분기**:
   - 그 전까지(0441-0460)는 Python Alembic과
     PHP 마이그레이션이 **독립적으로** 같은 변경을 정의.
   - 리뷰 시 양쪽이 체크리스트를 통과하는지 별도로 확인.

3. **정렬된 버전 추적**:
   - 양쪽이 모두 `schema_version` 테이블의 버전을 갱신해
     진행 상황을 동기화.

#### 3.3.4 검증 방법

**수동 리뷰**:
- PHP 마이그레이션(0459~0460) 추가 시,
  Python Alembic과 같은 변경을 하는지 확인.

**테스트 케이스**:
```python
# tests/migrations/test_version_consistency.py
def test_python_php_migration_versions_match():
    """Python과 PHP 마이그레이션이 같은 버전을 기록한다."""
    py_versions = list_migration_versions('migrations/versions')
    php_versions = list_migration_versions('php/migrations')
    
    # 0459 이전은 공통 부분 비교 불가 (각각 다른 변경)
    # 0461 이후는 db/schema 원본에서 생성되어야 함
    common_versions = set(py_versions) & set(php_versions)
    for ver in common_versions:
        if ver >= '0461':
            # db/schema 원본에서 생성됐는지 확인
            assert is_generated_from_schema_source(ver)
```

---

## 4. 종합 검증 전략

### 4.1 개발 시 로컬 검증

```bash
# 마이그레이션 추가 후
scripts/check_sql_denylist.py
scripts/check_schema_consistency.py  # 양쪽 DB 스키마 비교
scripts/test.sh -k migration        # 마이그레이션 테스트

# 저장소 코드 변경 후
scripts/test.sh -k persistence
scripts/qa.sh
```

### 4.2 코드 리뷰 체크리스트

- [ ] **Collation**: 모든 `VARCHAR`/`TEXT` 컬럼이 `utf8mb4_bin`을 명시하는가?
- [ ] **Transaction**: 여러 저장소 메서드를 호출하는 코드가
      `DocumentRevisionTransaction` 헬퍼를 사용하는가?
- [ ] **Migration**: 새 DDL이 여러 개면 별도 파일로 분리했는가?
      외래키 순서를 지키는가?

### 4.3 CI/CD 단계별 검증

**커밋 직후**:
- `scripts/qa.sh`: SQL denylist, 이름 길이, 기본 타입 검사.

**풀 리퀘스트 머지 전**:
- `scripts/test.sh`: 모든 유닛, 통합 테스트.
- 매뉴얼 코드 리뷰: 위 체크리스트.

**메인 브랜치 머지 후**:
- CD 파이프라인: 스테이징 환경에서
  PostgreSQL과 MariaDB 양쪽 배포.
- 스키마 비교 리포트.

---

## 5. 이후 단계와의 연계

- **0441-0450**: 이 문서가 식별한 위험들이 정책 문서(collation, transaction,
  migration)로 구체화.
- **0451-0460**: 개발자가 위 정책들을 따르며 위험 회피.
- **0461-0500**: PHP 포팅으로 Python/PHP 마이그레이션 분기; 이 문서의
  위험 항목이 양쪽을 검증하는 기준이 됨.
- **0501-0520**: 통합 테스트 및 양쪽 DB 운영 검증.

