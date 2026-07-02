# Portable Sorting Contract

이 문서는 목록 조회(`list_*`) 메서드가 결과를 어떤 키로, 어떤 순서로
정렬하는지, 그리고 NULL 값을 정렬할 때 DB별 기본 동작 차이를 어떻게
피하는지를 고정한다. Phase A: PHP Replacement Contract, 0351-0390 의
산출물이다.

`src/modules/revision/repository.py` 의 `list_by_document_id` 는 이미
`.order_by(RevisionORM.created_at)` 로 생성 순서 정렬을 쓰고 있고,
`src/modules/discussion/repository.py` 의 `InMemoryDiscussionRepository`
는 append 순서(=생성 순서)를 그대로 유지해 같은 정렬을 흉내 낸다.
`src/modules/discussion/recent_activity_service.py` 의
`list_recent_activities` 는 그 생성 순서를 뒤집어 최신순을 만든다. 이
문서는 그 관행을 모든 `list_*` 메서드에 적용되는 일반 정책으로 고정해
Python/PHP 양쪽 구현, PostgreSQL/MariaDB 양쪽 DB가 같은 정렬 결과를
내도록 한다.

## 기본 정렬 키: `created_at` 오름차순(생성 순서)

- 정렬 방식을 명시하지 않는 `list_*` 메서드의 기본 정렬은 생성
  순서(`created_at` 오름차순)다. `list_by_document_id`(revision),
  `list_threads_by_document_id`/`list_comments_by_thread_id`(discussion)
  가 이미 이 기본값을 따른다.
- 최신순이 필요한 경우(`list_recent_activities`)도 별도의 "최신순" 정렬
  키를 새로 정의하지 않는다 — 생성 순서로 얻은 결과를 뒤집어(`reversed`)
  얻는다. `DiscussionRecentActivityService.list_recent_activities` 가
  이미 이 방식이다.

## Tie-breaking: `id` 를 보조 정렬 키로 쓴다

- `created_at` 컬럼의 정밀도는 DB/드라이버에 따라 다를 수 있어(초 단위
  vs microsecond), 같은 요청 안에서 여러 행이 동일한 `created_at` 값을
  가질 수 있다. 이때 정렬 결과가 특정 DB의 내부 저장 순서(물리적 row
  순서, 인덱스 스캔 순서)에 우연히 의존하게 두지 않는다.
- `created_at` 이 같은 행 사이의 순서는 `id`(`docs/portable-id-policy.md`
  가 고정한 UUID v4 문자열) 오름차순으로 결정한다. SQL 기반 저장소
  구현은 `ORDER BY created_at, id` 형태로 정렬 키를 두 개 지정해야 한다.
- `src/modules/revision/repository.py` 의 현재
  `.order_by(RevisionORM.created_at)` 는 이 tiebreak 을 아직 갖고 있지
  않다 — 이 문서가 고정하는 정책에 따르면 이후 수정 시
  `.order_by(RevisionORM.created_at, RevisionORM.id)` 로 확장해야 한다.
  기존 코드를 이 태스크에서 바로 고치지는 않는다(Out of Scope).
- 메모리 기반 구현(`InMemoryDiscussionRepository`)은 리스트 append 순서
  자체가 생성 순서 및 id 발급 순서와 일치하므로 이 정책을 자동으로
  만족한다. 다만 새 메모리 구현을 작성할 때 정렬 후 삽입처럼 append
  순서가 생성 순서와 어긋나는 방식을 쓰지 않도록 주의해야 한다.

## NULL 정렬: PostgreSQL과 MariaDB 기본값 차이를 피한다

