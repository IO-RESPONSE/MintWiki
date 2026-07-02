# MariaDB Migration Smoke Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[Migration Portability Checklist](migration-portability-checklist.md),
[db/README.md](../db/README.md), [db/schema](../db/schema/README.md)가
정한 규칙을 실제 MariaDB 서버에 대해 확인하는 **smoke 테스트 계획**을
세운다. 이 문서는 새 정책을 만들지 않는다 — `db/schema` 아래 portable SQL
원본이 실제 MariaDB 10.6+에서 오류 없이 적용되는지 확인하는 절차만
고정한다. 실제 실행 스크립트는 만들지 않는다(0481의 범위).

## 목적

지금까지 Phase C 문서들(마이그레이션 체크리스트, compatibility matrix,
naming/ID/timestamp/collation 정책)은 모두 **문서 검토**와 `check_sql_denylist.py`
같은 **정적 검사**로만 검증됐다. `db/schema`의 portable SQL 원본이 실제
MariaDB 서버에서 `CREATE TABLE`을 실행했을 때도 오류 없이 동작하는지는
아직 한 번도 확인된 적이 없다 — 문법이 ANSI SQL 부분집합처럼 보여도, 실제
MariaDB 파서/엔진이 거부하는 지점(식별자 인용, 예약어, 타입 별칭 처리 등)은
실행해 보기 전까지 확신할 수 없다.

이 문서는 그 간극을 메우는 **smoke 테스트**의 범위, 실행 조건, 단계,
실패 판정 기준을 계획한다. "smoke 테스트"는 스키마가 실제로 운영 가능한지
검증하는 것이 아니라, **`db/schema`의 각 SQL 파일이 깨끗한 MariaDB
데이터베이스에 순서대로 적용됐을 때 오류 없이 끝나는가**만 확인하는 가장
얕은 수준의 확인이다.

## 적용 범위

- 대상: `db/schema/*.sql`(0460~0468이 추가한 11개 테이블 정의)을
  MariaDB 10.6+ 서버에 순서대로 적용하는 smoke 확인.
- 이 문서가 정하는 것: 실행 조건(선택 실행/skip 기준), 적용 순서,
  단계별 확인 항목, 실패를 어떻게 원인별로 구분하는지.
- 이 문서가 정하지 않는 것(범위 밖):
  - 실제 실행 스크립트 구현 — [0481 Add optional MariaDB test
    script](php-db-ui-micro-job-prompts-0351-0670.md)의 범위. 이 문서는
    그 스크립트가 따를 계획만 고정한다.
  - CI 파이프라인 연결 — 실제 CI 연결은 후속 잡이다(이 태스크 노트).
    지금은 로컬에서 선택적으로 실행하는 것만 가정한다.
  - `db/migrations/`를 순서대로 적용하는 마이그레이션 러너 자체 —
    [db/README.md](../db/README.md)가 "0484 이후 PHP skeleton, 0505
    dry-run 명령"으로 남겨 둔 범위. 지금은 `db/migrations/`가 비어 있어
    smoke 대상이 아니다(`db/schema/*.sql`만 대상).
  - 한글 정렬/collation 동작 검증 — [0511 MariaDB collation fixture
    tests](php-db-ui-micro-job-prompts-0351-0670.md)의 범위. smoke는
    "적용된다/안 된다"만 보고, 정렬 결과의 정확성은 보지 않는다.
  - 성능/부하 확인 — smoke의 목적이 아니다.

## 1. 실행 조건 (선택 실행)

**규칙: 이 smoke 테스트는 MariaDB 서버가 로컬/CI 환경에 준비돼 있을 때만
실행되고, 없으면 실패가 아니라 skip으로 처리한다.**

- 실행 여부는 [MariaDB DSN Config Placeholder](../src/app/config.py)가
  이미 정의한 `WIKI_MARIADB_DSN` 환경 변수(0470,
  [postgresql-dsn-compatibility.md](postgresql-dsn-compatibility.md)가
  기록한 `mysql+pymysql://...` 형식)의 존재 여부로 판단한다 — 이 값이
  비어 있으면 smoke 스크립트는 접속을 시도하지 않고 곧바로 skip한다.
