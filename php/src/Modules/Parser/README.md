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