- PostgreSQL 은 `NULL` 을 오름차순(`ASC`)에서 `NULLS LAST`, 내림차순
  (`DESC`)에서 `NULLS FIRST`로 취급한다. MariaDB/MySQL 은 `NULL` 을
  항상 가장 작은 값으로 취급해 `ASC`에서 `NULLS FIRST`, `DESC`에서
  `NULLS LAST`가 된다. 같은 `ORDER BY nullable_column` 쿼리가 이 기본값
  차이 때문에 두 DB에서 서로 다른 결과를 낸다 —
  `docs/php-replacement-strategy.md` 가 요구하는 "ANSI SQL + MariaDB
  호환" 기본 경로가 이 기본값 차이에 암묵적으로 의존해서는 안 된다.
- 이 계약이 고정하는 기본 정렬 키(`created_at`, `id`)는 모두
  `docs/persistence-boundaries.md` 가 이미 `NOT NULL`/`PRIMARY KEY` 로
  고정한 컬럼이다. 따라서 기본 정렬 경로에는 `NULL` 값이 존재하지 않고,
  위 DB별 차이가 애초에 나타나지 않는다.
- 정렬 키로 nullable 컬럼(예: 향후 soft-delete 용
  `deleted_at`(`docs/persistence-boundaries.md` "Future Considerations"),
  `revision.parent_revision_id`)을 쓰는 기능이 추가될 때는 다음을
  지켜야 이식성이 유지된다:
  - `COALESCE(column, sentinel_value)` 로 `NULL` 을 실제 데이터 범위를
    벗어나는 고정된 sentinel 값으로 치환한 뒤 그 표현식을 정렬 키로
    쓴다. `NULLS FIRST`/`NULLS LAST` 절은 ANSI SQL 표준 문법이지만
    MariaDB 가 지원하지 않는 버전이 있어(0351-0390 기준 대상 버전에서
    보장되지 않음) 기본 경로로 쓰지 않는다.
  - sentinel 값은 두 DB에서 같은 비교 결과를 내는 타입이어야 한다
    (예: `datetime` 컬럼이면 `docs/portable-datetime-policy.md` 가
    고정한 UTC epoch 의 최댓값/최솟값 근처 값).
- 이 문서를 작성하는 시점에는 어떤 `list_*` 메서드도 nullable 컬럼을
  정렬 키로 쓰지 않는다 — 위 규칙은 정렬 키가 nullable 컬럼으로
  확장될 때 적용할 정책을 미리 고정해 둔 것이다.

## 이 문서가 하지 않는 것

- 사용자가 정렬 기준을 선택하는 기능(요청 파라미터로 sort field/
  direction 을 받는 API)을 설계하지 않는다.
- 전문 검색(full-text search) relevance ranking 정렬을 다루지 않는다.
- 기존 코드(`revision/repository.py` 의 tiebreak 없는 `order_by` 등)를
  이 태스크에서 수정하지 않는다 — 정책만 고정하며, 실제 코드 변경은
  각 모듈이 이 계약을 참조하는 이후 태스크의 범위다.
- SQL `LIMIT`/`OFFSET` 절이나 페이지네이션 자체의 규칙을 다루지 않는다
  (`docs/portable-pagination-contract.md` 의 범위).

## 관련 문서

- `docs/php-replacement-strategy.md` — ANSI SQL + MariaDB 호환 기본
  경로 원칙과 PostgreSQL 전용 기능 사용 금지.
- `docs/portable-pagination-contract.md` — "정렬 → offset 건너뛰기 →
  limit 개수만 취하기" 순서에서 정렬이 차지하는 위치.
- `docs/persistence-boundaries.md` — `created_at`/`id` 컬럼의
  `NOT NULL`/`PRIMARY KEY` 정의와 향후 nullable `deleted_at` 컬럼 계획.
- `docs/portable-datetime-policy.md` — 정렬 키로 쓰이는 `created_at`
  값의 UTC 저장 정책.
- `docs/portable-id-policy.md` — tiebreak 키로 쓰이는 `id` 값의 형식과
  "id 는 순서를 인코딩하지 않는다"는 원칙.
- `docs/portability-glossary.md` — Contract/Adapter 용어 정의.
