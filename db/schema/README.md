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

## 0461이 채우는 것

- `document.sql`: `src/persistence/models.py`의 `DocumentORM`,
  `migrations/versions/0002_add_document_table.py`와 동일한 결과를 내는
  portable `CREATE TABLE` 문. 이 파일부터 PostgreSQL/MariaDB 차이(ID/FK,
  timestamp, text collation)를 컬럼별 주석으로 분리해 남긴다 — 실제 DDL은
  두 DB 모두에서 그대로 실행되는 공통 문법만 쓰고, 차이가 나는 지점은
  주석으로만 설명한다(collation 등 컬럼 단위 강제가 필요 없는 이유는 파일
  안의 주석 참고).

## 0462가 채우는 것

- `revision.sql`: `src/persistence/models.py`의 `RevisionORM`,
  `migrations/versions/0003_add_revision_table.py`와 동일한 결과를 내는
  portable `CREATE TABLE` 문. `document_id`는 `document.sql`(0461)이 만든
  `document` 테이블을 참조하는 `fk_revision_document_id` FK를 갖는다.
  `parent_revision_id`는 ORM/마이그레이션 원본과 동일하게 FK 없이 둔다.

## 0463이 채우는 것

- `account.sql`: `src/modules/user/model.py`의 `User`와
  [User Portable Repository Plan](../../docs/user-portable-repository-plan.md)
  §2가 확정한 컬럼(`id`, `username`, `display_name`)을 옮기는 portable
  `CREATE TABLE` 문. 테이블 이름은 `user`가 아니라 [Portable Schema Naming
  Policy §5](../../docs/portable-schema-naming-policy.md#5-예약어-회피)의
  예약어 회피 규칙에 따라 `account`다. 비밀번호/세션은 이 테이블에 두지
  않는다 — 비밀번호는 별도 컬럼/테이블(번호 미배정), 세션은
  `user_session` 테이블(0464)로 분리한다. `User` 도메인 모델이
  `created_at`/`updated_at`을 갖지 않아 이 파일도 두 컬럼을 두지 않는다.

## 0464가 채우는 것

- `user_session.sql`: `src/modules/user/session.py`의 `Session`,
  `src/modules/user/session_repository.py`의 `SessionRepository`와
  [User Portable Repository Plan §3](../../docs/user-portable-repository-plan.md#3-session--user_session-테이블)이
  확정한 컬럼(`id`, `account_id`, `created_at`, `expires_at`)을 옮기는
  portable `CREATE TABLE` 문. `account_id`는 `account.sql`(0463)이 만든
  `account` 테이블을 참조하는 `fk_user_session_account_id` FK를 갖는다.
  `SessionRepository`가 `create`/`get`/`delete`만 요구하고 모두 `id`(PK)
  기준이라 추가 인덱스는 두지 않는다.

## 0465가 채우는 것

- `acl_rule.sql`: `src/modules/acl/rule.py`의 `Rule`, `document_acl.py`의
  `DocumentAcl`과 [ACL Portable Repository Plan
  §3](../../docs/acl-portable-repository-plan.md#3-rule문서-범위--acl_rule-테이블)이
  확정한 컬럼(`id`, `document_id`, `subject_type`, `subject_id`,
  `permission`, `effect`, `expires_at`, `sort_order`)을 옮기는 portable
  `CREATE TABLE` 문. `document_id`는 `document.sql`(0461)이 만든
  `document` 테이블을 참조하는 `fk_acl_rule_document_id` FK를 갖는다.
  `subject_id`는 `USER`/`GROUP`에 따라 참조 대상이 갈리는 다형 참조라
  FK를 걸지 않는다. `sort_order`는 규칙 우선순위(first-match-wins)를
  재현하는 전용 정수 컬럼이며, `UNIQUE(document_id, sort_order)`
  (`uq_acl_rule_document_id_sort_order`)로 같은 문서 안 순번 중복을
  막는다.
- `acl_namespace_rule.sql`: `namespace_defaults.py`의
  `NamespaceAclDefaults`와 [ACL Portable Repository Plan
  §4](../../docs/acl-portable-repository-plan.md#4-rule네임스페이스-기본값--acl_namespace_rule-테이블)가
  확정한 컬럼(`id`, `namespace`, `subject_type`, `subject_id`,
  `permission`, `effect`, `expires_at`, `sort_order`)을 옮기는 portable
  `CREATE TABLE` 문. `acl_rule.sql`과 같은 `Rule` 도메인 모델을 다루지만
  키 컬럼 성격이 달라(`document_id`는 FK 필수, `namespace`는 FK 대상이
  없는 자유 문자열) 별도 테이블로 분리했다. `UNIQUE(namespace,
  sort_order)`(`uq_acl_namespace_rule_namespace_sort_order`)로 같은
  네임스페이스 안 순번 중복을 막는다.

## 0466이 채우는 것

- `discussion_thread.sql`: `src/modules/discussion/thread.py`의
  `DiscussionThread`, `state.py`의 `ThreadState`와 [Discussion Portable
  Repository Plan
  §3](../../docs/discussion-portable-repository-plan.md#3-discussionthread--discussion_thread-테이블)이
  확정한 컬럼(`id`, `document_id`, `title`, `created_by`, `status`,
  `created_at`, `closed_at`, `paused_at`)을 옮기는 portable `CREATE TABLE`
  문. `document_id`는 `document.sql`(0461)이 만든 `document` 테이블을
  참조하는 `fk_discussion_thread_document_id` FK를 갖는다. `status`는
  `ThreadState`가 도메인 계층에서 아직 검증되지 않아 계획 문서 §6이 확정한
  대로 `CHECK` 제약 없이 `VARCHAR(20)` 자유 문자열로 둔다.
- `discussion_comment.sql`: `comment.py`의 `DiscussionComment`와 [Discussion
  Portable Repository Plan
  §4](../../docs/discussion-portable-repository-plan.md#4-discussioncomment--discussion_comment-테이블)가
  확정한 컬럼(`id`, `thread_id`, `body`, `created_by`, `is_hidden`,
  `created_at`, `hidden_at`)을 옮기는 portable `CREATE TABLE` 문.
  `thread_id`는 `discussion_thread.sql`(같은 태스크)이 만든
  `discussion_thread` 테이블을 참조하는 `fk_discussion_comment_thread_id`
  FK를 갖는다.
- 두 파일 모두 계획 문서 §5가 확정한 페이지네이션 결정성 요구에 따라
  `(정렬 대상 FK 컬럼, created_at, id)` 복합 `CREATE INDEX` 문을 별도로
  둔다 — [ANSI SQL Persistence Policy](../../docs/ansi-sql-persistence-policy.md)가
  금지하는 것은 부분 인덱스(`WHERE` 절 포함)뿐이고 일반 `CREATE INDEX`는
  두 DB 모두의 표준 기능이라 이 디렉터리의 다른 파일들과 달리 `CREATE
  TABLE` 외의 문을 추가로 포함한다.

## 0467이 채우는 것

- `audit_event.sql`: `src/modules/acl/audit_event.py`의 `AclAuditEvent`,
  `src/modules/discussion/audit_event.py`의 `DiscussionAuditEvent`와 [Audit
  Portable Repository Plan
  §3](../../docs/audit-portable-repository-plan.md#3-audit_event-테이블)이
  확정한 컬럼(`id`, `category`, `action`, `entity_id`, `related_entity_id`,
  `actor_id`, `occurred_at`)을 옮기는 portable `CREATE TABLE` 문.
  `acl_audit_event`/`discussion_audit_event`로 나누지 않고 `audit` 모듈이
  소유하는 단일 테이블로 통합한다(계획 문서 §2). `entity_id`/
  `related_entity_id`는 `category`에 따라 `acl_rule`/`discussion_thread`나
  `document`/`discussion_comment`를 가리키는 다형 참조라 FK를 걸지 않는다
  (계획 문서 §4). `updated_at` 컬럼을 두지 않아 append-only 의도를 표현한다
  (계획 문서 §5). 인덱스는 계획 문서 §7이 아직 확립된 조회 패턴이 없다고
  판단해 이 태스크에서는 추가하지 않는다.

## 이후 채워질 파일

- **0468**: jobs 테이블.
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
