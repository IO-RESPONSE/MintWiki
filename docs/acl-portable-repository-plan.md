# ACL Portable Repository Plan

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md), [Portable Schema Naming
Policy](portable-schema-naming-policy.md), [Portable ID Column
Policy](portable-id-column-policy.md), [Portable Timestamp Column
Policy](portable-timestamp-column-policy.md), [Portable Query Builder
Policy](portable-query-builder-policy.md)이 이미 정한 정책을 바탕으로,
`acl` 모듈(`src/modules/acl/`)의 규칙(`Rule`)이 DB 백엔드로 옮겨갈 때 따를
테이블 설계를 계획한다. [User Portable Repository
Plan](user-portable-repository-plan.md)(0454)이 `user` 모듈에 대해 같은
작업을 한 것과 짝을 이루며, `acl` 모듈 역시 아직 Database* 구현체도
Alembic 마이그레이션도 없다. **이 문서는 계획이며, 새 코드나 마이그레이션을
추가하지 않는다.** 실제 SQL 초안은 [0465](php-db-ui-micro-job-prompts-0351-0670.md)(ACL
table portable SQL)에서, 실제 `Database*Repository` 구현체는 그 이후
태스크에서 작성한다.

## 목적

`src/modules/acl/`는 지금 저장소 인터페이스(ABC)조차 없다 —
`Rule`(`rule.py`)은 `DocumentAcl`(`document_acl.py`)이나
`NamespaceAclDefaults`(`namespace_defaults.py`) 인스턴스 내부의 평범한
Python 리스트/딕셔너리로만 존재하고, `document`/`revision`/`user`
모듈과 달리 `RuleRepository` 같은 포트 자체가 정의돼 있지 않다. 이 규칙
목록을 DB 테이블로 옮기려 할 때 실제로 막히는 지점은 두 가지다 — 이
문서의 태스크 노트가 지목한 그대로다.

1. **규칙 우선순위(rule precedence).** `AclService.check()`(`service.py`)는
   "등록 순서대로 스캔해 조건에 맞는 첫 규칙이 승리"하는 first-match-wins
   방식으로 동작한다(`acl/README.md`의 ACL Evaluation Order §2,
   `test_rule_precedence.py::TestOrderOverridesSpecificity`가 순서가
   effect 조합이나 구체성보다 우선함을 증명한다). Python 리스트는 append
   순서를 그대로 보존하지만, SQL 테이블은 `ORDER BY` 없이 행 반환 순서를
   보장하지 않는다 — 이 규칙 목록을 그대로 테이블에 옮기면 우선순위
   자체가 깨진다.
2. **인덱스 요구.** 미래 조회(`문서/네임스페이스별 규칙을 우선순위대로
   전부 가져오기`)가 실제로 어떤 인덱스를 필요로 하는지가 아직 어디에도
   정해져 있지 않다.

이 문서는 이 두 문제를 새 SQL/구현 태스크가 처음부터 판단하지 않도록
미리 정한다.

## 적용 범위

계획 대상:

- `src/modules/acl/rule.py`(`Rule`)가 `document_acl.py`(`DocumentAcl`)와
  `namespace_defaults.py`(`NamespaceAclDefaults`) 두 컨텍스트에서 암시하는
  미래 테이블.

계획 대상이 아닌 것(참고로만 다룸):

