# HTML Snapshot Fixtures

이 디렉토리는 렌더 모듈의 다양한 렌더링 시나리오에 대한 HTML 스냅샷 픽스처를 포함합니다.

## 픽스처 파일 목록

### 기본 요소

- `simple_paragraph.html` - 단순 문단 렌더링
- `simple_heading.html` - 단순 H1 제목 렌더링
- `simple_list.html` - 비순서 목록 렌더링
- `ordered_list.html` - 순서 목록 렌더링
- `simple_table.html` - 단순 테이블 렌더링

### 링크 및 서식

- `internal_link.html` - 내부 위키 링크 렌더링
- `external_link.html` - 외부 링크 렌더링
- `bold_text.html` - 굵은 텍스트 렌더링
- `italic_text.html` - 기울임 텍스트 렌더링
- `strike_text.html` - 취소선 텍스트 렌더링

### 복합 문서

- `complex_document.html` - 제목, 문단, 목록, 테이블을 포함한 복합 문서

### 보안 및 이스케이프

- `xss_escaped.html` - XSS 공격 시도가 이스케이프된 HTML
- `escaped_characters.html` - 특수 문자(&, <, >, ", ')가 이스케이프된 HTML

### 다국어 및 특수 문자

- `korean_text.html` - 한글 텍스트를 포함한 HTML
- `mixed_language.html` - 영어, 한글, 일본어가 섞인 HTML

### 코드 및 구조

- `code_block.html` - 코드 블록 렌더링

## 사용 방법

이 픽스처 파일들은 테스트에서 예상 출력 값과 비교하거나 렌더 함수의 동작을 검증하기 위해 사용됩니다.

```python
def test_render_paragraph():
    # 픽스처 파일 읽기
    with open('tests/modules/render/fixtures/simple_paragraph.html') as f:
        expected = f.read()
    
    # 실제 렌더링 결과와 비교
    result = render_plain_paragraph("Hello, World!")
    assert result == expected
```

## 추가 픽스처 작성

새로운 렌더링 시나리오에 대한 픽스처를 추가할 때:

1. 렌더링 함수의 예상 출력을 HTML 파일로 저장
2. 파일명은 `snake_case`로 작성하고 `.html` 확장자 사용
3. 이 README에 파일 설명 추가
4. 해당 테스트에서 픽스처 파일 경로 참조

## 공용 교차언어 fixture (`*.json`)

`docs/fixture-directory-convention.md` 는 위 HTML 스냅샷을 소급 변환하지
않되, render 모듈을 공용 fixture 기반으로 바꾸는 작업을 태스크 0372 로
남겨두었다. 이 태스크에서 `docs/cross-language-fixture-schema.md`(0369)
구조를 따르는 `*.json` fixture 를 추가했다. Python/PHP 두 구현이 같은
파일을 공유하며, `tests/modules/render/test_shared_fixtures.py` 가
`tests/fixtures/schema/cross_language_fixture.schema.json` 검증과 실제
렌더 함수 호출 결과 비교를 함께 수행한다.

render 모듈은 단일 진입 함수가 없으므로, 파일명을
`<함수명>__<시나리오>.json` 형식으로 지어 `__` 앞부분으로 대상 함수를
식별한다(`test_shared_fixtures.py` 의 `ASSERTIONS` 디스패치 테이블 참고).
현재는 `docs/module-contract-manifest-schema.md` 의 render 계약 노트가
"render 모듈이 소유한 유일한 살균 경계"로 명시한 세 함수
(`escape_html`/`sanitize_url`/`sanitize_css_value`)와, 그 살균 로직에
의존하며 정규식 문법 차이(Python `re` vs PHP PCRE)가 가장 먼저 드러날 수
있는 `generate_heading_id`, 그리고 대표적인 태그 렌더 함수
(`render_bold`/`render_heading`)만 변환했다. 나머지 render 함수는
이후 태스크에서 필요에 따라 추가 변환될 수 있다.

- `escape_html__xss_script_tag.json` / `escape_html__ampersand_and_quotes.json`
  — HTML 엔티티 이스케이프 경계.
- `sanitize_url__javascript_scheme_blocked.json` /
  `sanitize_url__tab_in_scheme_blocked.json` /
  `sanitize_url__safe_https_with_query.json` — URL 스킴 허용 목록 경계.
- `sanitize_css_value__javascript_url_function_blocked.json` /
  `sanitize_css_value__expression_function_blocked.json` /
  `sanitize_css_value__safe_declaration.json` — CSS 위험 키워드/함수 차단
  경계.
- `generate_heading_id__korean_text_is_stripped.json` /
  `generate_heading_id__collapses_whitespace_and_symbols.json` — 슬러그
  정규식이 비-ASCII 문자를 제거하는 경계 사례.
- `render_bold__escapes_script_injection.json` /
  `render_heading__generates_id_from_spaced_text.json` — 살균 함수를
  감싸는 대표 렌더 함수의 HTML 출력.
