# DB Phase QA Checklist

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서. 이 체크리스트는
PostgreSQL과 MariaDB 양쪽에서 동작하는 DB 계층을 보장하기 위해 필요한
자동 검사, 선택 smoke 테스트, PHP PDO 스켈레톤 검증을 한 곳에 정리한다.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md),
[Migration Portability Checklist](migration-portability-checklist.md),
[DB Portability QA Paths](db-portability-qa-paths.md),
[MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md)이 이미 정의한
검사 항목들을, **새 DB 기능을 추가하거나 PHP 기반 대체를 준비할 때** 로컬/CI
검사 경로별로 빠짐없이 실행하기 위한 체크리스트로 묶는다.

## 목적

Phase C는 스키마·마이그레이션·SQL 쿼리를 ANSI SQL 중심으로 재설계해,
PostgreSQL 전용 기능 없이 MariaDB에서도 동작하게 한다. 이 과정에서 세 가지
검사 경로가 필요하다:

1. **자동 검사** (`scripts/qa.sh`): SQL feature 금지 목록, 마이그레이션
   체크리스트, 코드 경계 검사.
2. **선택 실행** (MariaDB 서버 필요): 실제 MariaDB에 스키마를 적용하는 smoke
   테스트.
3. **PHP PDO 스켈레톤**: 향후 PHP 기반 저장소가 Python 계약과 일치하는지
   검증하기 위한 스켈레톤의 완성도.

이 문서는 세 경로를 한 곳에 정리해, 새 DB 관련 작업을 추가하거나 PHP로
교체할 때 각 항목을 누락하지 않도록 한다.

## 적용 범위

