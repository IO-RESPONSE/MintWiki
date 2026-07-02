# Portable Search DB Boundary

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록),
[DB Adapter Contract](db-adapter-contract.md), [DB driver capability
model](../src/persistence/capability.py), [Search Adapter
Design](search-adapter-design.md)이 이미 정한 규칙을 바탕으로, **DB 계층과
`search` 모듈 사이의 경계**를 확정한다. 이 문서는 새 코드를 만들지 않는다 —
기존 문서 세 개가 각각 다른 각도(SQL 금지 목록, 어댑터 계약, capability
플래그, 검색 포트 설계)에서 이미 규정한 "검색은 DB 전문 검색에 의존하지
않는다"는 원칙을, **경계선이 정확히 어디를 지나는가**로 한곳에 모은다.

## 목적

지금 이 규칙들은 서로 다른 문서에 흩어져 있다.

- [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)는
  `tsvector`/`tsquery`/GIN·GiST를 금지 목록에 올리고 "`search` 모듈
  어댑터가 엔진을 캡슐화한다"고만 적어 둔다.
- [search-adapter-design.md](search-adapter-design.md)는 `SearchAdapter`
  포트가 엔진과 토크나이저를 숨긴다고 정의하고, "(later) DB fallback
  adapter"를 계획 표에 예고만 해 둔다.
- [src/persistence/capability.py](../src/persistence/capability.py)의
  `DriverCapabilities.supports_fulltext`는 PostgreSQL을 `True`, MariaDB를
  `False`로 이미 표시했지만, 이 플래그를 실제로 어디서 써도 되는지는
  코드 주석 한 줄("search 모듈은 이 플래그와 무관하게...")뿐이다.

세 문서 모두 결론은 같지만("DB 전문 검색에 의존하지 않는다"), **어느
계층까지가 "DB"이고 어느 계층부터가 "search 어댑터 내부"인지**, 그리고
"DB fallback adapter"가 도착했을 때 그 내부 구현조차 지켜야 할 제약이
무엇인지는 명시된 적이 없다. 이 경계가 불명확하면, 향후 DB fallback
adapter를 구현하는 잡이 "adapter 내부니까 `MATCH ... AGAINST`나
`to_tsvector`를 써도 되는가"를 판단할 기준이 없다. 이 문서가 그 경계를
고정한다.

## 적용 범위

적용 대상:

- `src/modules/*/repository.py`의 Database* 구현체 — 검색 질의를 실행하지
  않는다는 것을 재확인한다.
