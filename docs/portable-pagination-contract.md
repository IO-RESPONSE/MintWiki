# Portable Pagination Contract

이 문서는 목록 조회(`list_*`) 메서드가 페이지네이션 파라미터를 어떤
이름·타입·기본값으로 받고, 결과를 어떻게 자르는지를 고정한다.
Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

`src/modules/discussion/repository.py`, `src/modules/discussion/service.py`,
`src/modules/discussion/router.py` 는 이미 `list_threads_by_document_id`,
`list_comments_by_thread_id` 에서 `limit: Optional[int] = None`,
`offset: int = 0` 을 쓰고 있고, `docs/repository-port-contracts.md`,
`docs/service-method-contracts.md` 도 같은 시그니처를 계약으로 적어두고
있다. 이 문서는 그 관행을 모든 `list_*` 메서드에 적용되는 일반 정책으로
고정해 Python/PHP 양쪽 구현이 같은 페이지네이션 규칙을 따르게 한다.

## 기본 방식: limit/offset

- 목록 조회 메서드가 페이지네이션을 지원할 때는 `limit`/`offset` 두
  파라미터를 기본으로 쓴다. `limit` 은 반환할 최대 개수, `offset` 은
  건너뛸 개수다.
- 타입과 기본값은 다음으로 고정한다:
  - `limit: Optional[int] = None` — 생략하면 개수 제한이 없다(전체
    반환). 값을 줄 때는 1 이상이어야 한다(`router.py` 의
    `Query(default=None, ge=1)` 이 이미 이 제약을 강제한다).
  - `offset: int = 0` — 생략하면 0, 즉 처음부터 반환한다. 값을 줄 때는
    0 이상이어야 한다(`Query(default=0, ge=0)`).
- 자르는 순서는 항상 "정렬 → offset 건너뛰기 → limit 개수만 취하기"다.
  `list_threads_by_document_id`/`list_comments_by_thread_id` 가 이미
  생성 순서로 정렬한 뒤 `[offset:]` 또는 `[offset:offset+limit]` 로
  자르는 방식이 이 순서를 따른다. 정렬 기준 자체(생성 순서 등)는
  이 문서가 아니라 각 모듈의 계약(0385 portable sorting contract)이
  고정한다.
- `limit`/`offset` 은 서비스 계층 메서드 시그니처와 저장소 포트 시그니처
  양쪽에 그대로 나타난다. 서비스 계층이 값을 변형하거나 다른 이름으로
  바꿔 저장소에 넘기지 않는다 — `docs/service-method-contracts.md` 의
  `list_threads_by_document_id`/`list_comments_by_thread_id` 가 이미
  이 형태다.

## Cursor 는 adapter 뒤로 둔다

- Cursor 기반 페이지네이션(불투명 토큰으로 다음 페이지를 가리키는 방식)은
  이 계약에 넣지 않는다. 서비스 메서드 시그니처, 저장소 포트 시그니처,
  fixture 는 모두 `limit`/`offset` 만 계약 타입으로 다룬다.
- 특정 adapter(예: 대량 데이터에 대한 keyset pagination 최적화가 필요한
  DB 어댑터)가 내부적으로 cursor 방식을 쓰고 싶다면, 그 cursor 는 adapter
  구현 세부사항으로만 존재해야 한다 — 공개 서비스 메서드 시그니처에
  cursor 파라미터나 cursor 반환값을 노출하지 않는다.
  `docs/repository-port-contracts.md` 의 "공통 패턴"이 이미 정의한
  포트/구현 분리 원칙과 같다: 구현체가 생성자에서 세션을 받는 것처럼
  구현 세부사항은 자유롭지만, 인터페이스(포트)는 고정되어야 한다.
- 이렇게 나누는 이유는 두 가지다. 첫째, `limit`/`offset` 은 SQL
  `LIMIT`/`OFFSET` 절로 PostgreSQL 과 MariaDB 양쪽에서 동일하게
  동작하지만, cursor 인코딩 방식(정렬 키 조합, base64 직렬화 등)은
  구현마다 달라지기 쉬워 Python/PHP 양쪽이 같은 cursor 형식을 유지하기
  어렵다. 둘째, `limit`/`offset` 은 상태가 없어 어떤 페이지든 바로 계산할
  수 있지만, cursor 는 이전 페이지의 응답을 그대로 다음 요청에 넘겨야
  하는 상태 의존적 API 를 강제한다 — Phase A 계약은 상태 없는 API를
  기본으로 삼는다.

## 이 문서가 하지 않는 것

- 정렬 기준(생성 순서 등)을 새로 정의하지 않는다. 이는 이후 태스크
  (0385 portable sorting contract)의 범위다.
- SQL `LIMIT`/`OFFSET` 절의 DB별 구체 문법이나 대용량 offset 성능 문제를
  다루지 않는다. 이는 이후 태스크(0477 portable pagination SQL tests)의
  범위다.
- 기존 코드에 새 필드나 변환 로직을 추가하지 않는다. 이 문서는 이미
  일관되게 지켜지고 있는 `limit`/`offset` 관행을 정책으로 고정할 뿐이다.
- Cursor 기반 페이지네이션을 구현하거나 특정 adapter 를 설계하지 않는다.
  "cursor 는 adapter 뒤에 둔다"는 원칙만 고정하며, 실제 cursor 구현은
  이 문서의 범위 밖이다.

## 관련 문서

- `docs/php-replacement-strategy.md` — 두 언어가 같은 공개 메서드
  시그니처를 공유해야 한다는 병행 기간 원칙.
- `docs/service-method-contracts.md` — `list_threads_by_document_id`/
  `list_comments_by_thread_id` 의 `limit`/`offset` 시그니처.
- `docs/repository-port-contracts.md` — 저장소 포트의 페이지네이션 계약과
  포트/구현 분리 원칙("공통 패턴").
- `docs/portability-glossary.md` — Contract/Adapter 용어 정의.
