# DB Phase Readiness Gate

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 최종 게이트 문서.
이 문서는 Phase C가 완료되었고 다음 단계(Phase D: UI)를 시작할 수 있는지를 판단하기 위한
필수 조건들을 명시한다. Phase C 동안 구축된 DB 계층 위에서 UI 개발이 안전하게 진행되기 위한
기반을 확인한다.

## 목적

Phase C(0441-0520)에서 ANSI SQL 중심의 이식 가능한 DB 계층을 구축했다면,
다음 Phase D(0521+)의 UI 개발을 시작하기 전에 **필수 조건 만족**, **자동 검사 통과**,
**문서 완성도** 세 가지를 확인한다. 이 게이트를 통과하지 못하면 UI 개발이 진행되지 않으며,
게이트를 통과하면 Phase D가 의존할 수 있는 안정적인 DB 인터페이스와 정책이 갖춰진 상태다.

## 대상

- Phase C 담당자: 게이트 통과 여부를 최종 확인.
- Phase D(UI) 개발자: 게이트 통과 후 아래 제약과 경계를 인지하고 개발 시작.
- 운영/검증자: 게이트 조건들이 실제로 만족되었는지 확인.

## 1. 필수 조건 (Prerequisites)

### 1.1 핵심 정책 문서 완성

다음 문서들이 **존재하고 최종 버전**이어야 한다:

| 문서 | 범위 | 검증 항목 |
|---|---|---|
| [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) | PostgreSQL 전용 기능 금지 목록 | RETURNING, ILIKE, JSONB, SERIAL 등 명시 |
| [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) | MariaDB 10.6+ 호환성 | 타입, 인덱스, transaction, collation 차이 기록 |
| [Portable Text Collation Policy](portable-text-collation-policy.md) | collation 전략 | utf8mb4_bin 명시, 대소문자 구분 확보 |
| [Portable Schema Naming Policy](portable-schema-naming-policy.md) | 이름 규칙 | 길이, 예약어, 문자 제약 고정 |
| [Migration Portability Checklist](migration-portability-checklist.md) | 마이그레이션 기준 | DDL 경계, 트랜잭션 안전성 |
| [Repository Transaction Policy](repository-transaction-policy.md) | Python/PHP 저장소 계약 | commit 경계, 원자성 보장 |
| [DB Adapter Contract](db-adapter-contract.md) | 공통 저장소 인터페이스 | Python/PHP 공통 의존성 |
| [DB Phase QA Checklist](db-phase-qa-checklist.md) | QA 경로 | 자동/선택/수동 검사 항목 |
| [DB Phase Risk Register](db-phase-risk-register.md) | 위험 요소 및 완화 | collation, transaction, migration 위험 |

### 1.2 핵심 스키마 파일 완성

다음 스키마 파일들이 **존재하고 ANSI SQL 기준을 만족**해야 한다:

| 파일 | 테이블 | 검증 항목 |
|---|---|---|
| `db/schema/document.sql` | document | PK, FK, collation, index 명 포팅 가능 |
| `db/schema/revision.sql` | revision | created_at 타입, FK 순서 |
| `db/schema/user.sql` | user, session | charset utf8mb4, 비밀번호 분리 |
| `db/schema/acl.sql` | acl_rule, acl_namespace_default | namespace/document 규칙 분리 |
| `db/schema/discussion.sql` | discussion_thread, discussion_comment, discussion_state | pagination 기반 |
| `db/schema/audit.sql` | audit_event | append-only, 파티션 없음 |
| `db/schema/jobs.sql` | job_definition, job_run | shared hosting sync 대응 |
| `db/schema/schema_migration.sql` | schema_version | 마이그레이션 상태 추적 |

**검증 방법**: `scripts/check_sql_denylist.py` 통과, 파일명 규칙 준수.

### 1.3 자동 검사 통과

#### 1.3.1 SQL feature 금지 목록 검사

```bash
scripts/qa.sh  # 자동 검사의 일부
```

**기준**:
- PostgreSQL 전용 기능(RETURNING, ILIKE, JSONB, SERIAL) 검출 0개.
- 모든 VARCHAR/TEXT에 COLLATE 명시 또는 주석에 이유 기록.
- 문자셋이 utf8mb4로 명시.

