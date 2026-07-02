# db/schema — Portable Table Definitions

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 골격.
[db/README.md](../README.md)가 예고한 자리를 이 태스크(0460)가 만든다.

## 목적

`migrations/versions/`의 Alembic 마이그레이션이 생성하는 스키마와 항상
같은 결과를 내야 하는 portable SQL 원본을 테이블 단위 파일로 둔다. PHP
마이그레이션 러너(0484 이후)는 여기 있는 `CREATE TABLE` 문을 그대로
실행해 Python/PHP 양쪽이 동일한 스키마를 갖게 한다.

## 파일 규칙

- 파일 하나에 테이블 하나: `<table>.sql` (테이블 이름과 동일, [Portable
  Schema Naming Policy](../../docs/portable-schema-naming-policy.md)의
  단수형·소문자 규칙을 따른다).
- 내용은 [ANSI SQL Persistence Policy](../../docs/ansi-sql-persistence-policy.md)의
  금지 목록을 지키는 `CREATE TABLE` 문으로 한정한다.
- 컬럼 타입/이름은 [Portable Schema Naming
  Policy](../../docs/portable-schema-naming-policy.md), [Portable ID Column
  Policy](../../docs/portable-id-column-policy.md), [Portable Timestamp
  Column Policy](../../docs/portable-timestamp-column-policy.md), [Portable
  Text Collation Policy](../../docs/portable-text-collation-policy.md)를
  따른다.
- PK/FK/UNIQUE/인덱스 이름은 명시적으로
  `pk_<table>`/`fk_<table>_<column>`/`uq_<table>_<column>`/
  `ix_<table>_<column>` 패턴을 쓴다(Naming Policy 4절).

## 이 태스크(0460)가 채우는 것

- `schema_migration.sql`: [db/README.md](../README.md)가 이미 확정한
  적용 이력 테이블의 **ANSI 중심 초안**. 도메인 테이블(`document`,
  `revision` 등)이 아니라, portable 마이그레이션 러너 자체가 필요로 하는
  기반 테이블이라 domain 테이블보다 먼저 이 자리에 둔다.
- 이 초안은 아직 PostgreSQL/MariaDB 차이를 주석으로 분리하지 않는다 —
  단순한 `VARCHAR`/`TIMESTAMP` 컬럼만 쓰므로 지금은 차이가 없다. 방언별
  주석 분리 패턴은 [0461 document table portable SQL](../../docs/php-db-ui-micro-job-prompts-0351-0670.md)부터
  적용한다.

## 이후 채워질 파일

- **0461~0468**: `document`, `revision`, `account`, `user_session`, ACL,
  discussion, audit, jobs 테이블.
- **0469**: 이 디렉터리 전체에 대한 SQL feature 금지 목록 자동 검사(lint
  테스트).
- **0493**: PHP 웹호스팅 installer가 참조할 별도의 schema version 테이블.

## 관련 문서

- [db/README.md](../README.md) — `schema_migration` 테이블 스펙(이름,
  컬럼, 적용 방식)의 원출처.
- [Migration Portability Checklist](../../docs/migration-portability-checklist.md) —
  이 디렉터리의 파일이 지켜야 할 체크리스트.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](../../docs/php-db-ui-micro-job-prompts-0351-0670.md) —
  Phase C 잡 목록 전체.
