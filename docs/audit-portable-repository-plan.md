# Audit Portable Repository Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md), [Portable Schema Naming
Policy](portable-schema-naming-policy.md), [Portable ID Column
Policy](portable-id-column-policy.md), [Portable Timestamp Column
Policy](portable-timestamp-column-policy.md), [Portable Text Collation
Policy](portable-text-collation-policy.md), [Portable Query Builder
Policy](portable-query-builder-policy.md)이 이미 정한 정책을 바탕으로,
`audit` 모듈(`src/modules/audit/`)이 소유하기로 되어 있는 "immutable
event logs"([modules.md](modules.md#audit))가 DB 백엔드로 옮겨갈 때 따를
테이블 설계를 계획한다. [User Portable Repository
Plan](user-portable-repository-plan.md)(0454), [ACL Portable Repository
Plan](acl-portable-repository-plan.md)(0455), [Discussion Portable
Repository Plan](discussion-portable-repository-plan.md)(0456)과 짝을
이루며, 두 문서 모두 자신이 다루는 감사 이벤트(`AclAuditEvent`,
`DiscussionAuditEvent`)의 저장소 설계를 이 문서(0457)로 명시적으로
미뤄 두었다. **이 문서는 계획이며, 새 코드나 마이그레이션을 추가하지
않는다.** 실제 SQL 초안은
[0467](php-db-ui-micro-job-prompts-0351-0670.md)(audit table portable
SQL)에서, 실제 `Database*Repository`/audit 서비스 구현체는 그 이후
태스크에서 작성한다.

## 목적

