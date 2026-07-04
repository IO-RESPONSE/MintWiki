# 0694 Add sidebar/tools area and responsive mobile skin

## Goal

나무위키식 사이드바/도구 영역(최근 변경, 랜덤 문서, 도구 링크 등)과 반응형 모바일 스킨(좁은 화면에서 상단바 축약/사이드바 접힘)을 추가해 스킨을 완성한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/src/Ui/Layout.php
- php/src/Ui (Sidebar 컴포넌트 신설 가능)
- php/public/assets/css (responsive/mobile)
- php/tests/Ui

## Acceptance Criteria

- 콘텐츠 옆(또는 나무위키처럼 접近 가능한 영역)에 사이드바/도구 링크 영역을 렌더링한다: 최소 "최근 변경", "랜덤 문서", "문서 검색" 등 링크(대상 라우트가 없으면 링크만 노출).
- 데스크톱에서는 본문 옆 또는 상단 도구 메뉴로, 모바일(좁은 폭)에서는 접히거나 상단바 메뉴로 전환되는 반응형 규칙을 CSS로 구현한다.
- 기존 모바일/반응형 자산(예: `responsive-table.css`, 기존 MobileCss 테스트)과 충돌 없이 통합한다.
- 브랜드 토큰(0689)으로 스타일링하고, 본문 폭·가독성이 데스크톱/모바일 모두에서 유지된다.
- php 테스트로 사이드바 렌더와 반응형 관련 CSS 규칙 존재를 검증하고, 기존 UI/모바일 테스트가 계속 통과한다.

## Out of Scope

- 사이드바 각 링크의 실제 기능/라우트 구현(후속 wiring).
- NamuMark 렌더링, TOC(문서 본문 목차)는 NamuMark 단계에서.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `tests/Ui/MobileCssTest.php`, `public/assets/css/responsive-table.css`. 사이드바는 Layout(0691)과 통합한다. TOC(목차)는 본문 파싱이 필요하므로 이 스킨 단계가 아니라 이후 NamuMark 단계에서 다룬다.
