# Discussion Portable Repository Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md), [Portable Schema Naming
Policy](portable-schema-naming-policy.md), [Portable ID Column
Policy](portable-id-column-policy.md), [Portable Timestamp Column
Policy](portable-timestamp-column-policy.md), [Portable Text Collation
Policy](portable-text-collation-policy.md), [Portable Query Builder
Policy](portable-query-builder-policy.md)이 이미 정한 정책을 바탕으로,
`discussion` 모듈(`src/modules/discussion/`)의 스레드/댓글 저장소가 DB
백엔드로 옮겨갈 때 따를 테이블 설계를 계획한다. [User Portable Repository
Plan](user-portable-repository-plan.md)(0454), [ACL Portable Repository
Plan](acl-portable-repository-plan.md)(0455)과 짝을 이루며, `discussion`
모듈 역시 아직 Database* 구현체도 Alembic 마이그레이션도 없다. **이 문서는
계획이며, 새 코드나 마이그레이션을 추가하지 않는다.** 실제 SQL 초안은
[0466](php-db-ui-micro-job-prompts-0351-0670.md)(discussion table portable
SQL)에서, 실제 `Database*Repository` 구현체는 그 이후 태스크에서 작성한다.

## 목적

`src/modules/discussion/`는 `DiscussionRepository`(ABC) 인터페이스와
`InMemoryDiscussionRepository` 구현체만 가지고 있고, Database 구현체와
Alembic 마이그레이션이 아직 없다는 점은 `user`/`acl` 모듈과 같은 상태다.
다만 이 모듈에는 다른 두 모듈에 없던 두 가지 새 요소가 있고, 이 문서는 그
둘을 확정하는 데 집중한다.

1. **페이지네이션.** `DiscussionRepository.list_threads_by_document_id`/
   `list_comments_by_thread_id`(`repository.py`)는 `limit`/`offset`
   파라미터를 받는다(`router.py`가 이를 그대로 `Query(default=None,
   ge=1)`/`Query(default=0, ge=0)`로 HTTP에 노출한다). `document`/`revision`/
   `user`/`acl` 어느 저장소 인터페이스에도 `limit`/`offset`이 없다 —
   `RevisionRepository.list_by_document_id`조차 정렬만 하고 페이지 분할은
   하지 않는다. `discussion`이 이 코드베이스에서 처음으로 페이지네이션을
   요구하는 저장소이므로, "정렬 기준 컬럼에 동시각(tie)이 있으면
   `LIMIT`/`OFFSET`이 페이지 경계에서 행을 중복 반환하거나 아예 누락시킬 수
   있다"는, 정렬만 하는 조회에는 없던 위험을 이 문서가 처음으로 다뤄야 한다
   (§5).
2. **State.** `DiscussionThread.status`(`thread.py`)는 `ThreadState`
   enum(`state.py`)이 정의하는 `open`/`closed`/`paused` 세 값을 의도하지만,
   `DiscussionThread.__init__`은 이 값을 검증하지 않는다 — `discussion/
   README.md`의 "State" 섹션이 이미 "an arbitrary string is not rejected"라고
   이 간극을 지적하고 있다. 이 문서는 `status` 컬럼을 DB로 옮길 때 이
   간극을 스키마 레벨에서 메울지(CHECK 제약) 여부를 판단한다(§6).

`discussion/README.md`의 "Discussion Migration Planning Note" 절이 이미
`discussion_thread`/`discussion_comment` 테이블과 대략적인 컬럼 목록을
스케치해 두었다 — 이 문서는 그 스케치를 이 Phase가 이미 확정한 portable
정책(naming/id/timestamp/collation/query builder) 위에서 다시 검토하고,
그 스케치가 다루지 않은 페이지네이션/state 결정을 채워 넣는다.

## 적용 범위

계획 대상:

- `src/modules/discussion/thread.py`(`DiscussionThread`)가 암시하는 미래
  테이블.
- `src/modules/discussion/comment.py`(`DiscussionComment`)가 암시하는 미래
  테이블.