`src/modules/audit/`는 지금 `README.md` 한 장뿐이다 — [ACL Portable
Repository Plan §1](acl-portable-repository-plan.md#1-현재-상태-저장소-인터페이스조차-없다)이
확인했던 "저장소 인터페이스조차 없다"보다도 이전 단계로, 도메인 모델도
저장소 포트도 InMemory 구현체도 전혀 없다. 반면 실제 감사 이벤트
도메인 모델은 이미 두 개 존재한다 — `AclAuditEvent`/`AclAuditRecorder`
(`src/modules/acl/audit_event.py`, `audit_recorder.py`)와
`DiscussionAuditEvent`/`DiscussionAuditRecorder`
(`src/modules/discussion/audit_event.py`, `audit_recorder.py`)다. 둘 다
`audit` 모듈이 아니라 각자 소속 모듈 안에 있고, 각 `*Recorder`는 이벤트를
파이썬 리스트(`self._events`)에 누적할 뿐 어디에도 영속화하지 않으며,
서로 다른 두 모듈 사이에 어떤 공유 코드도 없다.

[modules.md의 audit 절](modules.md#audit)은 이 상태가 임시라고 이미
선언해 두었다 — "Audit records should be written by modules through a
small audit service"라는 목표 아키텍처를 명시하고, `document
logs`/`permission change logs`/`admin action logs`/`auth logs`/`job
logs`를 모두 `audit` 모듈이 소유해야 한다고 적어 두었다.
[Dependency Rules](modules.md#dependency-rules)도 `acl`/`discussion`이
`audit`를 호출할 수 있다고 이미 선언했지만, 지금 코드는 그 호출을 하지
않는다 — `AclAuditRecorder`/`DiscussionAuditRecorder`는 `audit` 모듈을
import조차 하지 않는다. 이 문서는 그 목표 아키텍처가 실제 저장소로
구체화될 때 풀어야 할 두 질문에 먼저 답한다.

1. **통합 저장이냐 모듈별 저장이냐.** `AclAuditEvent`(`rule_id` 필수 +
   `document_id` 선택)와 `DiscussionAuditEvent`(`thread_id` 필수 +
   `comment_id` 선택)는 필드 구성이 서로 다르다. `acl_audit_event`/
   `discussion_audit_event`처럼 [User](user-portable-repository-plan.md)/
   [ACL](acl-portable-repository-plan.md)/[Discussion Portable Repository
   Plan](discussion-portable-repository-plan.md)이 써 온 모듈 접두어
   테이블 분리 패턴을 그대로 반복할지, 아니면 `audit` 모듈이 소유하는
   단일 테이블로 통합할지를 §2에서 정한다.
2. **append-only를 스키마가 어떻게 표현하는가.** 태스크 노트가 요구하는
   "append-only, partition 없는 기본 설계"를 §5~§6에서 구체화한다 —
   append-only가 스키마 레벨에서 실제로 무엇을 의미/보장하고 무엇은
   보장하지 못하는지, 그리고 지금 파티셔닝을 하지 않는 근거를 명시한다.

## 적용 범위

계획 대상:

- `src/modules/acl/audit_event.py`(`AclAuditEvent`)가 암시하는 미래
  저장 형태.
- `src/modules/discussion/audit_event.py`(`DiscussionAuditEvent`)가
  암시하는 미래 저장 형태.
- 위 두 이벤트를 하나의 저장소 설계로 통합할지 여부와, 통합한다면 그
  테이블 스키마.
- append-only 보장과 파티셔닝 유예를 스키마 레벨에서 어떻게 표현할지.

계획 대상이 아닌 것(참고로만 다룸):

- 실제 `Database*Repository`/`AuditService` 구현체, `AclAuditRecorder`/
  `DiscussionAuditRecorder`가 그 서비스를 호출하도록 바꾸는 리팩터 — 이
  문서 이후 별도 태스크(0467, 번호 미배정 후속 태스크)의 범위다.
- [modules.md](modules.md#audit)가 언급하는 `document logs`/`admin
  action logs`/`auth logs`/`job logs`의 구체 도메인 모델 — 지금
  코드베이스 어디에도 이 네 종류의 `*AuditEvent` 클래스가 존재하지
  않는다. 이 문서는 이들이 나중에 추가될 것을 전제로 테이블을 일반화해
  두되(§3), 그 도메인 모델 자체를 설계하지 않는다.
- `document`/`acl_rule`/`discussion_thread`/`discussion_comment` 테이블
  자체 — 다형 참조 대상으로서만 언급한다(§4).
- Alembic 마이그레이션 자체 — 이 문서 이후 별도 태스크(0467 이후)의
  범위다.

## 1. 현재 상태: README만 있고 도메인 모델도 저장소도 없다

| 도메인 모델 | 소속 모듈 | 저장소 인터페이스 | 현재 저장 방식 | Database 구현 |
|---|---|---|---|---|
| `AclAuditEvent` | `acl`(`audit_event.py`) | 없음 | `AclAuditRecorder._events`(리스트, 프로세스 메모리) | 없음 |
| `DiscussionAuditEvent` | `discussion`(`audit_event.py`) | 없음 | `DiscussionAuditRecorder._events`(리스트, 프로세스 메모리) | 없음 |
| (document/admin/auth/job logs) | 미배정 | 없음 | 없음(도메인 모델 자체가 없음) | 없음 |

`audit` 모듈 자체는 `README.md` 한 장 외에 파이썬 파일이 하나도 없다.
[ACL Portable Repository Plan §1](acl-portable-repository-plan.md#1-현재-상태-저장소-인터페이스조차-없다)이
"저장소 인터페이스조차 없다"고 표현했던 `acl`/`Rule`보다도 이전 단계다 —
`Rule`은 최소한 도메인 모델(`rule.py`)이 소속 모듈 안에 있었지만, `audit`는
소속될 도메인 모델도 아직 없고, `AclAuditEvent`/`DiscussionAuditEvent`는
이미 존재하되 `audit`가 아니라 각자 원래 모듈에 머물러 있다.

## 2. 이름 규칙: 모듈 접두어 테이블 분리 대신 단일 `audit_event` 테이블

**핵심 설계: `acl_audit_event`/`discussion_audit_event`로 나누지 않고,
`audit` 모듈이 소유하는 단일 `audit_event` 테이블에 두 이벤트를 함께
저장한다.**

- **왜 지금까지의 접두어 분리 패턴과 다른가.** [User](user-portable-repository-plan.md#2-예약어-충돌-테이블-이름부터-다시-확인한다)/
  [ACL](acl-portable-repository-plan.md#2-이름-규칙-rule-단독-대신-모듈-접두어를-쓴다)/
  [Discussion Portable Repository Plan](discussion-portable-repository-plan.md#2-이름-규칙-discussion_thread--discussion_comment)이
  써 온 "테이블 이름에 모듈 접두어를 남긴다"는 규칙은, 그 테이블을
  **소유하는 모듈**이 곧 그 도메인 모델이 원래 속한 모듈이었기 때문에
  성립했다(`user_session`은 `user` 모듈이 소유, `acl_rule`은 `acl`
  모듈이 소유). 감사 이벤트는 다르다 — [modules.md](modules.md#audit)가
  이미 "감사 로그의 소유자는 `audit` 모듈"이라고 선언했고, `AclAuditEvent`/
  `DiscussionAuditEvent`가 지금 `acl`/`discussion` 안에 있는 것은
  아키텍처 목표가 아니라 그 목표가 아직 구현되지 않은 현재 상태다. 이
  문서는 이 아키텍처 목표를 그대로 따라 테이블 소유자를 `acl`/
  `discussion`이 아니라 `audit`로 둔다.
- **왜 모듈별로 나누지 않고 하나로 합치는가.** [modules.md](modules.md#audit)가
  나열한 다섯 카테고리(document/permission/admin/auth/job logs)는 앞으로
  계속 늘어날 수 있는 목록이다. `acl_audit_event`/`discussion_audit_event`
  패턴을 그대로 따르면 카테고리가 하나 늘 때마다 테이블도 하나씩
  늘어나고, "전체 감사 로그를 시간순으로 훑어보기" 같은 감사 로그 본연의
  조회(운영자가 무슨 일이 있었는지 확인하는 화면)가 여러 테이블에 걸친
  `UNION`을 요구하게 된다. `AclAuditEvent`/`DiscussionAuditEvent`는
  이미 `id`/`action`/`occurred_at`/`actor_id`라는 공통 뼈대를 공유하고
  차이는 "무엇을 참조하는가"(`rule_id`+`document_id` vs
  `thread_id`+`comment_id`)뿐이므로(§3), 그 차이를 다형 참조 컬럼 두
  개(§4)로 흡수하면 카테고리가 늘어도 테이블을 새로 만들 필요가 없다.
  [ACL Portable Repository Plan §4](acl-portable-repository-plan.md#4-rule네임스페이스-기본값--acl_namespace_rule-테이블)가
  `acl_rule`/`acl_namespace_rule`을 굳이 분리한 이유("두 컨텍스트의 키
  컬럼 성격이 다르다")와 정반대 상황이다 — 여기서는 컬럼 성격이 이미
  공통 뼈대로 수렴하므로 분리할 이유가 없다.
- **이름.** [Portable Schema Naming Policy §3](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의
  단수형 규칙에 따라 `audit_event`로 확정한다. `event`는 §5의 예약어
  회피 표에 없는 일반 단어이고, `audit_` 접두어가 이미 [ACL](acl-portable-repository-plan.md#2-이름-규칙-rule-단독-대신-모듈-접두어를-쓴다)/
  [Discussion](discussion-portable-repository-plan.md#2-이름-규칙-discussion_thread--discussion_comment)
  두 문서가 확립한 "테이블 이름에 소유 모듈을 남긴다" 관례를 그대로
  따른다.

## 3. `audit_event` 테이블

`AclAuditEvent`(`id`, `action`, `rule_id`, `occurred_at`, `document_id`
선택, `actor_id` 선택)와 `DiscussionAuditEvent`(`id`, `action`,
`thread_id`, `occurred_at`, `comment_id` 선택, `actor_id` 선택) 두
모델을 하나의 컬럼 집합으로 흡수한다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) — `AclAuditRecorder`/`DiscussionAuditRecorder`가 이미 `str(uuid.uuid4())`로 이벤트 자신의 `id`를 생성한다(`audit_recorder.py` 양쪽 모두). 이 값을 그대로 행의 PK로 쓴다 — 별도 합성 키를 두지 않는다 |
| `category` | `String(20)` | `NOT NULL` | 이벤트가 어느 소스에서 왔는지 구분하는 판별 컬럼. 지금은 `"acl"`(`AclAuditEvent` 유래)/`"discussion"`(`DiscussionAuditEvent` 유래) 두 값만 실재하며, [modules.md](modules.md#audit)가 예고한 `document`/`admin`/`auth`/`job` 카테고리가 나중에 추가될 여지를 남겨 둔다. [Portable Text Collation Policy §3](portable-text-collation-policy.md#3-대소문자-구분-컬럼-예시-id)와 동일 근거(`utf8mb4_bin`, 고정된 소문자 문자열) |
| `action` | `String(50)` | `NOT NULL` | `AclAuditAction`(`rule_added`/`rule_removed`)과 `DiscussionAuditAction`(`thread_created`/`thread_closed`/`thread_reopened`/`thread_paused`/`comment_added`/`comment_hidden`) enum 값을 문자열로 저장 — 두 enum이 같은 컬럼을 공유하지만 `category`가 이미 네임스페이스를 분리하므로 값 충돌 걱정은 없다. 길이는 현재 가장 긴 값(`comment_hidden`, 14자)보다 여유를 두어 미래 admin/auth/job 액션 이름을 수용한다 |
| `entity_id` | `String(255)` | `NOT NULL` | 이벤트가 무엇에 대한 변경인지를 가리키는 필수 참조. `category="acl"`일 때 `AclAuditEvent.rule_id`, `category="discussion"`일 때 `DiscussionAuditEvent.thread_id` — 두 모델 모두에서 필수 필드([`MissingRuleIdError`](../src/modules/acl/audit_event.py)/[`MissingDiscussionThreadIdError`](../src/modules/discussion/audit_event.py)가 이미 빈 값을 거부) |
| `related_entity_id` | `String(255)` | `NULL` 허용 | 부가 참조. `category="acl"`일 때 `AclAuditEvent.document_id`, `category="discussion"`일 때 `DiscussionAuditEvent.comment_id` — 두 모델 모두에서 선택 필드(`Optional[str] = None`) |
| `actor_id` | `String(255)` | `NULL` 허용 | `AclAuditEvent.actor_id`/`DiscussionAuditEvent.actor_id` 그대로. §4처럼 FK 없음(`revision.author_id` 선례와 동일 근거 — [User Portable Repository Plan](user-portable-repository-plan.md#1-현재-상태-inmemory조차-없는-것도-있다)이 확인했듯 계정 테이블 자체가 아직 없다) |
| `occurred_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy §3](portable-timestamp-column-policy.md#3-db-서버-사이드-default-의존-최소화) — 두 `*Recorder`가 이미 `datetime.now(timezone.utc)`로 채운다 |

- `updated_at` 컬럼을 두지 않는다 — §5가 다루는 append-only 설계의
  일부다.

## 4. 다형 참조: `entity_id`/`related_entity_id`에는 FK를 걸지 않는다

`entity_id`는 `category`에 따라 `acl_rule.id`([ACL Portable Repository
Plan §3](acl-portable-repository-plan.md#3-rule문서-범위--acl_rule-테이블))를
가리키기도 하고 `discussion_thread.id`([Discussion Portable Repository
Plan §3](discussion-portable-repository-plan.md#3-discussionthread--discussion_thread-테이블))를
가리키기도 한다 — 하나의 컬럼이 카테고리에 따라 서로 다른 테이블을
참조하는 다형 참조다. `related_entity_id` 역시 `document.id`나
`discussion_comment.id`를 가리킬 수 있어 마찬가지다.

이는 [Persistence Boundaries](persistence-boundaries.md)가 이미
확립하고 [ACL Portable Repository Plan §3](acl-portable-repository-plan.md#3-rule문서-범위--acl_rule-테이블)이
`acl_rule.subject_id`(`USER`일 때 `account.id`, `GROUP`일 때
`user_group.id`)에 적용한 패턴과 동일하다 — 참조 대상이 컬럼 하나로
갈리는 다형 참조는 FK 제약을 걸지 않고, 무결성 검증은 서비스 계층(미래
audit 서비스)의 책임으로 남긴다. `entity_id`/`related_entity_id`도 같은
이유로 FK를 걸지 않는다.

- 감사 로그라는 성격도 이 결정을 강화한다 — 감사 이벤트는 "무슨 일이
  있었는지"의 기록이므로, 참조 대상 행이 나중에 삭제되더라도(예:
  `acl_rule` 행 자체는 `RULE_REMOVED` 이후 삭제될 수 있다) 그 사실을
  기록한 이벤트 행은 남아 있어야 한다. FK를 걸면 참조 대상 삭제 시
  `ON DELETE` 정책을 정해야 하는 문제가 추가로 생기는데, 이는 감사
  로그의 "일어난 일은 지우지 않는다"는 목적과 어긋난다 — FK를 아예
  걸지 않는 것이 이 목적과도 더 맞는다.

## 5. Append-only 보장: 스키마가 표현할 수 있는 것과 없는 것

**핵심 설계: 이 문서는 "append-only"를 스키마가 강제하는 제약이 아니라,
스키마가 UPDATE/DELETE 경로를 아예 필요로 하지 않도록 설계하는 것으로
해석한다.**

- `updated_at` 컬럼을 두지 않는다(§3) — 감사 이벤트는 생성된 뒤 내용이
  바뀔 이유가 없으므로, "언제 마지막으로 수정됐는가"를 추적할 컬럼
  자체가 불필요하다.
- [DB Adapter Contract §2](db-adapter-contract.md#2-최소-동작-집합)가
  정의한 최소 동작 집합(`add`/`fetch_one`/`fetch_all`/`execute`/
  `commit`/`rollback`) 중, 미래 `Database*Repository`는 `add`와
  `fetch_one`/`fetch_all`만 사용한다 — `execute`(UPDATE/DELETE 문
  실행)를 요구하는 조작이 이 모듈에는 없다. `document`/`revision`처럼
  `update` 계열 메서드를 저장소 인터페이스에 두지 않는 것이 이 문서가
  제안하는 audit 저장소 계약의 일부다.
- **이 문서가 보장하지 못하는 것.** ANSI SQL만으로는 "이 테이블에는
  UPDATE/DELETE를 실행할 수 없다"를 강제할 수 없다 — 그런 강제는
  트리거나 DB 권한(GRANT/REVOKE) 같은 DB별 기능에 의존하는데,
  [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)와
  [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)가
  이미 다루는 이식성 범위를 벗어난다. 따라서 append-only는 이 문서
  에서는 **애플리케이션이 UPDATE/DELETE 경로를 아예 만들지 않는다**는
  약속으로 존재하고, DB 레벨 강제(권한 분리 등)가 필요한지는 실제
  운영 설계 태스크(번호 미배정)가 별도로 판단한다.

## 6. 파티셔닝은 지금 하지 않는다

태스크 노트의 "partition 없는 기본 설계"를 그대로 확정한다.
[Persistence Boundaries의 Partitioning
절](persistence-boundaries.md#partitioning)이 이미 "테이블 성장이
파티셔닝을 요구하게 되면" 코드 변경 없이 마이그레이션만으로 대응할 수
있는 확장 지점으로 파티셔닝을 남겨 두었다 — 이 문서는 그 확장 지점을
지금 앞당겨 쓰지 않는다.

- **왜 지금 안 하는가.** `audit_event` 테이블은 아직 한 행도 존재하지
  않는다(§1) — 실제 트래픽도, 실제 행 수 증가율도 없는 상태에서
  파티션 키를 먼저 고르면 그 선택이 실제 조회 패턴과 맞지 않을 위험이
  있다. [User Portable Repository Plan §5](user-portable-repository-plan.md#5-group멤버십--user_group--user_group_member-테이블)/
  [Discussion Portable Repository Plan §6](discussion-portable-repository-plan.md#6-state-status는-지금-free-string으로-남기고-check는-걸지-않는다)이
  이미 따른 원칙("아직 근거가 없는 제약/설계를 먼저 걸지 않는다")을
  그대로 적용한다.
  - 미래 파티셔닝이 필요해지면 `occurred_at`(시계열 성장,
    [Persistence Boundaries](persistence-boundaries.md#partitioning)가
    `revision` 테이블에 든 예시와 동일한 성격) 또는 `category`(카테고리별
    운영 조회가 서로 독립적이라는 성격)가 가장 먼저 검토할 후보라는
    점만 남겨 둔다 — 이 문서가 그 중 하나를 확정하지는 않는다.

## 7. 인덱스: 지금은 확립된 조회 패턴이 없다는 것부터 인정한다

[ACL Portable Repository Plan §5](acl-portable-repository-plan.md#5-규칙-우선순위-재현-sort_order와-인덱스)/
[Discussion Portable Repository Plan §5](discussion-portable-repository-plan.md#5-페이지네이션-결정성-limitoffset은-tie-break-컬럼이-필요하다)의
인덱스 설계는 각각 실제 호출자(`AclService.check()`, `router.py`의
`limit`/`offset` 페이지네이션)가 이미 존재하는 조회 패턴에 근거했다.
`audit`는 다르다 — `AclAuditRecorder.events()`/
`DiscussionAuditRecorder.events()`(둘 다 `test_events_returns_copy_not_internal_list`
류 테스트로 검증됨)는 필터 없이 누적된 이벤트 전체를 시간순으로
반환할 뿐, "특정 카테고리만", "특정 entity_id만" 같은 조회를 요구하는
코드가 지금 어디에도 없다. 저장소 인터페이스 자체가 없으므로(§1)
이 문서가 참조할 실제 호출자가 없다.

**따라서 이 절은 인덱스를 확정하지 않고, [modules.md](modules.md#audit)가
명시한 audit 모듈의 목적(운영자가 감사 로그를 카테고리별/대상별로
확인)에 근거한 후보만 제안으로 남긴다:**

- `ix_audit_event_category_occurred_at`(`category`, `occurred_at`) —
  "이 카테고리의 최근 이벤트부터" 조회를 가정한 후보.
- `ix_audit_event_entity_id`(`entity_id`) — "이 규칙/스레드에 어떤
  변경이 있었는지" 조회를 가정한 후보.

두 인덱스 모두 실제 `Database*Repository`/audit 서비스 구현 태스크가
저장소 인터페이스(어떤 메서드가 필요한지)를 먼저 정한 뒤, 그 인터페이스가
실제로 요구하는 조회에 맞춰 추가하거나 뺄지 다시 판단해야 한다 — [ACL
Portable Repository Plan §5](acl-portable-repository-plan.md#5-규칙-우선순위-재현-sort_order와-인덱스)/
[Discussion Portable Repository Plan §5](discussion-portable-repository-plan.md#5-페이지네이션-결정성-limitoffset은-tie-break-컬럼이-필요하다)와
달리, 이 문서는 이 두 인덱스를 "필요하다"고 확정하지 않는다.

## 8. DB adapter 계약과 쿼리 빌더 정책 적용

미래 `Database*Repository`(또는 audit 서비스가 내부적으로 쓸 저장소)는
다른 모듈과 동일하게 [DB Adapter Contract](db-adapter-contract.md)의
최소 동작 집합 중 §5가 확인한 부분집합(`add`/`fetch_one`/`fetch_all`/
`commit`/`rollback`)만 어댑터에 기대야 하고, 모든 statement는 [Portable
Query Builder Policy](portable-query-builder-policy.md)에 따라
SQLAlchemy 쿼리 빌더 표현식으로만 작성해야 한다.

## 이 문서 이후 단계

- **0467**([audit table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §3이 제안한 `audit_event` 테이블을 실제 SQL 초안으로 옮긴다. §7이
  제안만 하고 확정하지 않은 인덱스도 이 태스크가 실제 저장소 인터페이스
  설계와 함께 다시 판단한다.
- 실제 `Database*Repository`/audit 서비스 구현체는 0467 이후 별도
  태스크(번호 미배정)의 범위다 — 그 태스크가 `AclAuditRecorder`/
  `DiscussionAuditRecorder`를 audit 서비스 호출로 바꿀지, 아니면 각
  모듈이 계속 자체적으로 이벤트를 만들고 audit 모듈은 저장만 담당할지도
  함께 정해야 한다.
- `document`/`admin`/`auth`/`job` 카테고리의 구체 도메인 모델과 그
  `*Recorder`는 각 소유 모듈([modules.md](modules.md))의 후속 태스크
  범위다 — 이 문서는 그 모델들이 §3의 `audit_event` 테이블에 `category`
  값만 추가해 수용될 수 있도록 컬럼을 일반화해 두었을 뿐이다.

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — Database* 구현체가
  공통으로 만족해야 하는 최소 계약(§5, §8의 근거).
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) —
  단일 테이블 이름 확정(§2)과 예약어 회피 근거.
- [Portable ID Column Policy](portable-id-column-policy.md) — `id`
  컬럼의 타입/생성 방식(§3).
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  `occurred_at` 컬럼의 타입 원칙(§3).
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  `category`/`action` 문자열 컬럼의 collation 근거(§3).
- [Portable Query Builder Policy](portable-query-builder-policy.md) —
  미래 구현체가 지켜야 할 statement 작성 방식(§8).
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) —
  append-only를 DB 권한/트리거로 강제하는 방식이 이식성 범위 밖임을
  확인하는 근거(§5).
- [Persistence Boundaries](persistence-boundaries.md) — 다형 참조를 FK
  없이 서비스 계층에서 검증하는 기존 패턴(§4)과 파티셔닝 확장 지점의
  원출처(§6).
- [User Portable Repository Plan](user-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0454), "근거 없는 제약을 먼저 걸지 않는다"는
  원칙의 원출처(§6).
- [ACL Portable Repository Plan](acl-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0455), `AclAuditEvent` 저장소 설계를 이
  문서로 명시적으로 넘긴 원출처, 다형 참조(`subject_id`) 패턴의 선례(§4).
- [Discussion Portable Repository Plan](discussion-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0456), `DiscussionAuditEvent` 저장소 설계를
  이 문서로 명시적으로 넘긴 원출처.
- [modules.md](modules.md#audit) — `audit` 모듈의 책임 범위와 목표
  아키텍처("Audit records should be written by modules through a small
  audit service")의 원출처(§목적, §2).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체, 이 문서가 참조하는 0454/0455/0456/0467의 출처.