#### 1.3.2 마이그레이션 체크리스트 검증

모든 Alembic 마이그레이션(`migrations/versions/*.py`)이:
- [ ] 이름 규칙 준수 (소문자, 숫자, 언더스코어만).
- [ ] DDL 경계 안전 (한 파일 = 하나의 논리적 변경).
- [ ] 멱등성 확보 (IF NOT EXISTS 등).
- [ ] 외래키 순서 준수 ([Persistence Boundaries](persistence-boundaries.md) 참고).

#### 1.3.3 DB 모듈 경계 검사

```bash
scripts/check_db_module_boundaries.py  # scripts/qa.sh 경유
```

**기준**:
- 저장소 계층이 ORM (SQLAlchemy) 의존을 최소화.
- 도메인 모듈이 persistence 계층을 직접 import하지 않음.
- PHP 포팅 가능성을 해치지 않는 인터페이스.

#### 1.3.4 기존 테스트 통과

```bash
scripts/test.sh  # 모든 테스트 통과
```

**기준**:
- Python 저장소 테스트 100% 통과.
- 이식성 테스트(document, revision, ACL 등) 통과.
- MariaDB smoke 테스트 skip이 아닌 통과 (서버 준비 시).

### 1.4 PHP/Python 저장소 계약 기준

#### 1.4.1 Python 저장소 완성도

각 저장소(`src/modules/*/repository.py`)가:
- [ ] 인터페이스 정의 (메서드 서명).
- [ ] 에러 코드 반환 ([Portable Exception Code Policy](portable-exception-code-policy.md) 준수).
- [ ] 트랜잭션 경계 명시 (각 public 메서드 문서화).
- [ ] ORM 특정 기능 회피 (RETURNING 등 미사용).

#### 1.4.2 PHP PDO 스켈레톤

[0484-0485](php-db-ui-micro-job-prompts-0351-0670.md) 이후, 다음이 준비:
- [ ] `php/src/Persistence/Connection.php` — MariaDB/PostgreSQL DSN 수용.
- [ ] `php/src/Persistence/TransactionWrapper.php` — begin/commit/rollback.
- [ ] 에러 코드 registry — Python과 이름 일치.

현재 점: **placeholder 단계 허용**, 0510 시점에는 **인터페이스만** 필요.

### 1.5 문서화 요구사항

#### 1.5.1 운영 관련 문서

- [DB Adapter Selection Guide](db-adapter-selection.md) — 개발/테스트/shared hosting 기준.
- [Web Hosting DB Constraints](db-web-hosting-constraints.md) — 권한 제한, charset, 마이그레이션 제약.
- [PostgreSQL DSN Compatibility](postgresql-dsn-compatibility.md) — 기존 개발 환경 유지.
- [Portable Backup Format](portable-backup-format.md) — SQL/JSON 백업 경계.
- [Portable Restore Plan](portable-restore-plan.md) — MariaDB/PostgreSQL 복구 절차.

#### 1.5.2 개발자 가이드

- [DB Portability QA Paths](db-portability-qa-paths.md) — 로컬/CI 검사 경로.
- [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) — 실제 MariaDB 테스트 절차.
- [Portable Query Builder Policy](portable-query-builder-policy.md) — ad hoc SQL 금지.
- [Repository Transaction Policy](repository-transaction-policy.md) — Python/PHP 공통 규약.
- [Portable ID Policy](portable-id-policy.md) — UUID/string ID 기본.
- [Portable Datetime Policy](portable-datetime-policy.md) — UTC 저장, timezone 분리.

## 2. 테스트/검증 요구사항

### 2.1 자동 QA 통과

```bash
# 필수: 모두 통과 (exit code 0)
scripts/test.sh
scripts/qa.sh
```

**통과하면 다음이 보장됨**:
- SQL feature denylist 위반 0개.
- 마이그레이션 체크리스트 항목 만족.
- DB 모듈 경계 보존.
- 기존 기능 호환성 유지.

### 2.2 MariaDB Smoke 테스트 (선택)

서버가 준비되면:

```bash
export WIKI_MARIADB_DSN=mysql+pymysql://user:pass@host:3306/db
.venv/bin/python scripts/mariadb_smoke_check.py
```

