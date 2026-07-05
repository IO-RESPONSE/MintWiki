# 0705 NamuMark block parser and headings

## Goal

NamuMark **블록 문법**(제목, 목록, 표, 구분선, 인용, 문단)을 파싱해 인라인 파서(0704)와 조립하고, 목차(TOC) 생성을 위한 제목 목록을 수집한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Modules/Parser (블록 파서)
- php/tests/Modules/Parser

## Acceptance Criteria

- 다음 블록 문법을 처리한다: 제목 `== 제목 ==`~`====== 제목 ======`(레벨 1~5, 나무위키식)→`<h2>`~`<h6>` + 각 제목을 앵커 id와 함께 수집, 순서없는 목록 `* 항목`(중첩 포함)→`<ul>`, 순서있는 목록 `1. 항목`→`<ol>`, 표 `||셀||셀||`→`<table>`(행/열), 구분선 `----`→`<hr>`, 인용 `> 인용`→`<blockquote>`, 빈 줄로 구분되는 문단→`<p>`.
- 각 블록의 텍스트는 0704 인라인 파서를 거쳐 렌더된다(예: 표 셀·목록 항목 안의 `'''굵게'''` 동작).
- 수집한 제목 목록(레벨 + 텍스트 + 앵커 id)을 `RenderResult.headings()`로 노출할 수 있는 형태로 반환한다 — 0706이 이걸로 TOC를 만든다.
- 모든 리터럴 텍스트는 이스케이프된다(0704 계약 유지). 앵커 id는 안전한 문자로 slug화(중복 시 -2 등 suffix).
- php 테스트로 각 블록·중첩 목록·표·제목수집·인라인 조합을 검증한다.

## Out of Scope

- TOC HTML 렌더와 문서 뷰 통합 — 0706.
- 각주/카테고리 — 필요 시 후속(이 태스크는 headings 우선).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

0704 인라인 파서에 의존. 출력은 문서 본문 HTML + 제목 컬렉션. `RenderResult` 시그니처(`headings()`)에 맞춰 렌더러(0706)가 조립하기 쉽게 자료구조를 반환한다. 순수 PHP, `MintWiki\Parser`.
