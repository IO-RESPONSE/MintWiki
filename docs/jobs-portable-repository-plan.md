# Jobs Portable Repository Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md), [Portable Schema Naming
Policy](portable-schema-naming-policy.md), [Portable ID Column
Policy](portable-id-column-policy.md), [Portable Timestamp Column
Policy](portable-timestamp-column-policy.md), [Portable Text Collation
Policy](portable-text-collation-policy.md), [Portable Query Builder
Policy](portable-query-builder-policy.md)이 이미 정한 정책을 바탕으로,
`jobs` 모듈(`src/modules/jobs/`)이 소유하기로 되어 있는 "background work
orchestration"([modules.md](modules.md#jobs))가 DB 백엔드로 옮겨갈 때
따를 테이블 설계를 계획한다. [User](user-portable-repository-plan.md)/
[ACL](acl-portable-repository-plan.md)/[Discussion](discussion-portable-repository-plan.md)/
[Audit Portable Repository Plan](audit-portable-repository-plan.md)과 같은
형식을 따르되, 태스크 노트가 명시한 **shared hosting sync runner**를
테이블 설계가 어떻게 수용하는지를 중심 질문으로 삼는다. **이 문서는
계획이며, 새 코드나 마이그레이션을 추가하지 않는다.** 실제 SQL 초안은
[0468](php-db-ui-micro-job-prompts-0351-0670.md)(jobs table portable
SQL)에서, 폴링/락 메커니즘은
[0516](jobs-polling-portable-policy.md)(jobs polling portable
policy)에서, 실제 `Database*Repository` 구현체는 그 이후 태스크에서
작성한다.

## 목적