- 이유: 개발자 로컬 환경과 지금 CI 모두 MariaDB 서버를 기본으로 두지
  않는다(현재 개발 환경은 PostgreSQL만 실행). smoke 테스트가 서버 부재를
  실패로 취급하면 `scripts/qa.sh`가 MariaDB 없는 환경에서 항상 깨져
  Phase C 이후에도 개발 흐름을 막는다. 이는 0481 태스크 노트("DB가 없으면
  skip한다")와 동일한 원칙이다.
- 이 판단 기준은 [0500 DB phase QA checklist](php-db-ui-micro-job-prompts-0351-0670.md)에
  smoke 항목이 편입될 때도 그대로 유지한다 — QA 체크리스트에 포함되더라도
  MariaDB 서버가 없는 실행 환경에서 전체 QA를 실패시키지 않는다.

## 2. 적용 순서

`db/schema/*.sql`은 파일명 알파벳 순서가 아니라 **외래키 의존 순서**로
적용해야 한다. FK가 있는 테이블은 참조 대상 테이블보다 뒤에 와야 한다
([Migration Portability Checklist §3](migration-portability-checklist.md#3-트랜잭션-경계-수작업-확인)의
"DDL은 즉시 커밋되고 롤백되지 않는다" 전제 때문에, 순서가 틀리면 중간
실패 후 수동 정리가 필요하다).

1. `schema_migration.sql` — 의존 없음.
2. `account.sql` — 의존 없음.
3. `document.sql` — 의존 없음(`current_revision_id`는 FK 없이 둔다,
   [db/schema/document.sql](../db/schema/document.sql) 주석 참고).
4. `revision.sql` — `document` 참조.
5. `user_session.sql` — `account` 참조.
6. `acl_rule.sql` — `document` 참조.
7. `acl_namespace_rule.sql` — 의존 없음(namespace는 자유 문자열, FK 없음).
8. `discussion_thread.sql` — `document` 참조.
9. `discussion_comment.sql` — `discussion_thread` 참조.
10. `audit_event.sql` — 의존 없음(다형 참조라 FK 없음).
11. `job.sql` — 의존 없음.

이 순서는 각 `db/schema/*.sql` 파일의 `FOREIGN KEY` 절을 근거로 도출했다
— 새 테이블이 추가되면 이 목록도 함께 갱신한다.

## 3. 단계

1. **접속 확인**: `WIKI_MARIADB_DSN`으로 접속을 시도한다. 실패하면
   §1 규칙대로 skip(테스트 실패 아님)한다.
2. **격리된 대상 스키마 준비**: 기존 데이터베이스를 손상시키지 않도록,
   smoke 전용 데이터베이스/스키마를 새로 만들거나 이미 있으면 비운다.
   운영 DSN을 그대로 재사용해 기존 테이블을 건드리지 않는다.
3. **순서대로 적용**: §2 순서로 각 `.sql` 파일 전체를 그대로 실행한다.
   파일을 가공(치환/파싱)하지 않고 원본을 그대로 실행하는 것이 핵심이다
   — 그래야 "실제로 이식될 파일이 그대로 동작하는가"를 확인하는 smoke의
   목적에 맞는다.
4. **테이블 존재 확인**: 11개 테이블이 모두 생성됐는지 카탈로그 조회로
   확인한다(생성 문이 오류 없이 끝났다는 것과, 실제로 테이블이 존재한다는
   것은 별개로 확인한다).
5. **정리**: smoke 전용 데이터베이스/스키마를 삭제해 반복 실행이 항상
   깨끗한 상태에서 시작하게 한다(§5 참고).

## 4. 실패 판정 기준

smoke 테스트는 세 가지 실패 원인을 구분해 보고한다 — 원인을 구분하지
않으면 "MariaDB에서 스키마가 깨졌다"는 신호가 "서버가 없다"는 신호에
묻힌다.

- **접속 실패** → skip (§1). 테스트 실패로 집계하지 않는다.
- **DDL 적용 실패**(파일 실행 중 SQL 오류) → 실패. 어느 파일, 어느 문에서
  실패했는지 원본 오류 메시지를 그대로 보고한다(0474 duplicate key 정책과
  동일하게, DB별 오류 문자열을 파싱해 분류하지 않는다 — 실행이 성공했는지
  실패했는지만 판단한다).
- **테이블 존재 확인 실패**(적용은 끝났지만 예상한 11개 테이블 중 일부가
  없음) → 실패. `db/schema/README.md`의 파일 목록과 실제 카탈로그 결과의
  차이를 보고한다.

## 5. 반복 실행과 정리

같은 smoke 테스트를 반복 실행해도 이전 실행의 잔여 테이블 때문에 실패하지
않아야 한다 — 대상 스키마를 매 실행 시작 시점에 새로 만들거나 비우고,
종료 시점에도 정리한다(§3의 2, 5단계). 이는 [Migration Portability
Checklist §5](migration-portability-checklist.md#5-순방향재실행-안전성-수작업-확인)의
"같은 마이그레이션을 두 번 실행해도 멱등하다고 가정하지 않는다"는 원칙과
같은 이유다 — smoke 스크립트 스스로가 재실행 안전성을 책임지고, `db/schema`
원본 SQL에 `IF NOT EXISTS` 같은 방어 문법을 추가하지 않는다(원본은 실제
이식 대상 그대로 유지한다).

## 이 문서 이후 단계

- **0481**([Add optional MariaDB test script](php-db-ui-micro-job-prompts-0351-0670.md)):
  이 계획의 §1~§5를 실제 `scripts/` 스크립트로 구현한다. DB가 없으면
  skip한다(§1과 동일한 원칙).
- **0500**([Add DB phase QA checklist](php-db-ui-micro-job-prompts-0351-0670.md)):
  이 smoke 계획을 ANSI lint, PHP PDO skeleton과 함께 DB phase QA
  체크리스트 항목으로 편입한다.
- **0505**([Add portable migration dry-run command](php-db-ui-micro-job-prompts-0351-0670.md)):
  `db/migrations/`가 채워진 뒤, 실제 적용 없이 SQL만 확인하는 dry-run
  명령을 추가한다 — 이 문서의 smoke(실제 적용)와는 달리 비파괴적 확인이
  목표다.
- 실제 CI 연결(스케줄/파이프라인에서 이 smoke를 자동 실행)은 이 태스크의
  범위 밖이며, 위 후속 잡 이후 별도 잡에서 다룬다.

## 관련 문서

- [Migration Portability Checklist](migration-portability-checklist.md) —
  이 smoke가 검증 대상으로 삼는 마이그레이션 작성 규칙의 원출처.
- [db/README.md](../db/README.md), [db/schema/README.md](../db/schema/README.md) —
  smoke 대상 SQL 원본의 위치와 파일 규칙.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 이
  smoke가 전제하는 MariaDB 최소 지원 버전(10.6 LTS).
- [PostgreSQL DSN Compatibility](postgresql-dsn-compatibility.md) — §1이
  기준으로 삼는 `WIKI_MARIADB_DSN` 형식의 원출처.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
