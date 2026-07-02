# Cross-Language Fixture Schema

이 디렉터리는 Python/PHP 공용 fixture 파일이 따라야 하는 JSON Schema와,
그 스키마를 만족하는 예시 fixture를 둔다. 필드 의미는
`docs/cross-language-fixture-schema.md` 가 고정한다.

## 파일 목록

- `cross_language_fixture.schema.json` — 기계 판독 가능한 JSON Schema
  (draft 2020-12). `schema_version`/`input`/`expected`/`errors` 최상위
  구조를 강제한다.
- `examples/success_example.json` — 성공 케이스 예시. `expected` 에 실제
  반환값을, `errors` 에 빈 배열을 담는다.
- `examples/error_example.json` — 실패 케이스 예시. `expected` 를
  `null` 로, `errors` 에 error code 1개 이상을 담는다.
