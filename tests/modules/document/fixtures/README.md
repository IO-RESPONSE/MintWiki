# Document Fixtures

`modules.document.title.normalize_title` 의 제목 정규화 동작을 검증하는
교차언어(cross-language) fixture다. 형식은
`docs/cross-language-fixture-schema.md` 가 고정한
`schema_version`/`input`/`expected`/`errors` 구조를 따르며, `input.title` 을
`normalize_title` 에 그대로 전달했을 때 나와야 하는 결과를 담는다. 이후 PHP
포트(0426 Add PHP document fixture parity tests)가 같은 파일을 재사용한다.

## 파일 목록

- `trims_leading_and_trailing_spaces.json` — 앞뒤 공백 제거.
- `trims_tabs_and_newlines.json` — 앞뒤 탭/개행 제거.
- `collapses_internal_whitespace.json` — 내부 연속 공백을 단일 공백으로 축소.
- `collapses_internal_whitespace_with_trimming.json` — 양 끝 제거와 내부 축소를 동시에 수행.
- `preserves_korean_title.json` — 한글 제목의 공백만 제거하고 내용은 유지.
- `preserves_mixed_language_and_special_characters.json` — 혼합 언어/특수문자/숫자 제목 정규화.
- `rejects_empty_string.json` — 빈 문자열 거부 (`document.empty_title`).
- `rejects_whitespace_only.json` — 공백만 있는 제목 거부.
- `rejects_mixed_whitespace_only.json` — 탭/개행만 있는 제목 거부.
