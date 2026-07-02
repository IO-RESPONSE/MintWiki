# User Portable Repository Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md), [Portable Schema Naming
Policy](portable-schema-naming-policy.md), [Portable ID Column
Policy](portable-id-column-policy.md), [Portable Timestamp Column
Policy](portable-timestamp-column-policy.md), [Portable Query Builder
Policy](portable-query-builder-policy.md)이 이미 정한 정책을 바탕으로,
`user` 모듈(`src/modules/user/`)의 세션/차단/그룹 저장소가 DB 백엔드로
옮겨갈 때 따를 테이블 설계를 계획한다. [0452](php-db-ui-micro-job-prompts-0351-0670.md)/
[0453](php-db-ui-micro-job-prompts-0351-0670.md)이 `document`/`revision`
저장소의 portability를 테스트로 검증한 것과 달리, `user` 모듈은 아직
Database* 구현체도 Alembic 마이그레이션도 없다. **이 문서는 계획이며, 새
코드나 마이그레이션을 추가하지 않는다.** 실제 SQL 초안은
[0463](php-db-ui-micro-job-prompts-0351-0670.md)(user table),
[0464](php-db-ui-micro-job-prompts-0351-0670.md)(session table)에서, 실제
`Database*Repository` 구현체는 그 이후 태스크에서 작성한다.

## 목적

`src/modules/user/`는 지금 `InMemoryUserRepository`만 구현되어 있고,
`SessionRepository`/`BlockRepository`는 인터페이스(ABC)만 정의되어 있을 뿐
구현체가 하나도 없다. `Group`(`group.py`)은 저장소 인터페이스 자체가 없고,
소속 사용자 목록(`member_ids`)을 도메인 모델 인스턴스 안에 리스트로 직접
들고 있다(비정규화). `document`/`revision`은 이미 Database* 구현체와
마이그레이션을 갖추고 있어 [db-adapter-contract.md](db-adapter-contract.md)
계약을 실제로 만족하는지 [0452](php-db-ui-micro-job-prompts-0351-0670.md)/
[0453](php-db-ui-micro-job-prompts-0351-0670.md)이 테스트로 검증할 수
있었지만, `user` 모듈은 검증할 대상 자체가 아직 없다. 이 문서는 세션/차단/
그룹을 DB 테이블로 옮길 때 이미 확정된 이식성 정책(네이밍, ID, timestamp,
쿼리 빌더)을 어떻게 적용할지 미리 정해, 실제 SQL/구현 태스크가 처음부터
판단해야 할 것을 줄인다.

## 적용 범위

계획 대상:

- `src/modules/user/session.py`(`Session`)와 `session_repository.py`
  (`SessionRepository`)가 암시하는 미래 테이블.
- `src/modules/user/block.py`(`Block`)와 `block_repository.py`
  (`BlockRepository`)가 암시하는 미래 테이블.
- `src/modules/user/group.py`(`Group`)가 암시하는 미래 테이블 — 저장소
  인터페이스 자체가 아직 없으므로, 이 문서가 그 설계까지 포함한다.

계획 대상이 아닌 것(참고로만 다룸):

- `src/modules/user/model.py`(`User`)의 기본 계정 테이블 — 실제 컬럼/제약은
  [0463 user table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)의
  범위다. 이 문서는 세션/차단/그룹 테이블의 FK 대상으로서만 참조한다(§2).
- `password.py`(`PasswordHasher`)의 해시 알고리즘 선택과 비밀번호 컬럼
  설계 — 0463 잡 노트("password/session은 별도 테이블로 분리한다")가
  가리키는 대로 계정과 별도 테이블이 되지만, 구체 설계는 이 문서의 범위
  밖이다.
- `anonymous.py`(`AnonymousIdentity`), `ip_identity.py`(`IpIdentity`) — 둘 다
  저장소가 없는 순수 인메모리 마커/값 객체이며, `user/README.md`의 "User
  Identity Boundaries"가 이미 문서화한 대로 세션/차단/그룹 어디에도
  연결되지 않는다. DB 테이블이 필요해질 지점이 없다.
- Database* 구현체 코드, Alembic 마이그레이션 자체 — 이 문서 이후 별도
  태스크(0463, 0464, 번호 미배정 후속 태스크)의 범위다.

## 1. 현재 상태: InMemory조차 없는 것도 있다

