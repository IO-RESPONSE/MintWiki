# Cross-Language Fixture Schema

이 문서는 `docs/fixture-directory-convention.md` 가 위치만 고정하고 남겨둔
Python/PHP 공용 fixture 의 JSON 구조 자체를 고정한다. Phase A: PHP
Replacement Contract, 0351-0390 의 산출물이다.

fixture 는 `docs/portability-glossary.md` 가 정의한 **Fixture**(하나의
입력과 그에 대응하는 기대 출력을 언어 독립 형식으로 고정한 데이터)의 실제
파일 형식이다. `tests/modules/<module>/fixtures/` 와 `tests/fixtures/`
어느 위치에 두든(`docs/fixture-directory-convention.md` 참고) 이 문서가
정한 구조를 따른다.

## 스키마 정의 위치

기계 판독 가능한 JSON Schema(draft 2020-12)는
`tests/fixtures/schema/cross_language_fixture.schema.json` 에 있다. 이후
런너(0387 PHP parity 테스트 계획, 0406/0407 PHP fixture runner, 0425 PHP
shared fixture loader 등)는 이 파일을 기준으로 fixture 를 읽고 검증한다.

## 최상위 구조: `input` / `expected` / `errors`

fixture 파일 하나는 정확히 아래 4개 최상위 필드만 가진 JSON 객체다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `schema_version` | string | 필수 | 이 문서가 따르는 스키마 버전. 현재 `"1.0"` 고정. |
| `description` | string | 선택 | fixture 가 다루는 시나리오에 대한 한글 요약. |
| `input` | any | 필수 | 검증 대상 서비스 공개 메서드에 그대로 전달하는 입력값. |
| `expected` | any \| null | 필수 | `input` 실행 결과로 Python/PHP 구현이 동일하게 반환해야 하는 값. |
| `errors` | string[] | 필수 | `input` 실행 시 기대되는 안정적인 error code 목록. |

### `input`

- `docs/module-contract-manifest-schema.md` 의 `service.public_methods`
  에 나열된 메서드 하나에 그대로 전달할 수 있는 형태로 적는다.
- 타입은 메서드마다 다르므로(문자열, 객체, 배열 등) 이 스키마는 `input`
  의 내부 타입을 제한하지 않는다.

### `expected`

- 성공이 기대되는 fixture(즉 `errors` 가 빈 배열)는 `input` 을 실행했을
  때 나와야 하는 실제 반환값을 그대로 적는다.
- 실패가 기대되는 fixture(`errors` 가 비어있지 않음)는 `expected` 를
  `null` 로 둔다 — 실패 케이스에서 부분 반환값을 기대값으로 오인하지
  않기 위함이다.

### `errors`

- 성공이 기대되면 빈 배열 `[]` 을 쓴다.
- 실패가 기대되면 `docs/php-replacement-strategy.md` 가 요구하는 안정적인
  error code(예: `document.empty_title`) 를 담는다. 이후 태스크(0373 Add
  portable exception code policy, 0374 Add document error codes 등)가
  실제 코드 목록을 채운다 — 이 문서는 필드 자체의 존재와 타입(문자열
  배열)만 고정한다.
- 에러 메시지 문자열은 담지 않는다. `docs/php-replacement-strategy.md` 의
  "예외 메시지 문자열 비교로 에러 종류를 식별하는 것" 금지 원칙과 같은
  이유다: 메시지는 언어/로케일마다 달라질 수 있지만 code 는 그렇지 않다.

## `expected` 와 `errors` 는 상호 배타적이다

한 fixture 는 성공 케이스이거나 실패 케이스 중 하나만 나타낸다.

- 성공 케이스: `expected` 는 실제 반환값, `errors` 는 `[]`.
- 실패 케이스: `expected` 는 `null`, `errors` 는 원소 1개 이상인 배열.

두 필드를 동시에 채우지 않는다 — 하나의 입력 실행은 성공 아니면 실패
중 하나의 결과만 낸다.

## 예시

성공 케이스:

```json
{
  "schema_version": "1.0",
  "description": "제목 앞뒤 공백을 제거한다.",
  "input": { "title": "  Example Title  " },
  "expected": { "title": "Example Title" },
  "errors": []
}
```

실패 케이스:

```json
{
  "schema_version": "1.0",
  "description": "빈 제목은 거부된다.",
  "input": { "title": "" },
  "expected": null,
  "errors": ["document.empty_title"]
}
```

## 관련 문서

- `docs/fixture-directory-convention.md` — fixture 를 어느 디렉터리에
  두는지.
- `docs/portability-glossary.md` — Fixture 용어 정의.
- `docs/module-contract-manifest-schema.md` — 모듈별 `fixtures.path`/
  `fixtures.format` 필드.
- `docs/php-replacement-strategy.md` — error code 정책과 fixture 가
  readiness gate 에서 하는 역할.
- `tests/fixtures/schema/cross_language_fixture.schema.json` — 기계
  판독 가능한 JSON Schema.