**확인 항목**:
- 모든 테이블이 MariaDB에 생성 가능.
- FK 제약이 정상 작동.
- collation이 의도대로 적용.

### 2.3 코드 리뷰 체크리스트

Phase C 완료 리뷰 시:

- [ ] **Collation**: 모든 문자열 컬럼이 UTF-8 charset과 적절한 collation 명시.
- [ ] **Transaction**: 여러 모듈에 걸친 쓰기는 transaction helper 사용.
- [ ] **Migration**: 새로운 DDL 파일이 체크리스트 준수.
- [ ] **Named constraints**: PK, FK, INDEX 이름이 명시적이고 portable.
- [ ] **Error codes**: 저장소 메서드가 명확한 error code 반환.
- [ ] **ORM 의존**: ad hoc SQLAlchemy magic 없음 (ORM-specific 기능 회피).

## 3. Phase D 시작 전 필수 인식 사항

### 3.1 DB 경계 (UI 개발자 필독)

**UI 계층이 직접 DB에 접근하면 안 됨**:

```python
# ❌ 금지: UI 계층에서 직접 SQLAlchemy 사용
from sqlalchemy import select
@app.get('/documents')
def list_documents():
    return db.session.query(Document).all()

# ✅ 허용: 저장소를 통한 접근
@app.get('/documents')
def list_documents(repo: DocumentRepository):
    return repo.list_all()
```

**준수 이유**:
- PHP 대체 가능성 (저장소 인터페이스는 언어 독립).
- DB 이식성 (특정 ORM 특징 회피).
- 테스트 용이성 (fake repository로 대체).

### 3.2 쿼리 패턴 제약 (DBA/백엔드 개발자)

**사용 가능한 패턴**:
- ANSI SQL: SELECT, INSERT, UPDATE, DELETE, CREATE INDEX, ALTER TABLE.
- Transaction: BEGIN, COMMIT, ROLLBACK.
- Pagination: LIMIT/OFFSET.
- Sorting: ORDER BY (NULL 정렬 차이 회피).

**금지 패턴**:
- PostgreSQL RETURNING 절 — 대신 재조회 사용.
- ILIKE 검색 — 정규화 컬럼 + lower() 함수 또는 adapter 패턴.
- JSONB/JSON 쿼리 — 관계형 테이블로 정규화.
- SERIAL 시퀀스 — UUID/string ID 사용.
- 비표준 타입 — BOOL → TINYINT(1), ARRAY → 별도 테이블.

**참고**: [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md), [Portable Query Builder Policy](portable-query-builder-policy.md).

### 3.3 데이터 타입 표준화

| 용도 | 타입 | 설명 |
|---|---|---|
| PK/FK | VARCHAR(255) | string UUID 또는 nanoid 기본 |
| 제목/이름 | VARCHAR(255) UTF8MB4 COLLATE utf8mb4_bin | case-sensitive, 한글 지원 |
| 내용 | TEXT UTF8MB4 COLLATE utf8mb4_bin | 한글/이모지 지원 |
| timestamp | DATETIME(6) UTC | 서버 UTC 기본, 표시 시 timezone 변환 |
| 부울 | TINYINT(1) | 0/1, BOOL 비표준 회피 |
| 정수 | INT 또는 BIGINT | DB 기본값 의존 최소화 |

### 3.4 공유 호스팅 제약 인식

Phase D 이후, shared hosting 배포 시:

- **DDL 권한 없음**: 테이블 생성/삭제는 설치 단계에서만.
- **단일 DB**: 여러 데이터베이스 참조 불가.
- **마이그레이션 권한 제약**: 호스팅 지원팀 의존.

**준비 사항**:
- [0517](php-db-ui-micro-job-prompts-0351-0670.md): 웹에서 실행 가능한 마이그레이션 정책.
- [0518](php-db-ui-micro-job-prompts-0351-0670.md): installer DB check skeleton.

## 4. 다음 단계로의 전환 (Phase D Handoff)

### 4.1 Phase D 개발자가 가져가야 할 것

