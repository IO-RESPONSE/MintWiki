# 0706 NamuMark renderer and document view integration

## Goal

0704/0705 파서를 `DocumentRenderer` 구현체 `NamuMarkDocumentRenderer`로 조립하고, 문서 보기(`GET /wiki/{title}`)가 저장된 위키 문법을 실제 HTML(+ 목차)로 렌더하도록 프론트 컨트롤러의 렌더러를 교체한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/src/Modules/Render (NamuMarkDocumentRenderer)
- php/public/index.php (렌더러 주입 교체)
- php/src/Ui/DocumentViewPage.php (TOC 표시, 필요 시)
- php/tests

## Acceptance Criteria

- `NamuMarkDocumentRenderer implements DocumentRenderer`를 구현한다 — `render(string $source): RenderResult`가 0705 블록 파서를 호출해 본문 HTML과 `headings()`를 채운다. `links()`도 채울 수 있으면 채운다.
- 제목 컬렉션으로 **목차(TOC)** HTML을 생성한다(제목 2개 이상일 때 노출, 각 항목이 본문 앵커로 점프). TOC는 `RenderResult` 메타 또는 렌더러 출력에 포함하되, `DocumentViewPage`가 본문 상단에 배치할 수 있게 한다.
- `index.php`에서 문서 보기 렌더러를 `PlainTextDocumentRenderer` → `NamuMarkDocumentRenderer`로 교체한다. `GET /wiki/{title}`가 이제 `'''굵게'''`·`[[링크]]`·표·제목을 HTML로 보여준다.
- 렌더 결과는 XSS 안전(파서 계약 유지)하며, 스킨 CSS로 본문/표/TOC가 브랜드 톤에 맞게 보이도록 필요한 assets를 추가한다.
- php 테스트로 (1) 렌더러가 대표 문서를 올바른 HTML로 변환, (2) TOC 생성/미생성 경계, (3) `/wiki/{title}` 라우트가 렌더된 HTML을 반환함을 검증한다.

## Out of Scope

- 편집 미리보기(0708) — 단, 같은 렌더러를 재사용하도록 설계.
- red link(존재하지 않는 문서 링크 강조)는 여력 되면 포함, 아니면 후속.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`Modules/Render`에 인터페이스·`PlainTextDocumentRenderer`·`RenderResult` 이미 있음. `DocumentViewPage`는 생성자에서 `?DocumentRenderer`를 받으므로 주입 지점만 바꾸면 됨(기본값도 NamuMark로). 이 렌더러는 0708 미리보기와 공유된다.