- 향후 구현될 DB fallback `SearchAdapter`
  ([search-adapter-design.md](search-adapter-design.md#planned-adapters)의
  "(later) DB fallback adapter" 행) — adapter 인터페이스 **안쪽**에서도
  지켜야 할 이식성 제약을 정의한다.
- [src/persistence/capability.py](../src/persistence/capability.py)의
  `supports_fulltext` 플래그가 어디까지 참조돼도 되는지.

적용되지 않는 것:

- `SearchAdapter` 포트 자체의 메서드 시그니처, 도메인 모델
  (`SearchDocument`/`SearchQuery`/`SearchResult`) — 이미
  [search-adapter-design.md](search-adapter-design.md)가 확정했다.
- 토크나이저 선택(n-gram 크기 등) — 어댑터 내부 정책이며 이미
  [search-adapter-design.md](search-adapter-design.md#what-stays-out-of-the-interface)가
  인터페이스 밖으로 명시했다.
- `InMemorySearchAdapter`(0246) — SQL을 전혀 거치지 않으므로 이 문서의
  대상이 아니다.
- DB fallback adapter의 실제 구현(테이블 스키마, 색인 갱신 방식) — 이
  문서는 그 구현이 **지켜야 할 경계**만 고정하고, 실제 스키마/코드는
  아직 큐에 없는 후속 잡의 범위다.

## 1. DB 계층은 검색 질의를 직접 실행하지 않는다

**규칙: `document`/`revision` 등 모듈 소유 테이블을 다루는
Database* 저장소는 제목/본문 검색 질의(`LIKE '%...%'` 전체 스캔 포함)를
직접 실행하지 않는다.** 검색은 항상 `SearchService` →
`SearchAdapter`를 거친다. 저장소는 최대한 단건 조회
(`get`, `get_by_normalized_title`)와 소유 테이블 갱신만 노출한다
([persistence-boundaries.md](persistence-boundaries.md#repository-pattern)의
Repository Pattern이 이미 규정한 "모듈은 자기 테이블만 쓴다"는 원칙의
검색 버전).

- 이유: 검색 질의가 여러 모듈 저장소에 산발적으로 흩어지면
  [search-adapter-design.md](search-adapter-design.md#design-principle-hide-the-engine-hide-the-tokenizer)가
  요구하는 "엔진을 숨긴다"는 원칙이 우회된다 — 어댑터 뒤에 숨겼어도, 다른
  경로로 저장소가 직접 `LIKE` 검색을 하면 엔진 교체 시(TNTSearch 전환 등)
  그 경로만 빠뜨리기 쉽다.

## 2. DB fallback adapter 내부도 벤더 전문 검색 문법을 쓰지 않는다

**규칙: `SearchAdapter`를 구현하는 DB fallback adapter라도, 내부 SQL은
[ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)의
금지 목록(`tsvector`/`tsquery`/GIN·GiST, MariaDB `MATCH ... AGAINST`
FULLTEXT 인덱스 포함)을 그대로 따른다.** "adapter 인터페이스 뒤에
숨겼으니 내부에서는 벤더 전용 기능을 써도 된다"는 예외를 두지 않는다.

- MariaDB(InnoDB, 10.0.5+)는 자체 `FULLTEXT` 인덱스와 ngram 파서
  플러그인을 갖고 있어 기술적으로는 사용 가능하지만, 이 정책은 여전히
  그 사용을 금지한다. 이유:
  - PostgreSQL의 `tsvector`/`tsquery`(사전 기반 랭킹, `@@` 연산자)와
    MariaDB의 `MATCH ... AGAINST`(자체 관련도 점수, 최소 단어 길이
    설정)는 문법과 랭킹 산식이 서로 달라 **양쪽에서 동일하게 동작하는
    공통 부분집합이 없다** — [ansi-sql-persistence-policy.md 원칙
    2](ansi-sql-persistence-policy.md#기본-원칙)("기능 대체가 없으면
    기능을 쓰지 않는다")를 그대로 적용한다.
  - [search-adapter-design.md](search-adapter-design.md#design-principle-hide-the-engine-hide-the-tokenizer)가
    이미 n-gram(bigram) 토크나이징을 포터블 선택으로 확정했다 — 벤더
    FULLTEXT의 내장 토크나이저에 의존하면 이 결정과 충돌하고, PHP
    TNTSearch 전환 시 이식할 대상도 사라진다.
  - `search-adapter-design.md`의 "Planned adapters" 표가 DB fallback
    adapter의 토크나이저를 이미 "PHP/SQL-side n-gram"으로 명시했다 —
    벤더 FULLTEXT가 아니라 애플리케이션이 만든 n-gram shingle을 SQL
    테이블에 저장하고 `LIKE`/`=` 같은 표준 조건으로 조회하는 방식이다.
- 결론: DB fallback adapter는 (아직 구현되지 않았지만, 구현될 때) 아래
  두 조각만으로 이루어진다.
  1. **shingle 색인 테이블** — `search_shingle(doc_id, shingle, ...)`
     같은 일반 테이블에 n-gram 조각을 저장. 표준 `VARCHAR`/`INTEGER`
     컬럼과 표준 인덱스만 쓴다.
  2. **표준 SQL 질의** — shingle 교집합을 표준 `JOIN`/`GROUP BY`/
     집계 함수로 계산해 점수를 매긴다. `MATCH ... AGAINST`나
     `@@`/`to_tsquery`는 등장하지 않는다.
  구체적인 테이블 스키마와 질의 형태는 이 문서의 범위가 아니다 — 실제
  구현이 큐에 오를 때 별도 태스크가 이 두 제약을 만족하는 스키마를
  정한다.

## 3. `supports_fulltext` capability 플래그는 검색 경로에 영향을 주지 않는다

**규칙: [`DriverCapabilities.supports_fulltext`](../src/persistence/capability.py)는
정보 제공용 플래그이며, `search` 모듈이나 DB fallback adapter의 어떤
분기 조건으로도 참조되지 않는다.**

- `capabilities_for(dialect).supports_fulltext`가 PostgreSQL에서
  `True`를 반환한다고 해서, DB fallback adapter가 PostgreSQL 경로에서만
  `tsvector`를 쓰고 MariaDB 경로에서만 shingle 테이블을 쓰는 것과 같은
  "dialect별 다른 검색 구현"으로 분기해서는 안 된다. §2가 이미 두 dialect
  모두 shingle 테이블 방식 하나로 통일했다 — capability 플래그는 이
  통일을 깨는 근거로 쓰이지 않는다.
  - PHP 마이그레이션 이후에도 §2의 shingle 테이블 방식은 PostgreSQL/
    MariaDB 어느 쪽에 붙어도 코드 변경 없이 동작해야 한다는 것이
    [search-adapter-design.md의 Portability
    path](search-adapter-design.md#portability-path-python--php)가 이미
    전제한 목표다 — dialect별 분기를 허용하면 이 목표가 무력화된다.
- 이 플래그가 실제로 쓰이는 곳은 검색과 무관한 지점뿐이다 — 예:
  `supports_returning`/`supports_json`을 참조해 insert 후 재조회 여부나
  JSON 컬럼 질의 방식을 dialect별로 분기하는 [db-adapter-contract.md
  §2](db-adapter-contract.md#2-최소-동작-집합) 관련 코드.
  `supports_fulltext`는 지금 코드베이스 어디에서도 분기 조건으로 읽히지
  않으며([src/persistence/capability.py](../src/persistence/capability.py)
  테스트인 `tests/persistence/test_capability.py` 참고, 값 검증만 하고
  분기 사용처는 없음), 이 문서는 그 상태를 정책으로 고정한다.

## 이 문서 이후 단계

이 문서는 경계 선언이며, 새 코드나 스키마를 만들지 않는다. DB fallback
adapter 자체의 구현(shingle 테이블 스키마, 색인/조회 SQL, `search`
모듈에서의 배선)은 [search-adapter-design.md의 Planned
adapters](search-adapter-design.md#planned-adapters) 표가 "later queue"로
남겨 둔 대로, 이 Phase(0441-0520)의 큐에는 아직 없다. 그 잡이 만들어질
때 이 문서의 §1~§3을 전제로 삼는다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록) —
  `tsvector`/`tsquery`/GIN·GiST 금지의 원출처.
- [DB Adapter Contract](db-adapter-contract.md) — 같은 "포트/어댑터 계약
  문서" 형식의 선례이자, capability 플래그가 참조되는 실제 지점(§2).
- [Search Adapter Design](search-adapter-design.md) — `SearchAdapter` 포트,
  도메인 모델, n-gram 토크나이저 결정의 원출처.
- [Persistence Boundaries](persistence-boundaries.md) — 모듈이 자기
  테이블만 쓴다는 원칙의 원출처(§1이 검색으로 확장).
- [src/persistence/capability.py](../src/persistence/capability.py) —
  `supports_fulltext` 플래그의 실제 정의.