- `AclAuditEvent`/`AclAuditRecorder`(`audit_event.py`, `audit_recorder.py`)의
  저장소 설계 — `modules/audit/README.md`가 "permission logs"를 명시적으로
  `audit` 모듈 소유로 두고 있고, 그 모듈의 portability 계획은
  [0457 audit portable repository plan](php-db-ui-micro-job-prompts-0351-0670.md)과
  [0467 audit table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)의
  범위다 — 이 문서보다 뒤 번호 태스크이므로 범위 밖(Out of Scope: "Work
  from later task numbers")이다.
- `Group`/`user_group` 테이블 — [User Portable Repository
  Plan](user-portable-repository-plan.md#5-groupmember_ids--user_group--user_group_member-테이블)(0454)이
  이미 계획했다. 이 문서는 `SubjectType.GROUP`이 그 테이블의 `id`를
  참조한다는 전제만 가져다 쓴다.
- `document` 테이블 자체 — FK 대상으로서만 참조한다.
- Database* 구현체 코드, Alembic 마이그레이션 자체 — 이 문서 이후 별도
  태스크(0465, 번호 미배정 후속 태스크)의 범위다.

## 1. 현재 상태: 저장소 인터페이스조차 없다

| 도메인 모델 | 저장소 인터페이스 | 현재 저장 방식 | Database 구현 |
|---|---|---|---|
| `Rule`(문서 범위) | 없음 | `DocumentAcl._rules`(인스턴스 내부 list) | 없음 |
| `Rule`(네임스페이스 기본값) | 없음 | `NamespaceAclDefaults._rules_by_namespace`(dict, 프로세스 메모리) | 없음 |

`document`/`revision`/`user`(세션/차단)는 최소한 `InMemory*Repository`나
`SessionRepository` 같은 ABC 인터페이스가 있어 "포트는 있지만 구현이
없다"는 상태였다. `acl`은 그 단계 이전이다 — 규칙을 담는 그릇
(`DocumentAcl`, `NamespaceAclDefaults`)이 도메인 모델 인스턴스 자체이고,
저장소 계층을 아예 거치지 않는다.

## 2. 이름 규칙: `rule` 단독 대신 모듈 접두어를 쓴다

[Portable Schema Naming Policy §5](portable-schema-naming-policy.md#5-예약어-회피)는
예약어 회피 예시로 `condition`의 대체 이름 중 하나로 `rule`을 직접 들고
있다 — 즉 `rule`이라는 단어 자체는 이 정책이 금지하는 예약어가 아니다.
그럼에도 이 문서는 테이블 이름으로 `rule`을 단독으로 쓰지 않는다:

- 이 모듈은 같은 도메인 모델(`Rule`)이 문서 범위/네임스페이스 범위라는
  서로 다른 두 컨텍스트에 쓰인다(§3, §4) — 접두어 없이 `rule` 하나만
  쓰면 두 테이블을 구분할 이름 공간이 없다.
  [User Portable Repository Plan §2](user-portable-repository-plan.md#2-예약어-충돌-테이블-이름부터-다시-확인한다)가
  `Session`/`Block`을 `user_session`/`user_block`으로 지은 것과 같은
  이유(모듈 접두어로 소속을 이름에 남긴다)를 따른다.
- 이 문서는 `acl_rule`(문서 범위)과 `acl_namespace_rule`(네임스페이스
  기본값 범위) 두 이름을 제안한다.

## 3. `Rule`(문서 범위) → `acl_rule` 테이블

`Rule`(`rule.py`)은 `id`, `subject_type`, `subject_id`(nullable),
`permission`, `effect`, `expires_at`(nullable) 필드를 가진다.
`DocumentAcl`(`document_acl.py`)은 `document_id` 하나에 이 규칙을 순서가
있는 리스트로 묶는다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) — 애플리케이션이 `uuid.uuid4()`로 생성 |
| `document_id` | `String(255)` | `NOT NULL`, FK → `document.id`(`fk_acl_rule_document_id`) | `DocumentAcl.document_id` |
| `subject_type` | `String(20)` | `NOT NULL` | `SubjectType` enum 값(`user`/`group`/`anonymous`/`all`)을 문자열로 저장. [Portable Text Collation Policy §2](portable-text-collation-policy.md#2-기본-collation-utf8mb4_bin-mariadb-대소문자-구분)의 기본값(`utf8mb4_bin`)을 그대로 쓴다 — enum 값은 애플리케이션이 고정된 소문자 문자열만 쓰므로 대소문자 비교 이슈가 없다(ID 컬럼과 같은 근거, [Portable Text Collation Policy §3](portable-text-collation-policy.md#3-대소문자-구분-컬럼-예시-id)) |
| `subject_id` | `String(255)` | `NULL` 허용 | `Rule.__init__`이 `USER`/`GROUP`일 때만 필수로 요구하고(`MissingSubjectIdError`) 그 외에는 받지 않는다 — 컬럼도 그 규칙을 그대로 반영해 nullable로 둔다. `USER`일 때는 미래 `account.id`, `GROUP`일 때는 [`user_group.id`](user-portable-repository-plan.md#5-groupmember_ids--user_group--user_group_member-테이블)를 가리키지만, 두 참조 대상이 컬럼 하나로 갈리므로 FK 제약은 걸지 않는다(다형 참조 — `document.current_revision_id`가 이미 같은 이유로 FK 없이 서비스 계층 검증에 의존하는 패턴, [persistence-boundaries.md](persistence-boundaries.md)) |
| `permission` | `String(20)` | `NOT NULL` | `Permission` enum 값(`read`/`edit`/`discuss`/`move`/`delete`/`admin`) — `subject_type`과 동일한 collation 근거 |
| `effect` | `String(10)` | `NOT NULL` | `Effect` enum 값(`allow`/`deny`) |
| `expires_at` | `DateTime(timezone=True)` | `NULL` 허용 | [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) — `Rule.expires_at`이 없으면 영구 규칙(`Rule.is_temporary()`) |
| `sort_order` | `Integer` | `NOT NULL` | §5에서 상세히 다루는 규칙 우선순위 재현용 컬럼 |

- **`UNIQUE(document_id, sort_order)`**(`uq_acl_rule_document_id_sort_order`):
  같은 문서 안에서 두 규칙이 같은 순번을 가질 수 없게 해, "이 문서의
  규칙 순서"가 항상 하나로 결정되게 한다.
- `id`가 규칙 자체의 식별자([`AclAuditEvent.rule_id`](php-db-ui-micro-job-prompts-0351-0670.md)가
  참조하는 대상)이고, 우선순위는 별도 `sort_order` 컬럼이 담당한다 —
  규칙을 식별하는 것과 규칙을 정렬하는 것을 하나의 컬럼에 겹쳐 쓰지
  않는다.

## 4. `Rule`(네임스페이스 기본값) → `acl_namespace_rule` 테이블

`NamespaceAclDefaults`(`namespace_defaults.py`)는 `document_id` 대신
문자열 `namespace`(예: `DEFAULT_NAMESPACE = "*"`,
`namespace_parser.py`가 문서 제목에서 파싱하는 값)를 키로 규칙 목록을
묶는다. `namespace`는 별도 테이블이 없는 자유 문자열이라 FK를 걸 대상이
없다 — [ACL README](../src/modules/acl/README.md)와
`default_policy.py`가 이미 등록되지 않은 네임스페이스를 빈 목록으로
처리하는 것도 이 값이 참조 무결성 검증 대상이 아님을 보여준다.

| 컬럼 | 타입 | 제약 | 근거 |
|---|---|---|---|
| `id` | `String(255)` | PK | [Portable ID Column Policy](portable-id-column-policy.md) |
| `namespace` | `String(255)` | `NOT NULL` | `NamespaceAclDefaults`의 키. FK 없음(위 설명) |
| `subject_type` | `String(20)` | `NOT NULL` | §3과 동일 |
| `subject_id` | `String(255)` | `NULL` 허용 | §3과 동일 |
| `permission` | `String(20)` | `NOT NULL` | §3과 동일 |
| `effect` | `String(10)` | `NOT NULL` | §3과 동일 |
| `expires_at` | `DateTime(timezone=True)` | `NULL` 허용 | §3과 동일 |
| `sort_order` | `Integer` | `NOT NULL` | §5 참고 |

- **`UNIQUE(namespace, sort_order)`**(`uq_acl_namespace_rule_namespace_sort_order`) —
  §3과 같은 이유.
- `acl_rule`과 합치지 않고 별도 테이블로 분리하는 이유: 두 컨텍스트는
  이미 서로 다른 도메인 클래스(`DocumentAcl` vs `NamespaceAclDefaults`)이고,
  키 컬럼의 성격이 다르다(`document_id`는 FK 필수, `namespace`는 FK
  없음). 한 테이블에 두 키 컬럼을 모두 두고 "정확히 하나만 채운다"는
  규칙을 CHECK 제약이나 애플리케이션 검증으로 강제하는 대신, 테이블을
  나눠 애초에 그 상태 자체가 존재할 수 없게 한다 — `user_block`처럼
  선택 사항 필드가 있는 테이블도 아니고, 두 컨텍스트가 조회 패턴(§5)까지
  다르므로 분리가 더 단순하다.
- [0465 ACL table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)의
  job 노트("namespace/document rule 구분을 둔다")가 이미 이 분리를
  전제하고 있다 — 이 문서가 그 구분을 두 테이블로 구체화한다.

## 5. 규칙 우선순위 재현: `sort_order`와 인덱스

**핵심 설계: 규칙 우선순위는 `created_at` 같은 타임스탬프가 아니라
전용 정수 컬럼 `sort_order`로 저장한다.**

- `revision.list_by_document_id`는 `created_at` 오름차순으로 정렬해도
  안전하다 — 리비전은 서로 다른 사용자 요청(HTTP 왕복)마다 하나씩
  생성되므로 타임스탬프 해상도(마이크로초/밀리초) 안에서 순서가 겹칠
  일이 거의 없다. 반면 `test_rule_precedence.py`가 보여주듯 ACL 규칙은
  같은 트랜잭션/같은 서비스 호출 안에서 여러 개가 연속으로 추가될 수
  있고(`default_policy.py::default_rules()`가 세 규칙을 한 번에 만드는
  것이 실제 사례), 이 경우 타임스탬프 컬럼만으로는 두 규칙의 순서를
  구분하지 못할 수 있다. 우선순위가 정확성에 직결되는 컬럼(첫 매칭
  규칙이 곧 최종 결정)이므로, 타임스탬프의 우연한 해상도에 기대지 않고
  애플리케이션이 명시적으로 정수 순번을 채운다.
- **값 생성 방식**: 규칙을 추가하는 서비스 계층(`DocumentAcl.add_rule`/
  `AclAuditRecorder.record_rule_added`에 대응할 미래
  `Database*Repository.add_rule`)이 "해당 `document_id`(또는
  `namespace`)에 이미 저장된 규칙 중 가장 큰 `sort_order` + 1"을 다음
  값으로 채운다 — `0`부터 시작해 append 순서를 그대로 정수로 옮기는
  것과 동일하다.
- **동시성은 이 문서가 확정하지 않는다.** 같은 문서/네임스페이스에
  동시에 두 규칙을 추가하는 요청이 경합하면, "가장 큰 `sort_order` + 1"
  계산이 레이스 컨디션에 노출될 수 있다(두 트랜잭션이 같은 최댓값을
  읽고 같은 다음 값을 계산). `UNIQUE(document_id, sort_order)` 제약이
  이 경합을 최소한 **조용한 순서 뒤바뀜이 아니라 명시적인 제약 위반
  에러**로 드러내지만, 재시도/직렬화 전략 자체는 실제
  `Database*Repository` 구현 태스크(0465 이후)가 결정한다.
- **필수 인덱스**: 미래 조회는 "주어진 `document_id`(또는 `namespace`)의
  규칙을 `sort_order` 오름차순으로 전부 가져오기" 하나뿐이다
  ([DB Adapter Contract §2](db-adapter-contract.md#2-최소-동작-집합)의
  "정렬은 호출자가 statement에 지정한다" 원칙에 따라 `ORDER BY
  sort_order`를 Repository가 명시). `revision` 테이블은 FK가 자동으로
  만드는 인덱스(MariaDB InnoDB 기준)에 기대 `document_id` 전용 인덱스를
  따로 두지 않았지만, ACL 규칙 조회는 정렬(`ORDER BY sort_order`)까지
  필요하므로 이 문서는 복합 인덱스를 명시적으로 요구한다:
  - `acl_rule`: `ix_acl_rule_document_id_sort_order` (`document_id`,
    `sort_order`)
  - `acl_namespace_rule`: `ix_acl_namespace_rule_namespace_sort_order`
    (`namespace`, `sort_order`)

  두 인덱스 모두 위 `UNIQUE` 제약과 컬럼 구성이 같으므로, 실제 DDL에서는
  `UNIQUE` 제약이 이 인덱스 역할을 겸한다(대부분의 DB가 UNIQUE 제약
  생성 시 인덱스를 자동으로 만든다) — 별도 인덱스를 중복으로 추가할
  필요는 없다. 이 문서가 "인덱스가 필요하다"고 확정하는 지점은 정렬
  키가 인덱스에 포함되어야 한다는 것이고, 그 인덱스를 UNIQUE 제약과
  별개 객체로 만들지 겸용할지는 실제 마이그레이션(0465 이후)의 DDL
  세부사항이다.

## 6. DB adapter 계약과 쿼리 빌더 정책 적용

미래 `Database*Repository` 구현체는 다른 모듈과 동일하게 [DB Adapter
Contract](db-adapter-contract.md)의 최소 동작 집합(`add`/`fetch_one`/
`fetch_all`/`execute`/`commit`/`rollback`)만 어댑터에 기대해야 하고,
모든 statement는 [Portable Query Builder
Policy](portable-query-builder-policy.md)에 따라 SQLAlchemy 쿼리 빌더
표현식으로만 작성해야 한다 — `sort_order` 계산에 쓰는 "현재 최댓값
조회" 쿼리도 예외가 아니다(`SELECT MAX(sort_order) ...`를 쿼리 빌더
`func.max()` 표현으로 작성). §5의 `UNIQUE(document_id, sort_order)`
위반은 [db-adapter-contract.md §3](db-adapter-contract.md#3-통합-제약-위반-신호)의
통합 제약 위반 신호를 거쳐 도메인 예외로 변환되어야 한다.

## 이 문서 이후 단계

- **0465**([ACL table portable SQL](php-db-ui-micro-job-prompts-0351-0670.md)):
  §3~§5가 제안한 `acl_rule`/`acl_namespace_rule` 테이블과 `sort_order`
  컬럼을 실제 SQL 초안으로 옮긴다.
- 실제 `Database*Repository` 구현체와 그에 대한 portability 테스트
  (0452/0453과 같은 형식)는 0465 이후 별도 태스크의 범위다 — 특히 §5가
  확정하지 않은 `sort_order` 동시성 처리(레이스 컨디션 재시도 전략)는
  그 구현 태스크가 결정해야 한다.
- `AclAuditEvent`의 저장소 설계는 [0457 audit portable repository
  plan](php-db-ui-micro-job-prompts-0351-0670.md)이 다룬다(적용 범위
  참고).

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — Database* 구현체가 공통으로
  만족해야 하는 최소 계약(§6의 근거)과 "정렬은 호출자가 지정" 원칙(§5의
  근거).
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — `rule`
  예약어 판단과 접두어 네이밍 패턴의 원출처(§2).
- [Portable ID Column Policy](portable-id-column-policy.md) — 두 테이블
  모두의 PK 타입/생성 방식(§3~§4).
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  `expires_at` 컬럼의 타입 원칙(§3~§4).
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  enum 문자열 컬럼(`subject_type`/`permission`/`effect`)의 collation
  근거(§3~§4).
- [Portable Query Builder Policy](portable-query-builder-policy.md) — 미래
  구현체가 지켜야 할 statement 작성 방식(§6).
- [Persistence Boundaries](persistence-boundaries.md) — 다형 참조를 FK
  없이 서비스 계층에서 검증하는 기존 패턴(`document.current_revision_id`,
  §3의 `subject_id` 근거).
- [User Portable Repository Plan](user-portable-repository-plan.md) —
  같은 형식의 계획 문서 선례(0454), `user_group` 테이블 참조 대상(§3).
- [ACL README](../src/modules/acl/README.md) — `AclService.check()`의
  ACL Evaluation Order(규칙 우선순위 동작의 원출처, §목적/§5).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체, 이 문서가 참조하는 0454/0457/0465의 출처.