| 도메인 모델 | 저장소 인터페이스 | InMemory 구현 | Database 구현 |
|---|---|---|---|
| `User` | `UserRepository`(`create`/`get`/`get_by_username`) | `InMemoryUserRepository` | 없음 |
| `Session` | `SessionRepository`(`create`/`get`/`delete`) | 없음(인터페이스만) | 없음 |
| `Block` | `BlockRepository`(`create`/`get`/`get_by_user_id`/`delete`) | 없음(인터페이스만) | 없음 |
| `Group` | 없음 | 없음 — `member_ids`가 `Group` 인스턴스 안에 리스트로 존재(비정규화) | 없음 |

`document`/`revision`과 달리 `user` 모듈은 세션/차단/그룹에 대해 SQL을
한 줄도 실행하지 않는다 — 아래 각 절의 제안은 전부 아직 구현되지 않은
미래 상태에 대한 계획이다.

## 2. 예약어 충돌: 테이블 이름부터 다시 확인한다

[Portable Schema Naming Policy
§5](portable-schema-naming-policy.md#5-예약어-회피)는 `user`와 `group`을
PostgreSQL/MariaDB 예약어 충돌 위험 이름으로 이미 지목하고, `account`
(`user` 대체)와 `namespace_group`/`permission_group`(`group` 대체 예시)을
제안했다. `user` 모듈이 실제로 이 두 단어를 테이블 이름 후보로 쓸
위치이므로, 이 문서가 다루는 세션/차단/그룹 테이블은 이 규칙을 처음부터
적용한다.

- 기본 계정 테이블은 `account`로 짓는다(`user`가 아니다) — 최종 컬럼/제약은
  [0463](php-db-ui-micro-job-prompts-0351-0670.md)이 확정하지만, `id`(PK),
  `username`, `display_name`처럼 `User`(`model.py`)의 필드를 그대로 옮기는
  것을 전제로 삼는다. FK 컬럼명은 [네이밍
  규칙](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)에 따라
  `account_id`가 된다(`user_id`가 아니다) — 아래 3~5절의 모든 FK가 이
  이름을 쓴다.
- `Group`이 가리키는 테이블은 정확히 `group`이라는 단일 단어를 쓰지 않는다.
  `namespace_group`/`permission_group`은 ACL 네임스페이스/권한 개념과
  엮인 예시라 이 모듈에는 맞지 않는다 — 이 문서는 `user_group`(사용자를
  묶는 그룹이라는 의미가 이름에 그대로 드러남)을 제안한다. `user_group`은
  예약어 `group`과 다른 하나의 식별자이므로 §5의 "예약어 자체를 쓰지
  않는다" 기준을 만족한다 — 예약어 회피 대상은 정확히 `group`이라는 단일
  식별자이지, 그 단어를 포함하는 모든 이름이 아니다.
- 두 이름 결정을 이 문서가 최종 확정하는 것은 아니다 — `account`는
  [0463](php-db-ui-micro-job-prompts-0351-0670.md)이 최종 확정한다. 이
  문서는 그 판단이 예약어 충돌을 놓치지 않도록 미리 드러내는 것이 목적이다.

## 3. `Session` → `user_session` 테이블

`Session`(`session.py`)은 `id`, `user_id`, `created_at`, `expires_at`
네 필드를 가진다. `SessionRepository`(`session_repository.py`)는
`create`/`get`/`delete` 세 메서드만 요구한다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) — 애플리케이션이 `uuid.uuid4()`로 생성 |
| `account_id` | `String(255)` | `NOT NULL`, FK → `account.id`(`fk_user_session_account_id`) | §2의 `account_id` 네이밍 |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy §3](portable-timestamp-column-policy.md#3-db-서버-사이드-default-의존-최소화) — 서비스 계층이 `datetime.now(timezone.utc)`로 채운다(`server_default` 없음). `Session.__init__`이 이미 `created_at`을 필수 인자로 받으므로 이 정책과 자연스럽게 맞는다. |
| `expires_at` | `DateTime(timezone=True)` | `NOT NULL` | 동일. `Session.is_expired(now)`가 이 값을 비교 기준으로 쓴다. |

- 인덱스: `get`/`delete`가 모두 `id`(PK) 조회이므로 추가 인덱스가 필요 없다.
  `get_by_user_id` 같은 메서드가 `SessionRepository`에 없으므로,
  `account_id`에 인덱스를 추가할 근거도 지금은 없다 — 필요해지면(예:
  "사용자당 활성 세션 목록" 기능이 생기면) 그 시점 태스크에서
  `ix_user_session_account_id`를 추가한다.
- 만료 세션 정리(삭제)는 `SessionRepository.delete(id)`가 이미 있으므로
  새 메서드 없이 처리 가능하다 — 배치로 만료 세션을 찾아 지우는 별도
  쿼리(`expires_at < now`)가 필요해지면, [Portable Query Builder
  Policy](portable-query-builder-policy.md)에 따라 쿼리 빌더 `select()`/
  `delete()` 표현으로만 작성한다.

## 4. `Block` → `user_block` 테이블

`Block`(`block.py`)은 `id`, `user_id`, `created_at`, `expires_at`(nullable),
`reason`(nullable), `blocked_by`(nullable) 필드를 가진다.
`BlockRepository`(`block_repository.py`)는 `create`/`get`/`get_by_user_id`/
`delete` 네 메서드를 요구한다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) |
| `account_id` | `String(255)` | `NOT NULL`, FK → `account.id`(`fk_user_block_account_id`), **UNIQUE**(`uq_user_block_account_id`) | 아래 참고 |
| `created_at` | `DateTime(timezone=True)` | `NOT NULL` | [Portable Timestamp Column Policy §3](portable-timestamp-column-policy.md#3-db-서버-사이드-default-의존-최소화) |
| `expires_at` | `DateTime(timezone=True)` | `NULL` 허용 | `Block.is_active(now)`가 `None`이면 무기한 차단으로 해석한다 — 컬럼도 nullable로 그대로 옮긴다 |
| `reason` | `Text` | `NULL` 허용 | 자유 형식 사유 |
| `blocked_by` | `String(255)` | `NULL` 허용, FK → `account.id`(`fk_user_block_blocked_by`) | 차단을 수행한 관리자 계정 — `account_id`와 같은 테이블을 참조하는 두 번째 FK이므로 관계명을 컬럼 이름 자체(`blocked_by`)에 남긴다([네이밍 규칙](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의 "관계명을 접두어로 추가" 예외) |

`account_id`에 `UNIQUE` 제약을 제안하는 이유: `get_by_user_id`가
`Optional[Block]` **단수**를 반환한다 — 한 계정에 동시에 여러 유효한
차단 행이 존재하면 "어떤 것을 반환해야 하는가"가 정의되지 않는다.
`BlockRepository.delete(id)`가 이미 존재하므로, "차단 해제 = 행 삭제,
재차단 = 새 행 생성" 생명주기를 전제하면 계정당 최대 한 행만 존재하는
것이 자연스럽다. 다만 이 제약은 **이 문서가 확정하는 것이 아니라
제안**이다 — 차단 이력(해제된 과거 차단 기록)을 남기는 요구가 생기면
`UNIQUE` 대신 일반 인덱스(`ix_user_block_account_id`)로 바꾸고
`get_by_user_id`의 "가장 최근/유효한 행" 선택 기준을 Repository 쿼리에
명시해야 한다 — 그 판단은 실제 구현 태스크(0464 이후)로 미룬다.

## 5. `Group`/멤버십 → `user_group` + `user_group_member` 테이블

`Group`(`group.py`)은 지금 저장소가 전혀 없고 `member_ids: List[str]`를
도메인 모델 인스턴스 자체가 들고 있다. DB로 옮기려면 그룹과 멤버십을
분리된 두 테이블로 정규화해야 한다 —
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)가
이미 `ARRAY` 타입 금지의 대체로 "연결 테이블(1:N)로 정규화"를 원칙으로
제시했고, `member_ids`는 정확히 이 패턴에 해당한다.

**`user_group`** (그룹 자체):

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) |
| `name` | `String(255)` | `NOT NULL` | `Group.name` — 그룹명 유일성은 현재 도메인 계층(`group.py`)이 검증하지 않고 `test_group.py`에도 유일성 테스트가 없다. 이 문서는 `UNIQUE` 제약을 걸지 않는 것을 기본으로 제안하되, 최종 결정은 실제 구현 태스크로 미룬다 — 도메인이 강제하지 않는 제약을 스키마에만 먼저 걸면 애플리케이션과 DB의 규칙이 어긋난다. |

