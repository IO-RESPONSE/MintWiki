# Portable Text Collation Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md#4-collation-매트릭스)의
"대체 필요"/"차이(주의)" collation 항목을 구체화하고,
[Portable ID Column Policy](portable-id-column-policy.md#2-id-생성-방식과-형식)와
[Portable Timestamp Column Policy](portable-timestamp-column-policy.md)가
예고한 마지막 컬럼 정책(naming → id → timestamp → **collation**)을
확정한다. 이 문서는 정책 선언이며, 기존 코드(`src/persistence/models.py`의
`String`/`Text` 컬럼, `document.normalized_title` UNIQUE 제약)를 지금 바꾸지
않는다 — 이미 이 정책이 요구하는 방식(대소문자 구분 비교, 애플리케이션 계층
정규화)으로 동작하고 있고, 이 문서는 그 동작을 새 컬럼에도 적용할 규칙으로
명문화하는 것이다.

## 목적

PostgreSQL은 기본적으로 문자열을 **바이트 단위로 대소문자 구분**해
비교한다(`=`, `LIKE`, UNIQUE 제약 모두 동일). MariaDB는 컬럼/테이블에 지정된
**collation**에 따라 비교 방식이 달라지는데, 흔히 쓰이는 기본값
(`utf8mb4_general_ci`, `utf8mb4_unicode_ci`)은 **대소문자를 구분하지 않는다**
([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#4-collation-매트릭스)의
"기본 문자열 비교" 항목). collation을 명시하지 않고 이식하면, PostgreSQL에서
서로 다른 값으로 취급되던 문자열(`"Test"`와 `"test"`)이 MariaDB에서는 같은
값으로 취급되어 `=` 비교 결과와 UNIQUE 제약 위반 여부가 DB마다 달라질 수
있다. 이 문서는 **모든 문자열 컬럼의 collation을 명시적으로 고정**해, 이
차이가 이식 시점에 드러나지 않게 한다.

## 적용 범위

이 정책은 아래가 정의하는 문자열 컬럼(`VARCHAR`/`TEXT`, SQLAlchemy
`String`/`Text`)에 적용된다.

- `migrations/versions/` 아래 Alembic 마이그레이션이 만드는 테이블/컬럼의
  문자셋·collation 설정.
- `src/persistence/models.py`의 `String`/`Text` 컬럼.
- 문자열 비교/검색을 수행하는 저장소·서비스 계층 코드
  (`document.normalized_title` 조회, 향후 검색 쿼리 등).
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡).

적용되지 않는 것:

- 대소문자 무시 검색(`ILIKE` 대체)의 구체적 쿼리 패턴 — 상세 정책은
  [0512](#이-문서-이후-단계)에서 확정한다. 이 문서는 그 패턴이 의존할
  **컬럼 collation의 기준값**만 정한다.
- 한글 정렬 순서를 fixture로 검증하는 작업 — [0511](#이-문서-이후-단계)의
  범위다.
- ID 컬럼의 타입·생성 방식 자체 — [Portable ID Column
  Policy](portable-id-column-policy.md)가 이미 확정했다. 이 문서는 3절에서
  그 정책이 collation 문제를 일으키지 않는다는 전제만 확인한다.

## 1. 문자셋: `utf8mb4` (MariaDB), `UTF8` (PostgreSQL)

**정책: MariaDB의 데이터베이스/테이블/컬럼 문자셋은 항상 `utf8mb4`로
명시한다.** MariaDB의 전통적 기본값인 3바이트 `utf8`은 일부 유니코드
문자(이모지, 일부 한자)를 저장하지 못하므로 쓰지 않는다
([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#4-collation-매트릭스)의
"문자셋" 항목). PostgreSQL 쪽은 이미 `UTF8` 인코딩을 쓰고 있으므로 별도
변경이 없다.

## 2. 기본 collation: `utf8mb4_bin` (MariaDB, 대소문자 구분)

**정책: 명시적으로 대소문자 비구분 비교가 필요하다고 표시되지 않은 모든
문자열 컬럼은 MariaDB에서 `utf8mb4_bin` collation을 쓴다.** `_bin`은
문자를 바이트 값으로 비교해, PostgreSQL의 기본 대소문자 구분 비교와 같은
결과를 낸다.

- **왜 대소문자 비구분을 기본값으로 두지 않는가.** `utf8mb4_general_ci`/
  `utf8mb4_unicode_ci`를 기본으로 두면, 컬럼을 새로 추가할 때마다 "이
  컬럼이 대소문자를 구분해야 하는가"를 매번 판단해야 하고, 판단을
  빠뜨리면 PostgreSQL과 다르게 동작하는 컬럼이 조용히 생긴다.
  `document.normalized_title`처럼 이미 대소문자를 구분해 UNIQUE를 검사하는
  컬럼([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#4-collation-매트릭스)의
  "중복키 오류 시 대소문자 취급" 항목)이 대표 사례다 — `_bin`을 기본값으로
  두면 이 컬럼은 아무 추가 조치 없이 두 DB에서 동일하게 동작한다.
- **대소문자 비구분 검색이 필요한 경우.** `ILIKE`가 하던 역할(대소문자
  무시 검색)은 컬럼 collation을 바꿔 얻지 않는다. 대신
  [persistence-boundaries.md](persistence-boundaries.md)의 정규화된 컬럼
  패턴(`normalized_title`류) 또는 `LOWER()` 비교로 애플리케이션 계층에서
  대소문자를 통일한 뒤 비교한다 — 이렇게 하면 비교 결과가 컬럼 collation
  설정에 의존하지 않는다. 구체적인 쿼리 패턴은
  [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)의
  `ILIKE` 금지 목록 항목이 예고한 대로 [0512](#이-문서-이후-단계)에서
  확정한다.
- **정렬(`ORDER BY`)에 대한 영향.** `utf8mb4_bin`은 코드포인트(바이트)
  순서로 정렬한다. 이는 로케일 인지 사전순 정렬(예: ICU `ko-KR` locale
  collation)과 동일하지 않지만, 3절이 명시하듯 이 정책이 목표로 하는 것은
  "완전한 사전순 일치"가 아니라 "두 DB에서 재현 가능한 안정적 정렬"이다.

## 3. 대소문자 구분 컬럼 예시: ID

[Portable ID Column Policy](portable-id-column-policy.md#2-id-생성-방식과-형식)에
따라 모든 ID 컬럼은 애플리케이션이 `uuid.uuid4()`로 생성한 **소문자
hex + 하이픈** 형식의 문자열만 저장한다. 저장/조회 양쪽 모두 이 형식만
쓰므로 대소문자가 섞인 값이 비교 대상이 되는 경우가 없고, 2절의
`utf8mb4_bin` 기본값 아래에서도 별도 예외 처리 없이 그대로 동작한다 — 이
문서가 [portable-id-column-policy.md](portable-id-column-policy.md)가
예고한 "ID 문자열은 대소문자 비교 이슈가 실질적으로 발생하지 않는다"는
전제를 확인하는 지점이다.

## 4. 한글 정렬

**정책: 한글을 포함한 문자열의 정렬 순서는 "완전한 로케일 사전순 일치"가
아니라 "유니코드 코드포인트 기준의 안정적 정렬"을 목표로 한다.**

- PostgreSQL은 ICU/locale collation(`ko-KR-x-icu` 등)을 설정할 수 있지만,
  MariaDB에는 동등한 ICU locale collation이 없다
  ([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#4-collation-매트릭스)의
  "한글 정렬 순서" 항목). 두 DB의 정렬 결과가 완전히 같다고 보장할 수
  없으므로, 이 정책은 애초에 그 보장을 요구하지 않는다.
- 두 DB 모두 `utf8mb4_bin`(2절)을 쓰면 코드포인트 순서로 정렬하므로,
  같은 데이터에 대해 두 DB가 서로 다른 정렬 결과를 낼 위험이
  `utf8mb4_general_ci`/`utf8mb4_unicode_ci` 같은 언어별 규칙이 섞인
  collation을 쓸 때보다 줄어든다.
- 실제 fixture 데이터로 두 DB의 정렬 결과가 이 목표를 만족하는지 검증하는
  작업은 [0511](#이-문서-이후-단계)에서 진행한다 — 이 문서는 목표만
  정의한다.

## 5. 예시

| 컬럼 | collation (MariaDB) | 이유 |
|---|---|---|
| `document.id`, `revision.id`, `*_id` (FK) | `utf8mb4_bin` | 소문자 UUID 문자열만 저장 — 3절 |
| `document.normalized_title` | `utf8mb4_bin` | 대소문자 다른 값을 다른 제목으로 취급(UNIQUE 제약) — 2절 |
| `document.title`, `revision.summary` 등 표시용 문자열 | `utf8mb4_bin` (기본값) | 명시적으로 대소문자 비구분이 필요하다고 표시되지 않음 — 2절 |
| 향후 대소문자 비구분 검색이 필요한 컬럼 | `utf8mb4_bin` + 정규화된 컬럼/`LOWER()` 비교 | 컬럼 collation 자체는 그대로 두고 애플리케이션 계층에서 흡수 — [0512](#이-문서-이후-단계) |

## 이 문서 이후 단계

- **0447**: 이 문서가 요구하는 명시적 `utf8mb4`/`utf8mb4_bin` 지정 누락과
  [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의
  `ILIKE` 등 금지 키워드를 코드에서 함께 자동 검사하는 스크립트에
  포함한다.
- **0511**([MariaDB collation fixture tests](php-db-ui-micro-job-prompts-0351-0670.md)):
  4절이 정의한 한글 정렬 목표와 2절의 `normalized_title` 대소문자 처리를
  실제 fixture 데이터로 검증한다.
- **0512**(portable LIKE 정책): 2절이 위임한 대소문자 비구분 검색(`ILIKE`
  대체)의 구체적 쿼리 패턴을 확정한다.

## 관련 문서

- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md#4-collation-매트릭스) —
  이 문서가 확정한 문자셋/collation 항목들의 원출처.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록) —
  이 문서가 대체 방식을 구체화한 `ILIKE` 금지 항목.
- [Portable ID Column Policy](portable-id-column-policy.md) — 3절이 확인하는
  ID 문자열 형식 규칙.
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  같은 컬럼 정책 계열(naming → id → timestamp → collation)의 앞 단계 문서.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — 이
  정책이 다루는 컬럼들의 이름 규칙.
- [Persistence Boundaries](persistence-boundaries.md) — 이 정책의 실제 적용
  사례(`document.normalized_title`)와 정규화된 컬럼 패턴.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