- 두 테이블에 대한 `list_threads_by_document_id`/`list_comments_by_thread_id`
  (`repository.py`)의 `limit`/`offset` 페이지네이션 결정성.
- `DiscussionThread.status`(`thread.py`)/`ThreadState`(`state.py`) 값을
  스키마에 반영하는 방식.

계획 대상이 아닌 것(참고로만 다룸):

- `DiscussionAuditEvent`/`DiscussionAuditRecorder`(`audit_event.py`,
  `audit_recorder.py`)의 저장소 설계 — [DB Adapter
  Contract](db-adapter-contract.md#이-문서-이후-단계)가 이미 "0456-0458:
  discussion/audit/jobs 각 모듈의 저장소 portability 계획"을 서로 다른
  문서로 구분해 두었고, `discussion/README.md`의 "Sequencing relative to
  existing gaps" 절이 지적하듯 close/reopen/pause가 아직 감사 이벤트를
  남기지 않는 상태에서 감사 로그 테이블을 먼저 확정하면 스키마가 완전하지
  않은 감사 트레일을 전제하게 된다 — [ACL Portable Repository
  Plan](acl-portable-repository-plan.md#적용-범위)이 `AclAuditEvent` 저장소
  설계를 같은 이유로 [0457 audit portable repository
  plan](php-db-ui-micro-job-prompts-0351-0670.md)에 넘긴 것과 동일하게, 이
  문서도 `DiscussionAuditEvent` 저장소 설계를 0457/그 이후 태스크로 넘긴다.
- `DiscussionRecentActivity`(`recent_activity.py`,
  `recent_activity_service.py`) — 저장소 자체가 없다. `from_audit_event()`가
  보여주듯 `DiscussionAuditEvent`로부터 파생되는 읽기 전용 표현 모델이므로,
  저장소 설계는 위 감사 이벤트 저장소 설계에 종속된다.
- `document` 테이블 자체 — FK 대상으로서만 참조한다.
- Database* 구현체 코드, Alembic 마이그레이션 자체 — 이 문서 이후 별도
  태스크(0466, 번호 미배정 후속 태스크)의 범위다.

## 1. 현재 상태: InMemory만 있고 Database 구현은 없다

| 도메인 모델 | 저장소 인터페이스 | 현재 저장 방식 | Database 구현 |
|---|---|---|---|
| `DiscussionThread` | `DiscussionRepository`(`create_thread`/`get_thread`/`list_threads_by_document_id`/`update_thread`) | `InMemoryDiscussionRepository.threads`(dict) + `document_threads`(dict[str, list[str]]) | 없음 |
| `DiscussionComment` | `DiscussionRepository`(`create_comment`/`list_comments_by_thread_id`/`get_comment`/`update_comment`) | `InMemoryDiscussionRepository.comments`(dict) + `thread_comments`(dict[str, list[str]]) | 없음 |

`document`/`revision`과 달리 `discussion`은 아직 SQL을 한 줄도 실행하지
않는다 — 아래 각 절의 제안은 전부 미래 상태에 대한 계획이다.
`InMemoryDiscussionRepository`가 이미 `list[offset:offset+limit]` 형태로
페이지네이션을 구현해 두었다는 사실이, 이 인터페이스가 페이지네이션을
"나중에 추가할 기능"이 아니라 지금 계약의 일부로 요구하고 있음을 보여준다.

## 2. 이름 규칙: `discussion_thread` / `discussion_comment`

[Portable Schema Naming Policy](portable-schema-naming-policy.md)의 예약어
표(§5)에 `thread`/`comment` 자체는 올라 있지 않지만, [User Portable
Repository Plan §2](user-portable-repository-plan.md#2-예약어-충돌-테이블-이름부터-다시-확인한다)/
[ACL Portable Repository Plan §2](acl-portable-repository-plan.md#2-이름-규칙-rule-단독-대신-모듈-접두어를-쓴다)가
이미 확립한 "테이블 이름에 모듈 접두어를 남긴다"는 관례를 그대로 따른다 —
`discussion/README.md`의 Migration Planning Note가 제안한 이름
(`discussion_thread`, `discussion_comment`)도 이미 이 관례와 일치한다.
이 문서는 그 두 이름을 그대로 확정한다.

## 3. `DiscussionThread` → `discussion_thread` 테이블

`DiscussionThread`(`thread.py`)는 `id`, `document_id`, `title`,
`created_by`, `created_at`, `status`, `closed_at`(nullable),
`paused_at`(nullable) 필드를 가진다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) — `DiscussionService.create_thread`가 이미 `str(uuid.uuid4())`로 생성 |
| `document_id` | `String(255)` | `NOT NULL`, FK → `document.id`(`fk_discussion_thread_document_id`) | `DiscussionThread.document_id`. `document`는 이미 마이그레이션이 있는 실재 테이블이므로(`revision.document_id`와 동일 근거), `acl_rule.subject_id`처럼 다형 참조가 아니라 FK를 그대로 건다 |
| `title` | `String(500)` | `NOT NULL` | `DiscussionThread.title` — 생성자가 공백만 있는 값은 거부하지만 길이 상한은 두지 않는다. `discussion/README.md`가 이미 제안한 `String(500)`을 그대로 채택(제목은 `document.title`류 표시용 문자열보다 길 수 있는 자유 텍스트라는 전제) |
| `created_by` | `String(255)` | `NOT NULL` | `DiscussionThread.created_by`. `revision.author_id`(`src/persistence/models.py`)가 이미 FK 없이 사용자 식별자를 저장하는 선례를 그대로 따른다 — [User Portable Repository Plan](user-portable-repository-plan.md#1-현재-상태-inmemory조차-없는-것도-있다)이 확인했듯 계정 테이블(`account`) 자체가 아직 DB 테이블이 아니므로 지금 FK를 걸 대상이 없다 |
| `status` | `String(20)` | `NOT NULL`, 기본값 `"open"` | §6에서 상세히 다루는 state 컬럼. `ThreadState`(`state.py`) 값(`open`/`closed`/`paused`)을 문자열로 저장 — [Portable Text Collation Policy §2](portable-text-collation-policy.md#2-기본-collation-utf8mb4_bin-mariadb-대소문자-구분)의 기본값(`utf8mb4_bin`)을 그대로 쓴다(고정된 소문자 문자열만 쓰므로 대소문자 비교 이슈 없음, ACL `subject_type`과 동일 근거) |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy §3](portable-timestamp-column-policy.md#3-db-서버-사이드-default-의존-최소화) — `DiscussionService.create_thread`가 이미 `datetime.now(timezone.utc)`로 채운다(`service.py`) |
| `closed_at` | `DateTime(timezone=True)` | `NULL` 허용 | `DiscussionThread.close()`가 설정, `reopen()`이 `None`으로 되돌린다 — README의 "closed_at/paused_at은 서로 독립적" 관찰(§6과 연결)을 그대로 컬럼에 반영 |
| `paused_at` | `DateTime(timezone=True)` | `NULL` 허용 | `DiscussionThread.pause()`가 설정. `pause()`가 `closed_at`을 건드리지 않는 것처럼, `close()`도 `paused_at`을 건드리지 않는다 — 두 컬럼을 하나로 합치지(`state_changed_at`) 않는 이유 |

- 인덱스: §5에서 페이지네이션 근거와 함께 다룬다.

## 4. `DiscussionComment` → `discussion_comment` 테이블

`DiscussionComment`(`comment.py`)는 `id`, `thread_id`, `body`,
`created_by`, `created_at`, `is_hidden`, `hidden_at`(nullable) 필드를
가진다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) |
| `thread_id` | `String(255)` | `NOT NULL`, FK → `discussion_thread.id`(`fk_discussion_comment_thread_id`) | `DiscussionComment.thread_id` |
| `body` | `Text` | `NOT NULL` | `DiscussionComment.body` — 댓글 본문은 길이 상한이 없는 자유 텍스트(`document`/`revision`의 본문 컬럼과 동일하게 `Text` 사용) |
| `created_by` | `String(255)` | `NOT NULL` | §3의 `discussion_thread.created_by`와 동일 근거(FK 없음) |
| `is_hidden` | `Boolean` | `NOT NULL`, 기본값 `False` | `DiscussionComment.is_hidden`. [Portable Schema Naming Policy §3](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의 `is_`/`has_` 접두어 규칙을 이미 만족하는 이름 |
| `hidden_at` | `DateTime(timezone=True)` | `NULL` 허용 | `DiscussionComment.hide()`가 설정 |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL` | §3과 동일 근거 |

- `to_public_view()`/`to_moderator_view()`(`comment.py`)는 도메인 계층의
  뷰 변환이며 컬럼 설계에 영향을 주지 않는다 — `is_hidden`이 `True`일 때
  `body`를 가리는 로직은 조회 이후 애플리케이션 계층의 책임으로 남는다(DB는
  항상 실제 `body`를 저장/반환).

## 5. 페이지네이션 결정성: `LIMIT`/`OFFSET`은 tie-break 컬럼이 필요하다

**핵심 설계: `ORDER BY created_at`만으로는 페이지네이션이 결정적이지
않다. `discussion_thread`/`discussion_comment` 모두 `(정렬 컬럼, id)`
복합 순서로 정렬해 동시각을 `id`로 깨뜨린다.**

- **왜 revision과 다른 문제인가.** [ACL Portable Repository Plan
  §5](acl-portable-repository-plan.md#5-규칙-우선순위-재현-sort_order와-인덱스)가
  이미 지적했듯, `RevisionRepository.list_by_document_id`는 `created_at`
  오름차순만으로 안전하다 — 그 조회는 페이지 분할 없이 전체 목록을 한 번에
  반환하므로, 두 리비전이 동시각을 가져도 그 둘의 상대 순서만 흔들릴 뿐
  결과 집합 자체(어떤 행이 포함되는가)는 변하지 않는다. `discussion`의
  `list_threads_by_document_id`/`list_comments_by_thread_id`는
  `limit`/`offset`으로 같은 정렬을 **여러 번에 걸쳐** 잘라 호출한다
  (`router.py`가 페이지당 한 번씩 호출) — `ORDER BY created_at`에 동시각
  행이 있으면 DB가 그 동시각 그룹 내부의 반환 순서를 호출마다 다르게 정할
  수 있고, 그러면 1페이지와 2페이지 경계에서 같은 행이 두 번 나타나거나
  아예 어느 페이지에도 나타나지 않을 수 있다. 정렬만 하는 조회에서는 사소한
  흔들림이던 것이 페이지네이션에서는 데이터 유실/중복으로 나타난다.
- **동시각이 실제로 생기는가.** `DiscussionService.create_thread`/
  `add_comment`(`service.py`)는 각각 별도 HTTP 요청마다
  `datetime.now(timezone.utc)`를 새로 호출하므로, 정상적인 단일 요청 흐름
  에서는 revision과 마찬가지로 동시각이 실질적으로 드물다. 하지만 이
  문서는 "드물다"에 기대지 않는다 — 페이지네이션은 정확성이 요구되는
  기능이고(사용자가 다음 페이지를 눌렀을 때 이전 페이지에서 이미 본 댓글이
  다시 보이거나, 반대로 한 댓글이 영영 보이지 않는 것은 눈에 띄는 버그다),
  타임스탬프 해상도(마이크로초)에 기대는 대신 항상 참인 결정성 보장을
  스키마 차원에서 만든다.
- **해법: `id`를 2차 정렬 키로 쓴다.** `id`는 [Portable ID Column
  Policy](portable-id-column-policy.md)에 따라 이미 모든 행에서 유일한
  UUID 문자열이다. `ORDER BY created_at, id`(또는 스레드/댓글 각각
  `document_id`/`thread_id`로 먼저 필터링한 뒤)로 정렬하면, `created_at`이
  같은 행들 사이에서도 `id` 값이 항상 같은 순서를 만들어 어떤 페이지
  호출에서도 동일한 전체 순서가 재현된다. ACL의 `sort_order`(전용 정수
  컬럼)와 달리 여기서는 순서 자체에 의미(우선순위)가 없고 "페이지 경계가
  항상 같은 곳에서 잘린다"만 보장하면 되므로, 이미 존재하는 `id` 컬럼을
  재사용하는 것으로 충분하다 — ACL처럼 새 컬럼(`sort_order`)을 추가할
  필요가 없다.
- **인덱스.** 두 조회 모두 "주어진 `document_id`(또는 `thread_id`)의 행을
  `created_at, id` 순으로 잘라 가져오기"이므로, 그 정렬 키를 포함하는 복합
  인덱스를 명시적으로 둔다:
  - `discussion_thread`: `ix_discussion_thread_document_id_created_at_id`
    (`document_id`, `created_at`, `id`)
  - `discussion_comment`: `ix_discussion_comment_thread_id_created_at_id`
    (`thread_id`, `created_at`, `id`)

  `revision`은 페이지네이션이 없어 FK가 자동으로 만드는 인덱스(MariaDB
  InnoDB 기준)에 기댈 수 있었지만(ACL Plan §5가 이미 인용), `discussion`은
  정렬 키(`created_at`, `id`)까지 인덱스에 포함되어야 `LIMIT`/`OFFSET`이
  매 페이지마다 전체 테이블을 정렬하지 않는다 — [DB Adapter Contract
  §2](db-adapter-contract.md#2-최소-동작-집합)의 "정렬은 호출자가 지정"
  원칙에 따라 Repository가 이 순서로 `ORDER BY`를 명시한다.

## 6. State: `status`는 지금 free string으로 남기고 CHECK는 걸지 않는다

`ThreadState`(`state.py`)는 `open`/`closed`/`paused` 세 값을 정의하지만,
`DiscussionThread.__init__`(`thread.py`)은 `status` 인자를 검증하지 않는다
— `discussion/README.md`의 "State" 섹션이 "an arbitrary string is not
rejected"라고 이미 이 상태를 사실로 기록해 두었다. [ANSI SQL Persistence
Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)는
네이티브 `ENUM` 타입을 금지하지만 `CHECK` 제약은 금지하지 않으므로(두 DB
모두의 표준 기능), 기술적으로는 `CHECK (status IN ('open', 'closed',
'paused'))`를 걸어 이 간극을 스키마 레벨에서 메울 수 있다.

**이 문서는 그 `CHECK` 제약을 지금 제안하지 않는다.** [User Portable
Repository Plan §5](user-portable-repository-plan.md#5-group멤버십--user_group--user_group_member-테이블)가
`user_group.name`의 `UNIQUE` 여부를 판단할 때 쓴 것과 같은 원칙 —
"도메인이 강제하지 않는 제약을 스키마에만 먼저 걸면 애플리케이션과 DB의
규칙이 어긋난다" — 을 그대로 적용한다. 지금 애플리케이션 계층이 임의
문자열을 허용하는 상태에서 DB에만 `CHECK`를 걸면, 같은 입력이 서비스
계층에서는 통과하고 DB commit 시점에만 실패하는 위치가 생기고, 그 실패를
받아내 도메인 예외로 변환할 처리도 `DiscussionService`/`DiscussionThread`
어디에도 아직 없다. 따라서:

- 컬럼은 `String(20)` `NOT NULL` 자유 문자열로 두고, 기본값만 도메인 기본값
  (`"open"`, `thread.py`의 `status: str = "open"`)과 맞춘다.
- `ThreadState`를 `DiscussionThread.__init__`에서 실제로 검증하도록 도메인
  계층을 먼저 바꾸는 것은 이 문서(0456, docs 범위)가 아니라 discussion
  모듈 자체의 후속 태스크(번호 미배정) 범위다 — 그 변경이 들어온 뒤에야
  `CHECK` 제약을 추가하는 것이 애플리케이션 규칙과 일치한다.
- `discussion/README.md`의 "Sequencing relative to existing gaps" 절이
  이미 같은 결론(state machine이 아직 강제되지 않은 상태에서 마이그레이션을
  먼저 걸지 말 것)을 도출해 두었다 — 이 절은 그 결론을 `status` 컬럼의 DB
  제약 여부라는 구체적 질문에 적용한 것이다.
- 최종 결정은 여전히 확정이 아니라 제안이다 — `ThreadState` 강제가
  먼저 들어오면 [0466 discussion table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)이
  `CHECK` 제약 추가 여부를 다시 판단해야 한다.

## 7. DB adapter 계약과 쿼리 빌더 정책 적용

미래 `Database*Repository` 구현체는 다른 모듈과 동일하게 [DB Adapter
Contract](db-adapter-contract.md)의 최소 동작 집합(`add`/`fetch_one`/
`fetch_all`/`execute`/`commit`/`rollback`)만 어댑터에 기대야 하고, 모든
statement는 [Portable Query Builder Policy](portable-query-builder-policy.md)에
따라 SQLAlchemy 쿼리 빌더 표현식으로만 작성해야 한다 — §5의 `ORDER BY
created_at, id` + `LIMIT`/`OFFSET`도 예외가 아니다(`select(...).order_by(
CommentORM.created_at, CommentORM.id).limit(limit).offset(offset)` 형태의
쿼리 빌더 체인으로 작성).

## 이 문서 이후 단계

- **0466**([discussion table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §3~§5가 제안한 `discussion_thread`/`discussion_comment` 테이블과
  `(created_at, id)` 정렬 인덱스를 실제 SQL 초안으로 옮긴다. §6이 제안만
  하고 확정하지 않은 `status` `CHECK` 제약 여부도 이 태스크가 다시 판단
  한다.
- 실제 `Database*Repository` 구현체와 그에 대한 portability 테스트
  (0452/0453과 같은 형식)는 0466 이후 별도 태스크의 범위다.
- `DiscussionAuditEvent`의 저장소 설계는 [0457 audit portable repository
  plan](php-db-ui-micro-job-prompts-0351-0670.md)이 다룬다(적용 범위 참고).

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — Database* 구현체가 공통으로
  만족해야 하는 최소 계약(§7의 근거)과 "정렬은 호출자가 지정" 원칙(§5의
  근거), 0456이 discussion 모듈 계획 문서임을 명시한 원출처.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — 모듈
  접두어 네이밍 패턴의 원출처(§2).
- [Portable ID Column Policy](portable-id-column-policy.md) — 두 테이블
  모두의 PK 타입/생성 방식(§3~§4), §5가 tie-break 키로 재사용하는 `id`의
  유일성 근거.
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  `created_at`/`closed_at`/`paused_at`/`hidden_at` 컬럼의 타입 원칙(§3~§4).
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  `status` 문자열 컬럼의 collation 근거(§3).
- [Portable Query Builder Policy](portable-query-builder-policy.md) — 미래
  구현체가 지켜야 할 statement 작성 방식(§7).
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 네이티브
  `ENUM` 금지와 `CHECK` 제약 허용 근거(§6).
- [User Portable Repository Plan](user-portable-repository-plan.md) — 같은
  형식의 계획 문서 선례(0454), 도메인이 강제하지 않는 제약을 스키마에
  먼저 걸지 않는다는 원칙의 원출처(§6).
- [ACL Portable Repository Plan](acl-portable-repository-plan.md) — 같은
  형식의 계획 문서 선례(0455), revision과 다른 정렬 결정성 문제를 다루는
  방식의 선례(§5).
- `src/modules/discussion/README.md`의 "Discussion Migration Planning Note",
  "Sequencing relative to existing gaps" 절 — 이 문서가 재검토·확장한
  기존 스케치와 state machine 미완성 상태의 원출처.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체, 이 문서가 참조하는 0454/0455/0457/0466의 출처.
