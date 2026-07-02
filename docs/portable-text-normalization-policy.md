# Portable Text Normalization Policy

이 문서는 사용자 입력 텍스트를 "정규화"하거나 대소문자 구분 없이
비교할 때 어떤 Unicode 정규화 폼과 case 정책을 쓰는지 고정한다.
Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

`src/modules/document/title.py` 의 `normalize_title` 은 이미 주변
공백을 제거하고 내부 공백을 단일 공백으로 축소해 `normalized_title`
을 만들고 있다. `src/modules/render/heading.py`,
`src/modules/render/css_sanitizer.py`,
`src/modules/render/simple_table.py`,
`src/modules/render/url_sanitizer.py`,
`src/modules/search/in_memory_adapter.py` 는 각각 슬러그 생성, 위험
키워드 매칭, 속성명 매칭, URL 스킴 매칭, 검색어 매칭을 위해
`str.lower()` 를 쓰고 있다. 이 문서는 이 관행들을 일반 정책으로
고정해 Python/PHP 양쪽 구현이 같은 문자열 비교 결과를 내도록 한다.

## 공백 정규화: 트림 + 내부 공백 단일 공백 축소

- "정규화된" 값(`normalized_title` 등 `normalize_*`/`normalized_*`
  이름을 가진 값)은 앞뒤 공백을 제거하고, 내부에 연속된 공백 문자(스페이스,
  탭, 개행 포함)를 단일 스페이스(` `, U+0020)로 축소한다.
  `normalize_title` 의 `" ".join(title.split())` 이 이미 이 규칙을
  따른다 — Python `str.split()` 인자 없이 호출하면 모든 공백 문자
  종류를 구분자로 취급하고 빈 조각을 버린다.
- PHP 구현은 동일한 결과를 내기 위해 `trim()` 만으로는 부족하다 —
  내부 연속 공백 축소를 위해 `preg_replace('/\s+/u', ' ', trim($s))`
  형태(Unicode 모드 `u` 플래그 필수)를 쓴다.

## Unicode 정규화 폼: NFC

- 저장하거나 비교하는 모든 텍스트는 Unicode 정규화 폼 C(NFC,
  Canonical Composition)로 통일한다. 조합 문자 시퀀스(예: `e` +
  결합 악센트 U+0301)와 미리 조합된 문자(예: `é`, U+00E9)는 화면에
  같아 보여도 코드포인트 시퀀스가 다르며, NFC 로 정규화하지 않으면
  같은 제목을 입력해도 `normalized_title` UNIQUE 제약을 우회해 두
  문서가 생성되거나, 검색어가 색인된 텍스트와 일치하지 않을 수 있다.
- 정규화 순서는 공백 정규화보다 먼저다: 원본 텍스트 → NFC 정규화 →
  공백 트림/축소. NFC 변환이 공백 문자 자체를 바꾸지는 않지만, 순서를
  고정해 두 언어 구현이 동일한 중간 단계를 거치게 한다.
- Python 구현은 `unicodedata.normalize("NFC", s)` 를 쓴다. PHP 구현은
  표준 확장에 없으므로 `intl` 확장의 `Normalizer::normalize($s,
  Normalizer::FORM_C)` 를 쓴다 — `intl` 없이 배포하는 환경은 이 정책을
  만족할 수 없으므로 PHP 골격 태스크(Phase B)에서 `intl` 을 필수
  의존성으로 명시해야 한다.
- 이 문서를 작성하는 시점에 `normalize_title` 은 NFC 정규화를 아직
  적용하지 않는다 — 이 문서가 고정하는 정책에 따르면 이후 수정 시
  공백 정규화 앞에 NFC 변환 단계를 추가해야 한다. 기존 코드를 이
  태스크에서 바로 고치지는 않는다(Out of Scope).

## Case 정책: 저장/식별용은 보존, 비교/매칭용은 폴딩

두 가지 서로 다른 목적을 구분한다.

- **저장·식별용 정규화**(`normalized_title` 등, 문서 식별 목적):
  대소문자를 그대로 보존한다. `normalize_title` 은 case-folding을
  하지 않으며, 이 문서는 그 관행을 고정한다 — 대소문자만 다른 제목
  (`"Wiki"`, `"wiki"`)은 서로 다른 문서로 취급되어야 한다. Unicode
  case-folding은 정보 손실적 변환(예: 독일어 `ß` → `ss`)이라 원본
  식별값을 복원할 수 없게 만들 수 있으므로 식별용 값에는 적용하지
  않는다.
- **비교·매칭용 정규화**(검색어 매칭, 위험 키워드/속성명/URL 스킴
  매칭처럼 case를 무시하고 동등성만 확인하는 경우): 두 문자열을
  case-insensitive 하게 비교하기 전에 `str.casefold()` 로 변환한다.
  `str.lower()` 가 아니라 `str.casefold()` 를 쓰는 이유는 `lower()`
  가 처리하지 못하는 경우(독일어 `ß`/`SS`, 그리스어 최종형 시그마
  `ς`/`Σ`)를 `casefold()` 는 동일하게 접어 매칭 누락을 줄이기
  때문이다.