- 새로운 테이블/마이그레이션 추가 시의 검증 대상.
- [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP PDO 스켈레톤 추가.
- Python repository와 PHP PDO 계약 일치성 확인.

이 문서가 정하지 않는 것:

- 기존 검사 스크립트의 구현 세부사항 — 각 스크립트의 공식 문서 참고.
- 성능 최적화, 데이터 마이그레이션 전략 — Phase D/운영 정책 범위.
- CI/CD 파이프라인 구축 — 이 문서는 로컬 및 `scripts/run-next-task.sh`
  자동 게이트의 검사만 다룬다.

## 1. 자동 검사 (로컬 + CI 경로, DB 서버 불필요)

개발자가 커밋 전에 반드시 통과해야 하는 검사들. `scripts/qa.sh`에 포함되어
자동 실행되거나, CI의 `scripts/run-next-task.sh`가 자동으로 실행한다.

### 1.1 ANSI SQL feature 금지 목록 검사

**목적**: PostgreSQL 전용 기능(RETURNING, JSONB, ILIKE, SERIAL 등)이
코드베이스에 숨어 있지는 않은지 자동으로 확인한다.

**자동화**: `scripts/check_sql_denylist.py`가 이미 모든 SQL 파일과 마이그레이션을
검사한다 (`scripts/qa.sh` 경유).

**체크리스트**:

- [ ] 새로운 `.sql` 파일을 추가했다면 `db/schema/*.sql`에 포함되어 있다.
  (`scripts/qa.sh`가 검사 대상에 포함시킨다.)
- [ ] 새로운 Alembic 마이그레이션을 추가했다면
  `migrations/versions/*.py`에 포함되어 있다. (자동 검사 대상)
- [ ] repository 쿼리 코드를 추가했다면
  `src/modules/*/repository.py`와 `src/persistence/` 아래 파일들이
  검사 대상에 포함된다. (자동 검사)
- [ ] 검사 통과: 로컬에서 `scripts/qa.sh` 실행 후 금지 목록 오류 없음을 확인.

**참고**: [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의
금지 목록 표 참고. 자동 검사가 거짓 양성(주석 속 금지 기능 언급 등)을
걸러내는 방식은 `check_sql_denylist.py` 코드 참고.

### 1.2 마이그레이션 Portability 체크리스트

**목적**: 새로운 Alembic 마이그레이션이 향후 PHP 마이그레이션과 같은
스키마를 만들 수 있도록 일관된 규칙을 따르는지 확인한다.

**체크리스트**: [Migration Portability Checklist](migration-portability-checklist.md)의
1절(자동 검사) ~ 5절(순방향/재실행 안전성)을 따른다.

- [ ] **SQL feature 금지** (자동): `scripts/qa.sh` 통과 = 통과.
- [ ] **이름 규칙** (수작업): 테이블/컬럼/인덱스 이름이 소문자 ASCII,
  숫자, 밑줄만 사용. 제약 이름이 `pk_<table>` 등 명시적 패턴 준수.
  예약어 회피 확인.
- [ ] **트랜잭션 경계** (수작업): DDL이 암묵적 커밋되고 롤백 불가능하다는
  전제로 설계. 한 파일 = 하나의 논리적 변경. `downgrade()`가 역방향
  DDL로 명시 작성됨.
- [ ] **컬럼 타입** (수작업): PK/FK는 `String(255)`, timestamp는
  `DateTime(timezone=True)`, 문자열은 collation 전제 확인.
- [ ] **순방향/재실행 안전성** (수작업): 선형 히스토리 유지, 멱등성 가정
  없음.

**참고**: [Migration Portability Checklist](migration-portability-checklist.md)의
§2~§5 항목을 마이그레이션 코드 리뷰 시점에 사람이 확인한다. 1절(금지 목록)은
이미 자동 검사로 다뤄진다.

### 1.3 DB 모듈 경계 검사

**목적**: 저장소 계층이 특정 ORM이나 프레임워크에 과도하게 결합되지는
않았는지 확인한다 (PHP 포팅 가능성).

**자동화**: `scripts/check_db_module_boundaries.py`가 import 정책을
검사한다 (`scripts/qa.sh` 경유).

**체크리스트**:

- [ ] 새로운 repository 파일을 추가했다면 검사 대상에 포함되는지 확인.
- [ ] import 제약 위반 없음 (예: `src/modules/document/repository.py`가
  Flask 직접 import 하지 않음).
- [ ] `scripts/qa.sh` 통과 확인.

**참고**: [DB Module Boundary Check](db-module-boundary-check.md)

### 1.4 기존 테스트 통과

**목적**: 새로운 스키마/마이그레이션 변경이 기존 코드와 호환되는지 검증한다.

**자동화**: `scripts/test.sh`가 pytest 전체를 실행한다 (`scripts/qa.sh`
경유).

**체크리스트**:

- [ ] `scripts/test.sh` 통과.
- [ ] 새로운 테스트를 추가했다면 합께 커밋됨.
- [ ] 기존 smoke 테스트 skip 로직(`test_mariadb_smoke_check.py` 등의
  `@pytest.mark.skipif(no_dsn)`)이 작동함을 확인 (로컬에서 MariaDB 없으면
  skip 됨).

## 2. 선택 실행: MariaDB Smoke 테스트 (서버 필요)

MariaDB 실제 서버가 준비돼 있을 때만 실행되는 선택 검사. 로컬과 CI 양쪽에서
**실행 여부는 환경 변수로 판단**되며, 서버가 없으면 실패가 아니라 skip으로 처리된다.

**조건**: `WIKI_MARIADB_DSN=mysql+pymysql://user:pass@host:3306/db`
환경 변수 설정 시에만 실행.

**목적**: `db/schema/*.sql`의 각 파일이 실제 MariaDB 10.6+ 서버에서
오류 없이 실행되는지 확인한다. 이는 **문법 검사가 아니라 실제 MariaDB
파서·엔진의 동작 검증**.

### 2.1 Smoke 테스트 검사 단계

[MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md)을 따른다.

- [ ] **접속 확인**: DSN이 유효하고 MariaDB에 접속 가능한지 확인.
  접속 실패 시 skip.
- [ ] **격리된 대상 스키마 준비**: smoke 전용 DB/스키마를 새로 만들거나
  기존 내용 삭제.
- [ ] **순서대로 적용**: 11개 테이블을 FK 의존 순서로 적용. 파일 가공 없이
  원본 SQL 그대로 실행.
- [ ] **테이블 존재 확인**: 11개 테이블 모두 생성됐는지 카탈로그 확인.
- [ ] **정리**: smoke 스키마 삭제해 반복 실행이 깨끗한 상태에서 시작.

### 2.2 체크리스트

- [ ] MariaDB 서버 준비 (로컬 Docker/실제 원격 인스턴스).
- [ ] `WIKI_MARIADB_DSN` 환경 변수 설정.
- [ ] 새로운 `.sql` 파일을 추가했다면:
  - [ ] FK 의존 순서 목록(`db/schema/README.md`와 smoke plan)에 추가.
  - [ ] 파일명이 정책(소문자, `_` 구분자) 따름.
  - [ ] 마이그레이션 기록 테이블(`schema_migration.sql`) 존재 확인.
- [ ] `scripts/mariadb_smoke_check.py` 실행:
  ```bash
  WIKI_MARIADB_DSN=mysql+pymysql://root:password@127.0.0.1:3306/test_wiki \
    .venv/bin/python scripts/mariadb_smoke_check.py
  ```
- [ ] 모든 테이블이 성공적으로 생성됨 확인. 오류 메시지 없음.
- [ ] 테이블 개수가 예상 11개와 일치 확인.

**참고**: [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md).
실행 후 자동으로 smoke 스키마는 정리된다(파괴 불가능한 검사).

## 3. PHP PDO 스켈레톤 검증

[0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP PDO connection
skeleton이 추가되면, Python 저장소와 계약을 일치시키기 위한 검증 항목들.
현재(0500 시점)는 Python 쪽 준비 단계이므로, 아래 항목들은 **0484~0485
완료 후** 실제 PHP 코드 리뷰 때 적용한다.

### 3.1 PHP PDO Connection Skeleton (0484 이후)

**검증 항목**:

- [ ] `php/src/Persistence/Connection.php`가 존재하고, MariaDB/PostgreSQL
  DSN을 모두 수용 가능.
- [ ] DSN 형식이 `mysql+pymysql://...`(MariaDB) 와 `postgresql://...`(PostgreSQL)
  을 둘 다 지원.
- [ ] 환경 변수 `WIKI_MARIADB_DSN`, `WIKI_DATABASE_URL` 읽기 지원.
- [ ] 접속 실패 시 명확한 오류 메시지(DSN 형식 오류, 서버 부재 등).
- [ ] 주석과 docblock이 Python `src/app/config.py`의 DSN config 설명과
  대응.

**참고**: [PostgreSQL DSN Compatibility](postgresql-dsn-compatibility.md).
0484 task notes 참고.

### 3.2 PHP PDO Transaction Wrapper (0485 이후)

**검증 항목**:

- [ ] `php/src/Persistence/TransactionWrapper.php` 또는 유사 파일이 존재.
- [ ] `begin()`, `commit()`, `rollback()` 메서드 제공.
- [ ] Python `src/persistence/transaction.py`의 계약과 네이밍 일치.
- [ ] 주석이 [Repository Transaction Policy](repository-transaction-policy.md)의
  계약 설명과 대응.
- [ ] 스켈레톤 단계이므로 구현은 placeholder 가능 (pass 또는 실제 PDO 호출).

**참고**: [Repository Transaction Policy](repository-transaction-policy.md).
0485 task notes 참고.

### 3.3 PHP Repository Port 구현 준비

향후 [0486~0488](php-db-ui-micro-job-prompts-0351-0670.md) 단계에서
Python repository 포트를 PHP로 구현할 때:

- [ ] PHP 메서드 시그니처가 Python 메서드와 일치.
- [ ] 입출력 모델(DTO)의 필드명이 Python과 동일.
- [ ] 에러 코드 반환이 [Portable Exception Code Policy](portable-exception-code-policy.md)
  준수.
- [ ] 트랜잭션 경계가 Python과 동일 시점에서 시작/종료.

## 4. QA 실행 순서

### 4.1 로컬 개발 중 (언제든 수동 실행)

```bash
# 1단계: 자동 검사 (필수, DB 불필요)
scripts/qa.sh

# 2단계: Smoke 테스트 (선택, MariaDB 서버 필요)
export WIKI_MARIADB_DSN=mysql+pymysql://root:password@127.0.0.1:3306/test_wiki
.venv/bin/python scripts/mariadb_smoke_check.py
```

### 4.2 CI 경로 (커밋 전 자동 게이트)

[Runner](runner.md)가 매 태스크 완료 후 자동 실행:

```bash
# 1단계: 자동 검사만 실행 (§1 전체)
scripts/test.sh
scripts/qa.sh

# 2단계 skip: MariaDB smoke는 자동 게이트에 포함 안 함 (환경이 준비 안 됨)
```

### 4.3 수동 검증 (필요 시)

새로운 DB 기능 추가 후 코드 리뷰 체크리스트로 활용:

- [ ] §1 자동 검사 완료.
- [ ] 마이그레이션 portability 체크리스트 확인.
- [ ] PHP PDO 스켈레톤이 준비 중이면 계약 일치 확인.

## 5. 이 체크리스트가 다루지 않는 것

- **쿼리 성능 검증** — Phase D 이후 최적화 작업.
- **데이터 마이그레이션 도구** — 별도 phase/작업.
- **실제 배포 환경 검증** — 운영 정책.
- **PostgreSQL smoke 테스트** — §2는 MariaDB만 다루고, PostgreSQL은
  이미 개발 환경이므로 기존 테스트로 검증.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — §1 금지
  목록 원출처.
- [Migration Portability Checklist](migration-portability-checklist.md) — §1.2,
  마이그레이션 규칙 원출처.
- [DB Portability QA Paths](db-portability-qa-paths.md) — §1, §2 자동·CI
  경로 구성 원출처.
- [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) — §2 실행
  단계 원출처.
- [DB Module Boundary Check](db-module-boundary-check.md) — §1.3 경계 검사
  문서.
- [Repository Transaction Policy](repository-transaction-policy.md) — §3.2
  트랜잭션 계약 원출처.
- [PostgreSQL DSN Compatibility](postgresql-dsn-compatibility.md) — §3.1 DSN
  형식 원출처.
- [Portable Exception Code Policy](portable-exception-code-policy.md) — §3.3
  에러 코드 원출처.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 및 0484~0485 PHP PDO 스켈레톤 태스크.
- [Runner](runner.md) — §4.2 CI 자동 게이트 원출처.
