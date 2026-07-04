# 0692 Add NamuWiki-style document header and action tabs

## Goal

`DocumentViewPage`(및 편집/문서 페이지)가 나무위키식 문서 헤더를 렌더링하도록 한다: 문서 제목(H1) + 액션 탭(읽기·편집·역사·토론) + 마지막 편집 정보. 탭은 해당 문서의 라우트로 링크한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/src/Ui/DocumentViewPage.php
- php/src/Ui (필요 시 공용 DocumentHeader/ActionTabs 컴포넌트)
- php/public/index.php
- php/public/assets/css
- php/tests/Ui

## Acceptance Criteria

- 문서 보기 화면 상단에 나무위키식 액션 탭을 렌더링한다: "읽기"(`/wiki/{title}`), "편집"(`/wiki/{title}/edit`), "역사"(`/wiki/{title}/history`), "토론"(`/wiki/{title}/discussion`). 현재 화면에 해당하는 탭을 활성 표시한다.
- 아직 라우트가 없는 탭(역사/토론)도 링크는 나무위키 관례대로 노출하되, 대상 라우트가 없으면 클릭 시 앱의 404 처리로 이어져도 된다(이 태스크에서 라우트 구현은 하지 않음).
- 문서 제목 헤더와 "마지막 편집" 등 메타 정보를 0689 브랜드 토큰으로 나무위키풍으로 스타일링한다.
- 문서가 없을 때(404 경로)도 제목 + "이 문서는 아직 없습니다. 편집하여 만들 수 있습니다" 안내와 "편집" 탭을 보여준다(나무위키 빈 문서 UX). 기존 `EmptyState` 컴포넌트가 있으면 재사용한다.
- 모든 출력은 `Escaper`로 이스케이프한다.
- php 테스트로 탭 링크/활성표시/빈 문서 안내/이스케이프를 검증하고, 기존 DocumentViewPage 테스트가 계속 통과한다.

## Out of Scope

- 역사/토론 라우트 및 기능 구현(후속 wiring 태스크).
- NamuMark 본문 렌더링.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `src/Ui/DocumentViewPage.php`(`render(...)`, Layout 재사용), `src/Ui/DocumentHistoryPage.php`/`DiscussionPage.php`(페이지 클래스는 있으나 라우트 미연결). 탭 활성 판단은 현재 경로로 한다. 문서 링크 제목은 URL 인코딩을 고려한다.
