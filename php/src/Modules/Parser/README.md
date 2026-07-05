# php/src/Modules/Parser

`MintWiki\Parser` namespace 골격. 태스크 0399 에서 빈 디렉터리로
추가되었다.

namespace 이름은 `docs/php-namespace-mapping.md` 가 고정한 값을 따른다
(Python `modules.parser` → PHP `MintWiki\Parser`). 대응하는 계약
manifest 는 `src/modules/parser/manifest.json` 이다. manifest의
`port.status`는 블록 파서(`PlainTextBlockParser`, 0705)가 아직 없으므로
여전히 `not_started`다 — `tests/Modules/Parser/ParityPlaceholderTest.php`가
이를 가드한다.

## InlineParser (태스크 0704)

`InlineParser::parse(string $source): InlineParseResult`는 NamuMark풍
**인라인** 문법(굵게/기울임/밑줄/취소선/코드/내부 링크/외부 링크)만 HTML
조각으로 변환한다. 블록 분리(제목/목록/표/문단, 0705)와 최종 렌더 조립
(0706)은 다루지 않는다. `InlineParseResult::links()`는 발견한 내부 링크
문서 제목을 수집해, 이후 렌더러가 `RenderResult::links()`를 채우는 데
그대로 쓸 수 있게 한다. 이스케이프는 `MintWiki\Ui\Escaper`를 재사용한다.

## BlockParser (태스크 0705)

`BlockParser::parse(string $source): BlockParseResult`는 NamuMark풍
**블록** 문법(제목/목록/표/구분선/인용/문단)을 줄 단위로 나눠 HTML로
조립한다. 각 블록의 텍스트는 `InlineParser`에 위임해 렌더링하므로 표 셀,
목록 항목, 인용문, 제목 안에서도 굵게/링크 등 인라인 문법이 그대로
동작한다.

- 제목 `== 제목 ==`~`====== 제목 ======`(레벨 1~5, 나무위키식)→`<h2>`~`<h6>`.
  각 제목은 마크업 기호를 걷어낸 순수 텍스트와, 그 텍스트를 slug화한 앵커
  id(중복 시 `-2`, `-3`, ... 접미사)를 `BlockParseResult::headings()`
  (`list<array{level, text, id}>`)로 수집한다. 이 shape은
  `MintWiki\Render\RenderResult::headings()`가 기대하는 shape과 동일해,
  0706의 렌더러가 그대로 옮겨 담을 수 있다.
- 순서없는 목록 `* 항목`(`**`, `***`, ...로 중첩)→`<ul>`, 순서있는 목록
  `1. 항목`→`<ol>`, 표 `||셀||셀||`→`<table>`, 구분선 `----`→`<hr>`, 인용
  `> 인용`→`<blockquote>`, 빈 줄로 구분되는 그 외 텍스트→`<p>`.
- `BlockParseResult::links()`는 모든 블록에서 발견된 내부 링크 문서 제목을
  모아 `InlineParseResult::links()`와 같은 방식으로 노출한다.

TOC HTML 렌더와 문서 뷰 통합, 각주/카테고리 추출은 이 태스크의 범위가
아니다(0706 이후).