- `heading.py` 의 슬러그 생성(`generate_heading_id`)은 예외다 — 이는
  case-insensitive 비교가 아니라 ASCII 전용 HTML id 슬러그를 만드는
  것이 목적이므로, `str.lower()` 로 소문자화한 뒤 `[^a-z0-9-]` 정규식
  으로 비-ASCII 문자를 제거하는 현재 방식을 그대로 유지한다. 이 문서의
  case-folding 정책은 슬러그 생성처럼 출력 문자셋을 의도적으로
  제한하는 코드에는 적용하지 않는다.
- PHP 구현에서 case-insensitive 비교를 할 때는 `strtolower()`(바이트
  단위, ASCII 외 문자에서 깨짐)를 쓰지 않는다 — Python `str.lower()`/
  `str.casefold()` 와 동등한 Unicode 인식 동작을 얻으려면
  `mb_strtolower($s, 'UTF-8')` 를 쓴다. `mb_strtolower` 는 `casefold()`
  가 접는 모든 특수 case(독일어 `ß` 등)를 접지는 않지만, 이 문서가
  다루는 대상(제목/속성명/URL 스킴 등 대부분 ASCII 또는 단순 Unicode
  텍스트)에서는 실용적으로 충분한 근사치로 채택한다 — PHP 표준
  확장만으로 `casefold()` 와 완전히 동일한 결과를 내는 함수는 없다.

## DB collation: normalized_title UNIQUE는 대소문자를 구분해야 한다

- PostgreSQL 기본 collation(`C`/`en_US.UTF-8` 등 대부분의 로케일)은
  문자열 비교와 UNIQUE 제약을 대소문자 구분(case-sensitive)으로
  평가한다. 반면 MariaDB/MySQL 은 컬럼에 명시적으로 지정하지 않으면
  서버/DB 기본 charset의 기본 collation(흔히
  `utf8mb4_general_ci`/`utf8mb4_unicode_ci`, 접미사 `_ci` = case
  insensitive)을 쓰며, 이 collation 아래에서는 `"Wiki"` 와 `"wiki"`
  가 UNIQUE 제약상 같은 값으로 취급되어 두 번째 INSERT가 실패한다.
  같은 스키마와 같은 애플리케이션 코드로 PostgreSQL에서는 성공하는
  삽입이 MariaDB에서는 실패하는 이식성 문제가 생긴다.
- 이 문서는 위 Case 정책("저장·식별용 정규화는 대소문자를 보존한다")
  이 DB 계층에서도 그대로 성립하도록, `document.normalized_title`
  컬럼(과 향후 추가되는 대소문자 구분이 필요한 UNIQUE 텍스트 컬럼)에
  대소문자 구분 collation을 명시적으로 지정하도록 고정한다: MariaDB는
  `utf8mb4_bin` 또는 `utf8mb4_0900_as_cs`(대소문자·악센트 모두 구분)
  같은 `_bin`/`_as_cs` collation을, PostgreSQL은 기본 collation이 이미
  대소문자를 구분하므로 별도 지정이 필요 없다.
- 컬럼 collation 지정 자체(ORM 마이그레이션 문법, 구체 DDL)는 이
  문서의 범위가 아니다 — `docs/persistence-boundaries.md` 와 Phase C
  의 portable schema 태스크가 실제 DDL을 다룰 때 이 정책(대소문자
  구분 collation 사용)을 반영해야 한다.

## 이 문서가 하지 않는 것

- 전문 검색(full-text search)의 토크나이징, 형태소 분석, 언어별
  stemming 규칙을 다루지 않는다(`docs/search-adapter-design.md` 의
  범위).
- `heading.py` 의 슬러그 생성 알고리즘(비-ASCII 문자 처리 방식)을
  바꾸지 않는다.
- 기존 코드(`normalize_title` 의 NFC 미적용, `render`/`search` 모듈의
  `lower()` 호출)를 이 태스크에서 수정하지 않는다 — 정책만 고정하며,
  실제 코드 변경은 각 모듈이 이 계약을 참조하는 이후 태스크의 범위다.
- DB 컬럼 collation의 구체 DDL 문법을 정하지 않는다
  (`docs/persistence-boundaries.md`/Phase C 의 범위).

## 관련 문서

- `docs/php-replacement-strategy.md` — ANSI SQL + MariaDB 호환 기본
  경로 원칙과 두 DB가 같은 스키마를 공유해야 한다는 전제.
- `docs/portable-id-policy.md` — 대비되는 정책: `id` 값은 정규화나
  case 변환의 대상이 아니라 애플리케이션이 생성한 불투명한 문자열로
  그대로 저장/비교된다.
- `docs/portable-sorting-contract.md` — DB 기본값 차이(NULL 정렬)를
  명시적으로 고정한 선례 — 이 문서의 collation 절이 같은 구조를
  따른다.
- `docs/persistence-boundaries.md` — `normalized_title` 컬럼의
  `String(500) NOT NULL UNIQUE` 정의.
- `docs/search-adapter-design.md` — 검색어 매칭이 이 문서의 case
  정책을 적용받는 지점.
- `docs/portability-glossary.md` — Contract/Adapter 용어 정의.