`src/modules/jobs/`는 지금 `README.md` 한 장뿐이다 — [Audit Portable
Repository Plan §1](audit-portable-repository-plan.md#1-현재-상태-readme만-있고-도메인-모델도-저장소도-없다)이
확인했던 "README만 있고 도메인 모델도 저장소도 없다"는 상태와 같지만,
`jobs`는 그보다도 더 이르다 — audit는 최소한 `AclAuditEvent`/
`DiscussionAuditEvent`라는 실제 도메인 모델이 다른 모듈 안에 이미
존재했지만(그 모델들이 "미래 audit 테이블"의 형태를 암시했다), `jobs`가
암시할 수 있는 도메인 모델은 코드베이스 어디에도 없다. `README.md`가
나열하는 책임(job interface, sync runner, queued backend adapter, retry
metadata, dead-letter handling, job audit records)만이 이 문서가 근거로
삼을 수 있는 유일한 사양이다.

이 책임 목록 중 이 문서가 특히 풀어야 할 질문은 두 가지다.

1. **sync runner와 queued runner가 같은 테이블을 쓸 수 있는가.**
   [PHP job port 태스크(0412)](php-db-ui-micro-job-prompts-0351-0670.md)와
   [shared hosting cron policy 태스크(0653)](php-db-ui-micro-job-prompts-0351-0670.md)가
   이미 "shared hosting sync fallback"을 목표 아키텍처로 예고해 두었다 —
   cron이나 상시 워커 프로세스를 쓸 수 없는 shared hosting 환경에서는
   job이 즉시 동기 실행되고, 워커 프로세스를 둘 수 있는 환경에서는 job이
   큐에 쌓여 폴링된다. 이 두 실행 모델이 스키마 레벨에서 서로 다른
   테이블을 요구하는지, 아니면 하나의 테이블이 상태 값만으로 흡수할 수
   있는지를 §4에서 정한다.
2. **retry metadata와 dead-letter handling을 별도 테이블 없이 표현할 수
   있는가.** `README.md`가 나열한 "retry metadata"와 "dead-letter
   handling"이 각각 별도 테이블을 요구하는 개념인지, 아니면 하나의 job
   행이 상태 전이로 표현할 수 있는 속성인지를 §5에서 정한다.

## 적용 범위

계획 대상:

- `src/modules/jobs/README.md`가 나열한 책임(job interface, sync runner,
  queued backend adapter, retry metadata, dead-letter handling) 중 영속화가
  필요한 부분이 암시하는 테이블 형태.
- sync runner와 queued runner가 하나의 테이블/상태 모델을 공유할 수
  있는지 여부.
- retry metadata(시도 횟수, 다음 실행 가능 시각)와 dead-letter 상태를
  스키마 레벨에서 어떻게 표현할지.
- "job audit records" 책임과 [Audit Portable Repository
  Plan](audit-portable-repository-plan.md#3-audit_event-테이블)이 이미
  `category` 컬럼에 남겨 둔 `"job"` 카테고리 자리 사이의 경계.

계획 대상이 아닌 것(참고로만 다룸):

- 실제 `Database*Repository`/큐 폴링 구현체 — 이 문서 이후 별도 태스크
  (0468, 0516, 번호 미배정 후속 태스크)의 범위다.
- 폴링/락 메커니즘의 구체 SQL(`SELECT ... FOR UPDATE`, `SKIP LOCKED` 대안
  등) — [0516](jobs-polling-portable-policy.md)의 범위다(§7).
- `job` 도메인 모델 자체(파이썬 클래스, enum) — 이 문서는 미래 모델이
  가질 필드를 테이블 컬럼으로 역산할 뿐, 그 모델을 지금 작성하지 않는다.
- Alembic 마이그레이션 자체 — 이 문서 이후 별도 태스크(0468 이후)의
  범위다.

## 1. 현재 상태: README 한 장, 도메인 모델조차 없다

| 대상 | 상태 |
|---|---|
| 도메인 모델(`Job` 등) | 없음 — `src/modules/jobs/`에 파이썬 파일이 하나도 없다 |
| 저장소 인터페이스 | 없음 |
| InMemory 구현 | 없음 |
| Database 구현 | 없음 |
| 사양 | `README.md` 6줄(책임 목록)뿐 |

[Audit Portable Repository Plan §1](audit-portable-repository-plan.md#1-현재-상태-readme만-있고-도메인-모델도-저장소도-없다)이
"audit는 `AclAuditEvent`/`DiscussionAuditEvent`라는 참고할 도메인 모델이
이미 있었다"고 기록한 것과 달리, `jobs`가 참고할 수 있는 도메인 모델은
전무하다. 이 문서의 컬럼 설계(§3)는 따라서 기존 코드가 아니라
`README.md`의 책임 목록과 [modules.md의 jobs
절](modules.md#jobs)에서 직접 역산한다.

## 2. 이름 규칙: 모듈 접두어 없이 `job` 단수형

**핵심 설계: `jobs_job`처럼 접두어를 겹치지 않고, `document`/`revision`과
같은 패턴으로 `job` 단수형 테이블 하나를 둔다.**

[User](user-portable-repository-plan.md#2-예약어-충돌-테이블-이름부터-다시-확인한다)/
[ACL](acl-portable-repository-plan.md#2-이름-규칙-rule-단독-대신-모듈-접두어를-쓴다)/
[Discussion](discussion-portable-repository-plan.md#2-이름-규칙-discussion_thread--discussion_comment)/
[Audit](audit-portable-repository-plan.md#2-이름-규칙-모듈-접두어-테이블-분리-대신-단일-audit_event-테이블)
네 문서 모두 테이블 이름에 소유 모듈 접두어를 붙였다 — 하지만 그 접두어는
"테이블이 담는 개념"과 "그 개념을 소유하는 모듈"이 다른 이름을 가질 때
필요했다(`user` 모듈의 `Session`/`Block`/`Group`, `acl` 모듈의 `Rule`,
`audit` 모듈의 `AuditEvent`). `jobs` 모듈이 담는 개념은 모듈 이름 자체와
같다 — `README.md`가 나열한 책임 전부가 "job" 하나를 중심으로 돈다. 이는
`document`/`revision` 모듈이 각각 `Document`/`Revision`이라는, 모듈
이름과 동일한 단일 개념을 테이블 이름 그대로 쓴 것과 같은 상황이다
([Portable Schema Naming Policy §3](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의
단수형 규칙). 따라서 `jobs_job`처럼 접두어를 겹쳐 쓰지 않고 `job`을
그대로 테이블 이름으로 확정한다 — `job`은 PostgreSQL/MariaDB 예약어
목록([Portable Schema Naming Policy §5](portable-schema-naming-policy.md#5-예약어-회피))에
없는 일반 단어다.

## 3. `Job`(아직 존재하지 않는 도메인 모델) → `job` 테이블

`README.md`의 책임 목록(job interface, sync runner, queued backend
adapter, retry metadata, dead-letter handling)이 암시하는 컬럼을
역산한다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) — [User](user-portable-repository-plan.md)/[ACL](acl-portable-repository-plan.md)/[Discussion](discussion-portable-repository-plan.md)/[Audit](audit-portable-repository-plan.md) 네 문서가 이미 따른 것과 동일하게 애플리케이션이 생성한 UUID 문자열을 PK로 쓴다 |
| `job_type` | `String(255)` | `NOT NULL` | job interface 책임 — 어떤 작업을 실행할지 식별하는 판별 컬럼(예: `"reindex_document"`, `"send_notification"`). [Portable Text Collation Policy §3](portable-text-collation-policy.md#3-대소문자-구분-컬럼-예시-id)과 동일 근거(`utf8mb4_bin`, 고정된 소문자 문자열) |
| `payload` | `Text` | `NULL` 허용 | job 실행에 필요한 인자를 애플리케이션이 직렬화해 저장. [ANSI SQL Persistence Policy의 금지 목록](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)이 `JSONB`/`JSON` 연산자를 금지하고 "필요 시 애플리케이션에서 직렬화한 `TEXT`로 저장하고 조건 검색은 하지 않는다"고 명시한 대안을 그대로 따른다 — `payload` 컬럼에 대한 `WHERE` 조건 검색은 이 설계에서 전제하지 않는다 |
| `status` | `String(20)` | `NOT NULL` | retry metadata + dead-letter handling + sync/queued 구분을 함께 표현하는 상태 컬럼. §4~§5가 값 집합을 정한다 |
| `attempts` | `Integer` | `NOT NULL DEFAULT 0` | retry metadata 책임 — 지금까지 실행을 시도한 횟수 |
| `max_attempts` | `Integer` | `NOT NULL` | retry metadata 책임 — 이 값을 넘으면 §5가 정한 `dead_letter` 상태로 전이 |
| `available_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy §3](portable-timestamp-column-policy.md#3-db-서버-사이드-default-의존-최소화) — queued runner가 폴링할 때 "지금 실행 가능한 job"을 가리는 기준 시각. 재시도 backoff이 있으면 미래 시각, 즉시 실행이면 생성 시각과 동일 |
| `last_error` | `Text` | `NULL` 허용 | retry metadata 책임 — 마지막 실패 원인. dead-letter로 전이된 job을 운영자가 조사할 때 필요 |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) 표준 컬럼 |
| `updated_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) 표준 컬럼 — `job` 행은 상태가 바뀌는 가변 테이블이므로 [Audit Portable Repository Plan §3](audit-portable-repository-plan.md#3-audit_event-테이블)이 `audit_event`에는 두지 않기로 한 `updated_at`을 여기서는 둔다(§6에서 이 차이를 다시 설명한다) |

- `locked_at`/`locked_by`처럼 폴링 클레임(claim)에 필요할 수 있는 컬럼은
  이 문서가 확정하지 않는다 — 락 메커니즘 자체가 §7이 명시적으로
  [0516](jobs-polling-portable-policy.md)에 미루는 질문이라,
  그 결정 전에 컬럼만 먼저 고정하면 실제 폴링 쿼리와 맞지 않을 위험이
  있다.

## 4. Sync/Queued 상태: 두 실행 모델을 같은 테이블이 흡수한다

**핵심 설계: sync runner와 queued runner를 위한 테이블을 따로 두지
않는다. `status` 컬럼 값이 어느 러너가 이 행을 만들었는지를 구분한다.**

- **왜 테이블을 나누지 않는가.** [PHP job port(0412)](php-db-ui-micro-job-prompts-0351-0670.md)/
  [shared hosting cron policy(0653)](php-db-ui-micro-job-prompts-0351-0670.md)가
  예고한 목표는 "shared hosting은 sync fallback이 기본"이다 — 즉 같은
  `job` 개념이 배포 환경에 따라 즉시 실행되거나 큐에 쌓일 뿐, 개념 자체가
  둘로 갈라지지 않는다. 테이블을 나누면 배포 환경이 바뀔 때(예: shared
  hosting에서 워커 프로세스를 쓸 수 있는 환경으로 이전) 마이그레이션으로
  데이터를 옮겨야 하는데, 이는 [Persistence
  Boundaries](persistence-boundaries.md)가 지향하는 "코드 변경 없이
  마이그레이션만으로 대응"하는 확장 지점 원칙과 맞지 않는다.
- **`status` 값 집합.** [0468 태스크 노트](php-db-ui-micro-job-prompts-0351-0670.md)("sync/queued
  상태를 둔다")를 그대로 따라, 아래 값을 후보로 남긴다(최종 확정은
  0468).
  - `sync` — sync runner가 즉시 실행을 시작했다는 표시. shared hosting
    기본 경로에서는 이 상태를 거쳐 같은 요청 안에서 바로 `succeeded`/
    `failed`로 전이한다 — 폴링 대상이 아니다.
  - `queued` — queued runner가 폴링할 대상. `available_at`이 지금 이하인
    행만 후보가 된다.
  - `running` — 워커가 실행을 시작해 클레임한 상태(§3의 락 컬럼 미정과
    맞물린다).
  - `succeeded` / `failed` — 종료 상태.
  - `dead_letter` — §5가 정의하는 재시도 소진 상태.
- **왜 이 흡수가 가능한가.** sync runner 경로에서 `job` 행을 아예 쓰지
  않는 대안(즉시 실행하고 기록을 남기지 않는 방식)도 검토했지만 채택하지
  않는다 — `README.md`의 "job audit records" 책임과 §6이 논의하는
  `audit_event.category="job"` 미래 연동이 성립하려면, sync 경로로 실행된
  job도 최소한 하나의 `job` 행(시작 시각, 종료 상태, 실패 사유)을 남겨야
  운영자가 "무슨 job이 언제 실행됐는지"를 sync/queued 구분 없이 한
  테이블에서 조회할 수 있다.

## 5. Dead-letter handling: 별도 테이블 없이 `status` 전이로 표현한다

**핵심 설계: dead-letter queue를 위한 별도 테이블을 두지 않는다.**
`attempts >= max_attempts`가 된 시점에 같은 `job` 행이 `status`를
`dead_letter`로 전이할 뿐, 행을 다른 테이블로 옮기지 않는다.

- **왜 별도 테이블을 두지 않는가.** 전통적인 큐 시스템은 "실행 대기 큐"와
  "실패 격리 큐"를 물리적으로 분리해 폴링 쿼리가 실패한 job을 다시 집어
  올리지 않게 한다. 이 설계에서는 그 분리를 테이블이 아니라 `status`
  값(§4)과 폴링 쿼리의 `WHERE status = 'queued'` 조건(§7이 미루는 실제
  폴링 SQL의 전제)으로 이미 달성할 수 있다 — `dead_letter` 상태인 행은
  정의상 그 조건에 걸리지 않으므로 별도 테이블이 주는 격리 효과와
  동일하다. 반면 별도 테이블을 두면 `job` 행이 상태 전이 중 테이블을
  옮겨 다녀야 해서, [DB Adapter Contract §2](db-adapter-contract.md#2-최소-동작-집합)가
  최소 동작으로 규정한 단순한 `add`/`fetch_one`/`fetch_all`/`execute`
  조합을 넘어서는 "행 이동" 로직이 저장소 계층에 추가로 필요해진다.
- **재시도 스케줄링과의 관계.** `attempts < max_attempts`인 실패는
  `status`를 `queued`로 되돌리고 `available_at`을 backoff 계산 결과로
  미래로 미룬다(§3) — 이 경로는 dead-letter가 아니다. `dead_letter`는
  `attempts >= max_attempts`에 도달한 이후에만 전이하는 종료 상태다.

## 6. job 실행 이력은 이 테이블이 아니라 `audit_event`의 몫이다

`job` 테이블은 **현재 상태**(지금 이 job이 어떤 상태인지, 몇 번
시도했는지)만 담는 가변 테이블이다 — §3이 `audit_event`와 달리
`updated_at`을 두기로 한 이유가 이것이다. 이는 `document`(현재 상태) vs
`revision`(불변 이력)이 이미 확립한 분리와 같은 구조다.

`README.md`가 나열한 "job audit records" 책임은 이 `job` 테이블이 아니라
[Audit Portable Repository Plan §3](audit-portable-repository-plan.md#3-audit_event-테이블)이
이미 `category` 컬럼에 값 후보로 남겨 둔 `"job"` 카테고리
(`document`/`admin`/`auth`/`job` 중 하나, [Audit Portable Repository Plan
§2](audit-portable-repository-plan.md#2-이름-규칙-모듈-접두어-테이블-분리-대신-단일-audit_event-테이블)가
확정한 단일 `audit_event` 테이블 설계)로 맡긴다 — 상태가 바뀔 때마다("이
job이 언제 queued에서 running으로, running에서 dead_letter로
바뀌었는지") append-only 기록을 남기는 일은 `job` 테이블의 UPDATE가 아니라
`audit_event`에 `category="job"`인 새 행을 추가하는 방식으로 이루어져야
한다. 이 문서는 그 연동을 설계하지 않는다 — `AclAuditEvent`/
`DiscussionAuditEvent`와 마찬가지로 아직 `JobAuditEvent`류 도메인 모델
자체가 존재하지 않기 때문이다(§1). [Audit Portable Repository Plan
§2](audit-portable-repository-plan.md#2-이름-규칙-모듈-접두어-테이블-분리-대신-단일-audit_event-테이블)가
이미 이 미래 연동을 "카테고리가 늘어도 테이블을 새로 만들 필요가 없다"는
근거로 전제해 두었으므로, 이 문서는 그 전제를 재확인만 한다.

## 7. 락/폴링 메커니즘은 0516 정책을 따른다

**핵심 설계: queued runner는 조건부 `UPDATE`의 영향 행 수로 job claim
성공 여부를 판정한다.** [0516 정책 문서](jobs-polling-portable-policy.md)가
이 질문을 확정했다 —
`SELECT ... FOR UPDATE SKIP LOCKED`는 PostgreSQL과 MariaDB 10.6+ 양쪽
모두 문법상 존재하지만, [ANSI SQL Persistence
Policy](ansi-sql-persistence-policy.md)와 [MariaDB Compatibility
Matrix](mariadb-compatibility-matrix.md)가 이미 다루는 "두 DB에서 동일하게
지원되는 기능만 기본으로 쓴다"는 원칙에 비춰 기본 폴링 경로로 전제할 수
없다(구버전 MariaDB, 특히 shared hosting에서 흔한 관리형 MariaDB 배포는
`SKIP LOCKED`를 지원하지 않을 수 있다).

- §3이 `locked_at`/`locked_by` 컬럼을 확정하지 않은 이유가 이것이다 — 락
  컬럼의 구체 형태는 실제 클레임 SQL(낙관적 락으로 `UPDATE ... WHERE
  status='queued' AND id=?`인지, 비관적 락으로 별도 락 컬럼을 두는지)이
  정해진 뒤에야 확정할 수 있다.
- 0516은 기본 구현에서 `SKIP LOCKED`를 제외하고, `status='queued' AND
  available_at <= ?` 조건을 포함한 `UPDATE job ... WHERE id = ?`의 영향 행
  수가 `1`이면 claim 성공, `0`이면 다른 runner가 먼저 claim한 것으로 보는
  정책을 확정했다.

## 8. 인덱스: 지금은 확립된 조회 패턴이 없다는 것부터 인정한다

[Audit Portable Repository Plan
§7](audit-portable-repository-plan.md#7-인덱스-지금은-확립된-조회-패턴이-없다는-것부터-인정한다)과
같은 이유로, 이 절은 인덱스를 확정하지 않는다 — 저장소 인터페이스 자체가
없으므로(§1) 이 문서가 참조할 실제 호출자가 없다.
`README.md`/[modules.md](modules.md#jobs)에 근거한 후보만 제안으로 남긴다:

- `ix_job_status_available_at`(`status`, `available_at`) — §7이 미루는
  폴링 쿼리("지금 실행 가능한 queued job부터")를 가정한 후보.
- `ix_job_job_type`(`job_type`) — "이 종류의 job만" 조회하는 운영 화면을
  가정한 후보.

두 인덱스 모두 실제 `Database*Repository`/폴링 구현 태스크(0516 이후)가
저장소 인터페이스가 실제로 요구하는 조회에 맞춰 추가하거나 뺄지 다시
판단해야 한다 — 이 문서는 이 두 인덱스를 "필요하다"고 확정하지 않는다.

## 9. DB adapter 계약과 쿼리 빌더 정책 적용

미래 `Database*Repository`는 다른 모듈과 동일하게 [DB Adapter
Contract](db-adapter-contract.md)의 최소 동작 집합(`add`/`fetch_one`/
`fetch_all`/`execute`/`commit`/`rollback`)에 기대야 한다 — `audit_event`와
달리 `job`은 상태 전이가 있는 가변 테이블이므로(§6) `execute`(UPDATE 문
실행)가 실제로 필요하다. 모든 statement는 [Portable Query Builder
Policy](portable-query-builder-policy.md)에 따라 SQLAlchemy 쿼리 빌더
표현식으로만 작성해야 한다.

## 이 문서 이후 단계

- **0468**([jobs table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §3이 제안한 `job` 테이블을 실제 SQL 초안으로 옮기고, §4의 `status` 값
  집합을 확정한다. §8이 제안만 하고 확정하지 않은 인덱스도 이 태스크가
  다시 판단한다.
- **0516**([jobs polling portable policy](jobs-polling-portable-policy.md)):
  §7이 미룬 락/폴링 메커니즘(`SKIP LOCKED` 대안 포함)을 확정했다. 기본
  구현은 조건부 `UPDATE`의 영향 행 수로 claim 성공을 판정한다.
- 실제 `Database*Repository`/queued runner 구현체, `job` 도메인 모델
  자체는 0468/0516 이후 별도 태스크(번호 미배정)의 범위다.
- `audit_event.category="job"` 연동(§6)은 audit 모듈과 jobs 모듈 양쪽의
  후속 태스크가 함께 설계해야 한다 — 이 문서는 그 연동이 가능하다는
  것만 확인한다.

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — Database* 구현체가
  공통으로 만족해야 하는 최소 계약(§9의 근거).
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) —
  단일 테이블 이름 확정(§2)과 예약어 회피 근거.
- [Portable ID Column Policy](portable-id-column-policy.md) — `id`
  컬럼의 타입/생성 방식(§3).
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  `available_at`/`created_at`/`updated_at` 컬럼의 타입 원칙(§3).
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  `job_type`/`status` 문자열 컬럼의 collation 근거(§3).
- [Portable Query Builder Policy](portable-query-builder-policy.md) —
  미래 구현체가 지켜야 할 statement 작성 방식(§9).
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) —
  `payload` 컬럼에 `JSON`/`JSONB`를 쓰지 않는 근거(§3).
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) —
  `SKIP LOCKED` 같은 DB별 폴링 기능을 기본에서 제외하는 근거(§7).
- [Jobs Polling Portable Policy](jobs-polling-portable-policy.md) —
  0516에서 확정한 portable polling/claim 정책(§7).
- [Persistence Boundaries](persistence-boundaries.md) — 배포 환경 전환을
  코드 변경 없이 마이그레이션만으로 흡수한다는 확장 지점 원칙(§4)의
  원출처.
- [User Portable Repository Plan](user-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0454).
- [ACL Portable Repository Plan](acl-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0455).
- [Discussion Portable Repository Plan](discussion-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0456), `status` 컬럼에 `CHECK`를 걸지 않는
  판단 근거(§3)의 원출처.
- [Audit Portable Repository Plan](audit-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0457), 단일 `audit_event` 테이블과 `category`
  판별 컬럼 설계(§6이 참조), 도메인 모델 없이 계획만 먼저 쓰는 선례(§1).
- [modules.md](modules.md#jobs) — `jobs` 모듈의 책임 범위 원출처(§목적,
  §3).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체, 이 문서가 참조하는 0412/0457/0468/0516/0653의
  출처.
