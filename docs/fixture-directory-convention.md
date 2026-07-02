# Fixture Directory Convention

이 문서는 `docs/portability-glossary.md` 가 정의한 **Fixture**(언어 독립
입력/기대출력 데이터)를 어느 디렉터리에 두는지 고정한다. Phase A: PHP
Replacement Contract, 0351-0390 의 산출물이며, JSON 구조 자체(입력/기대출력/
에러 필드 등)는 이 문서가 아니라 이후 태스크(0369, Add cross-language
fixture schema)가 정한다 — 이 문서는 "무엇을 어디에 두는가"만 고정한다.

## 두 종류의 fixture 디렉터리

### 1. 모듈 전용 fixture — `tests/modules/<module>/fixtures/`

한 모듈의 공개 서비스 동작(parity)만 검증하는 fixture는 그 모듈 테스트
디렉터리 아래 `fixtures/` 서브디렉터리에 둔다. 이 위치는 이미
`docs/module-contract-manifest-schema.md` 의 `fixtures.path` 필드와 각
`src/modules/<module>/manifest.json` 이 고정하고 있다 — 이 문서는 그 값을
바꾸지 않고 그대로 따른다.

- 예: `tests/modules/document/fixtures/`, `tests/modules/acl/fixtures/`.
- 이 디렉터리의 fixture는 정확히 하나의 모듈에 속하며, 그 모듈의 Python
  구현과 (이후) PHP 구현이 같은 파일을 공유한다.
- 모듈 이름은 `docs/modules.md` 가 정의한 12개 모듈
  (`document`, `revision`, `parser`, `render`, `acl`, `discussion`,
  `search`, `cache`, `jobs`, `user`, `admin`, `audit`)과 일치해야 한다.

### 2. 공유 fixture — `tests/fixtures/`

특정 모듈 하나에 속하지 않는 fixture(여러 모듈이 함께 참조하는 스키마,
DB 시드 데이터 등)는 저장소 최상위 `tests/fixtures/` 아래 둔다.

- 예: 교차언어 fixture 자체의 JSON Schema(0369), 여러 모듈에 걸친 DB
  이식 시드 데이터(0490).
- 이 디렉터리는 어떤 한 모듈의 `manifest.json` `fixtures.path` 값과도
  겹치지 않는다 — 모듈 전용 데이터를 여기 두지 않는다.
- 하위 구조가 필요하면 용도별 서브디렉터리(예: `tests/fixtures/schema/`,
  `tests/fixtures/seed/`)로 나눈다. 이 문서는 그 서브디렉터리 이름까지
  선점하지 않으며, 실제로 만드는 태스크가 정한다.

두 디렉터리 중 어디에 둘지 애매하면 기준은 다음과 같다: fixture가 오직
한 모듈의 `service.py` 공개 메서드 입출력만 검증하면 모듈 전용
(`tests/modules/<module>/fixtures/`)에 두고, 두 개 이상의 모듈이나 모듈
경계 밖(DB 시드, fixture 형식 자체)을 다루면 공유(`tests/fixtures/`)에
둔다.

## 형식: JSON 기본

두 디렉터리 모두 fixture 파일은 **JSON을 기본 형식**으로 한다
(`docs/module-contract-manifest-schema.md` 의 `fixtures.format` 필드가
이미 `"json"`으로 고정되어 있는 것과 동일한 이유: Python `json` 표준
라이브러리와 PHP `json_decode`가 같은 구조를 언어 독립적으로 읽을 수
있다).

- 새 fixture는 `.json` 확장자를 쓴다.
- `tests/modules/render/fixtures/*.html` 처럼 이 규칙 이전에 만들어진
  언어 종속 스냅샷 fixture는 이 문서가 소급 적용해 강제로 변환하지
  않는다 — 해당 모듈을 공용 fixture 기반으로 바꾸는 것은 별도
  태스크(0372, Convert render tests to shared fixtures)의 범위다.

## 파일 이름 규칙

- 파일 이름은 `snake_case`를 쓰고 시나리오를 설명하는 이름을 붙인다
  (`tests/modules/render/fixtures/simple_paragraph.html` 과 같은 기존
  관례를 JSON에도 그대로 적용한다).
- 한 디렉터리에 fixture가 여러 개 쌓이면 `README.md`를 두어 파일 목록과
  각 파일이 다루는 시나리오를 한글로 요약한다
  (`tests/modules/render/fixtures/README.md` 참고).

## 관련 문서

- `docs/portability-glossary.md` — Fixture 용어 정의.
- `docs/module-contract-manifest-schema.md` — 모듈별 `fixtures.path`/
  `fixtures.format` 필드.
- `docs/php-replacement-strategy.md` — fixture가 readiness gate에서
  하는 역할.