1. **문서**:
   - [DB Adapter Contract](db-adapter-contract.md) — 저장소 인터페이스.
   - [DB Phase QA Checklist](db-phase-qa-checklist.md) — 유지할 검사 항목.
   - [Portable Exception Code Policy](portable-exception-code-policy.md) — 에러 코드.
   - [Repository Transaction Policy](repository-transaction-policy.md) — 트랜잭션 경계.

2. **코드**:
   - `src/modules/*/repository.py` — 저장소 인터페이스.
   - `tests/modules/*/test_*_portable*.py` — 이식성 테스트.
   - `src/persistence/` — 어댑터/트랜잭션 기반.

3. **제약**:
   - §3.1~3.4 필수 준수.
   - Phase C 정책 위반하는 코드 추가 금지.

### 4.2 Phase D 진입 조건

```
Phase D(0521+) 시작 <==> 다음 모두 만족:
  1. scripts/test.sh, scripts/qa.sh 통과 ✓
  2. 모든 Phase C 문서 완성 ✓
  3. Python 저장소 계약 고정 ✓
  4. PHP 스켈레톤 (placeholder OK) ✓
  5. 리뷰: DB 경계, 쿼리 패턴, 타입 표준화 확인됨 ✓
```

### 4.3 연계 작업

Phase D 내 DB 관련 작업:
- [0518](php-db-ui-micro-job-prompts-0351-0670.md): PHP installer DB check.
- [0519](php-db-ui-micro-job-prompts-0351-0670.md): installer check 테스트.
- 이후 UI 작업들: 저장소를 통해서만 DB 접근.

## 5. 게이트 점검표 (Gate Checklist)

Phase C 완료 확인용:

### 5.1 문서화 ✓

- [ ] ANSI SQL Persistence Policy 완성.
- [ ] MariaDB Compatibility Matrix 완성.
- [ ] 모든 portable 정책 문서 완성 (collation, ID, timestamp, naming).
- [ ] Migration Portability Checklist 완성.
- [ ] DB Phase QA Checklist 완성.
- [ ] DB Phase Risk Register 완성.
- [ ] DB Adapter Contract 완성.
- [ ] Web Hosting DB Constraints 완성.

### 5.2 스키마 ✓

- [ ] `db/schema/*.sql` 모두 ANSI SQL 기준 충족.
- [ ] 모든 VARCHAR/TEXT에 utf8mb4, collation 명시.
- [ ] 외래키 순서, 제약 이름 명시.
- [ ] schema_migration.sql 준비.

### 5.3 자동 검사 ✓

- [ ] `scripts/test.sh` 통과.
- [ ] `scripts/qa.sh` 통과 (SQL denylist, boundary check).
- [ ] MariaDB smoke test skip 아닌 통과 (서버 있을 때).

### 5.4 저장소 계약 ✓

- [ ] 모든 Python 저장소 메서드 인터페이스 고정.
- [ ] 에러 코드 registry 완성.
- [ ] 트랜잭션 경계 명시.
- [ ] PHP 스켈레톤 Connection/Transaction 준비.

### 5.5 코드 리뷰 ✓

- [ ] 마이그레이션 체크리스트 준수 확인.
- [ ] DB 경계 보존 (UI가 저장소 사용).
- [ ] ORM 의존 회피 확인.
- [ ] Collation 일관성 확인.

## 6. 게이트 미통과 시 조치

아래 항목 중 하나라도 미충족 시 **Phase D 진입 금지**:

| 상태 | 원인 | 조치 |
|---|---|---|
| `scripts/qa.sh` 실패 | SQL 금지 기능 또는 경계 위반 | Phase C 내 정책 준수 작업 추가 |
| 문서 누락 | 정책 문서 미완성 | 누락된 문서 작성 (Phase C 범위 내) |
| 스키마 불일치 | PostgreSQL/MariaDB 차이 | db/schema/*.sql 수정 (Phase C 범위) |
| 저장소 계약 불완전 | ORM 의존 또는 메서드 서명 불안정 | 저장소 인터페이스 정리 (Phase C 범위) |

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 금지 기능 원본.
- [DB Phase QA Checklist](db-phase-qa-checklist.md) — 검사 항목 상세.
- [DB Phase Risk Register](db-phase-risk-register.md) — 위험 요소 원본.
- [DB Adapter Contract](db-adapter-contract.md) — 저장소 인터페이스.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) — Phase C 잡 정의.
