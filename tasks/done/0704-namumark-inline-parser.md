# 0704 NamuMark inline parser

## Goal

나무위키풍(NamuMark) **인라인 문법**을 HTML 조각으로 변환하는 파서를 `Modules/Parser`에 구현한다. 블록 파서(0705)와 렌더러(0706)가 이것을 조립한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Modules/Parser (인라인 파서)
- php/tests/Modules/Parser

## Acceptance Criteria

- 다음 인라인 문법을 HTML로 변환하는 순수 함수/클래스를 구현한다: `'''굵게'''`→`<strong>`, `''기울임''`→`<em>`, `__밑줄__`→`<u>`, `~~취소선~~`(또는 `--취소선--`)→`<del>`, `[[문서]]`/`[[문서|표시문구]]`→내부 링크(`/wiki/{rawurlencode(title)}`), `[[http... 표시]]`/`[http...]`→외부 링크, `` `코드` ``→`<code>`.
- **XSS 안전**: 원문의 모든 리터럴 텍스트는 기존 `Escaper`로 이스케이프한 뒤에만 마크업을 씌운다. 사용자 입력이 속성/URL로 들어갈 때도 이스케이프한다. 원문에 든 `<`,`>`,`&`,따옴표가 절대 raw로 새지 않아야 한다.
- 내부 링크는 문서 제목만 추출해 반환값 메타(존재/부재 판정은 렌더러가)로 노출할 수 있게 하거나, 최소한 링크 리스트를 수집 가능한 형태로 설계한다(`RenderResult.links()` 채우기 준비).
- 중첩(예: `'''[[링크]]'''`)과 경계 케이스(짝 안 맞는 마크업은 리터럴로)를 합리적으로 처리한다.
- php 테스트로 각 문법·중첩·이스케이프·짝 불일치를 검증한다.

## Out of Scope

- 블록 요소(제목/목록/표/문단) — 0705.
- 문서 존재여부에 따른 red link 스타일 — 0706.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`Modules/Parser`는 현재 README만 있는 빈 모듈. 렌더 계약은 `Modules/Render/DocumentRenderer::render(string): RenderResult`, `RenderResult`는 `html()/headings()/links()/categories()/footnotes()` 보유. 인라인 파서는 그중 html 조각과 links 수집에 기여한다. 도메인 프레임워크 금지(0424) — 순수 PHP. `MintWiki\Parser` 네임스페이스(Modules classmap 예외).