**`user_group_member`** (그룹-계정 다대다 연결 테이블):

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `user_group_id` | `String(255)` | `NOT NULL`, FK → `user_group.id`(`fk_user_group_member_user_group_id`), 복합 PK 일부 | [네이밍 규칙](portable-schema-naming-policy.md#3-테이블컬럼-네이밍-규칙)의 `<참조 테이블 단수형>_id` |
| `account_id` | `String(255)` | `NOT NULL`, FK → `account.id`(`fk_user_group_member_account_id`), 복합 PK 일부 | 동일 |

- 복합 PK `pk_user_group_member`(`user_group_id`, `account_id`)로 "같은
  계정을 같은 그룹에 중복 추가할 수 없다"를 DB가 보장한다 —
  `Group.add_member()`가 이미 애플리케이션 계층에서 중복을 막고 있지만
  (`test_add_member_does_not_duplicate_existing_member`), DB 제약으로도
  같은 불변식을 이중으로 보장한다.
- 별도 `id` PK 컬럼을 두지 않는 이유: 이 테이블은 관계 자체를 표현하는
  순수 연결 테이블이고, `(user_group_id, account_id)` 조합이 이미 자연키로
  충분하다 — `document`/`revision`처럼 참조되는 개체가 아니므로 대리키가
  필요 없다.
- `AclService`/`SubjectType.GROUP`(`acl/rule.py`)이 이 그룹 id를 subject
  식별자로 참조하지만, ACL 규칙 테이블 자체의 설계는 [ACL portable
  repository plan](php-db-ui-micro-job-prompts-0351-0670.md)(0455)의
  범위다 — 이 문서는 `user_group.id`가 그 참조 대상이 될 수 있다는
  전제만 남긴다.

## 6. DB adapter 계약과 쿼리 빌더 정책 적용

세 테이블의 미래 `Database*Repository` 구현체는 다른 모듈과 동일하게
[DB Adapter Contract](db-adapter-contract.md)의 최소 동작 집합(`add`/
`fetch_one`/`fetch_all`/`execute`/`commit`/`rollback`)만 어댑터에
기대해야 하고, 모든 statement는 [Portable Query Builder
Policy](portable-query-builder-policy.md)에 따라 SQLAlchemy 쿼리 빌더
표현식으로만 작성해야 한다 — ad hoc 문자열 SQL은 다른 모듈과 동일하게
금지 대상이다. 통합 제약 위반 신호(§3 `UNIQUE`/`FK` 위반 등)를 도메인
예외로 바꾸는 방식도 [db-adapter-contract.md
§3](db-adapter-contract.md#3-통합-제약-위반-신호)을 그대로 따른다 — 예를
들어 `user_block.account_id` `UNIQUE` 위반은 `document`의
`DuplicateNormalizedTitleError` 패턴과 같은 방식으로 도메인 예외로
변환되어야 한다(구체적인 위반 식별 방법은 0474의 범위).

## 이 문서 이후 단계

- **0463**([user table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §2가 제안한 `account` 테이블 이름과 컬럼을 최종 확정한다.
- **0464**([session table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §3의 `user_session` 설계를 실제 SQL 초안으로 옮긴다.
- `user_block`/`user_group`/`user_group_member`(§4, §5)에 대응하는
  `db/schema` 잡은 이 문서를 쓰는 시점까지 번호가 배정되지 않았다 —
  0463/0464와 달리 [job
  목록](php-db-ui-micro-job-prompts-0351-0670.md)에 별도 항목이 없으므로,
  실제 SQL 작성이 필요해지면 이 계획을 참조하는 새 태스크를 큐에 추가해야
  한다(이 문서 자체는 태스크를 추가하지 않는다).
- 실제 `DatabaseSessionRepository`/`DatabaseBlockRepository`/그룹
  저장소 구현체와 그에 대한 portability 테스트(0452/0453과 같은 형식)는
  위 SQL 초안 이후 별도 태스크의 범위다.
- §4가 제안만 하고 확정하지 않은 `user_block.account_id`의 `UNIQUE` 여부,
  §5가 확정하지 않은 `user_group.name`의 `UNIQUE` 여부는 그 SQL 초안
  태스크가 결정해야 한다.

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — Database* 구현체가 공통으로
  만족해야 하는 최소 계약(§6의 근거).
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — `user`/
  `group` 예약어 충돌과 `account`/`user_group` 대체 이름의 원출처(§2).
- [Portable ID Column Policy](portable-id-column-policy.md) — 세 테이블
  모두의 PK 타입/생성 방식(§3~§5).
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  `created_at`/`expires_at` 컬럼의 타입과 애플리케이션 값 생성 원칙(§3~§4).
- [Portable Query Builder Policy](portable-query-builder-policy.md) — 미래
  구현체가 지켜야 할 statement 작성 방식(§6).
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — `ARRAY`
  타입 금지와 "연결 테이블로 정규화" 원칙(§5의 근거).
- [Persistence Boundaries](persistence-boundaries.md) — Repository 패턴과
  세션 소유권의 원출처.
- `src/modules/user/README.md`의 "User Identity Boundaries" — `Session`/
  `Block`/`Group`이 `User.id`만 참조하고 `AnonymousIdentity`/`IpIdentity`는
  참조하지 않는다는 경계(적용 범위 절에서 인용).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체, 이 문서가 참조하는 0452/0453/0463/0464/0455의
  출처.
