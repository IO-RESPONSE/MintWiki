# Parser Fixtures

`modules.parser.parser.PlainTextBlockParser.parse` 의 파싱 동작을 검증하는
교차언어(cross-language) fixture다. 형식은
`docs/cross-language-fixture-schema.md` 가 고정한
`schema_version`/`input`/`expected`/`errors` 구조를 따르며, `input.source` 를
`parse` 에 그대로 전달했을 때 나와야 하는 `blocks`/`metadata` 를 `expected` 에
담는다. 파서는 예외를 던지지 않고 항상 `ParserResult` 를 반환하므로 모든
fixture 의 `errors` 는 빈 배열이다.

정규식 문법은 Python `re` 와 PHP PCRE 가 다를 수 있으므로(태스크 0371), 이
디렉터리는 각 마크업 패턴에서 정규식 차이가 가장 먼저 드러날 만한 시나리오를
우선 선정했다. 나머지 기존 픽스처(`src/modules/parser/fixtures.py` 의
`ParserFixtureLoader`)는 계속 유지되며, 이후 태스크에서 필요에 따라 추가
변환될 수 있다.

## 파일 목록

- `heading_with_text.json` — 대칭 등호 제목 정규식과 문단 분리.
- `abuse_deep_heading_levels.json` — 등호 7개처럼 비정상적으로 깊은 제목 수준.
- `bold_with_special_chars.json` — 굵은 텍스트 정규식과 `&`, `!` 특수 문자.
- `abuse_empty_bold.json` — 따옴표 6개 연속(빈 굵은 텍스트) 경계 사례.
- `abuse_bold_italic_conflict.json` — 굵은 텍스트와 이탤릭 마커가 겹치는 충돌 사례.
- `links_with_labels.json` — 내부 링크에서 라벨을 제외한 대상만 추출.
- `abuse_mismatched_brackets.json` — 중첩된 여는 대괄호와 하나의 닫는 대괄호.
- `external_link_with_label.json` — 외부 링크에서 URL과 라벨 분리.
- `categories_with_special_chars.json` — `&`, 숫자를 포함한 카테고리명.
- `nowiki_with_special_chars.json` — nowiki 블록의 다른 마크업 토큰 보존.
- `code_with_special_chars.json` — 코드 블록의 다른 마크업 토큰 보존.
- `table_with_colspan_and_alignment.json` — colspan과 정렬 지시자가 결합된 테이블 셀.
