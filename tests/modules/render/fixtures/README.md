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
