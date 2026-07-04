# 0693 Rebuild home as a NamuWiki-style front page

## Goal

현재 검색 폼만 있는 홈(`GET /`)을 나무위키식 프론트/대문 페이지로 개편한다: 스킨(상단바/푸터) 위에 대문 콘텐츠(검색 + 최근 편집된 문서 목록 + 안내 영역)를 나무위키풍으로 배치한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/public/index.php
- php/src/Ui (FrontPage/HomePage 컴포넌트 신설 가능)
- php/public/assets/css
- php/tests

## Acceptance Criteria

- 홈이 인라인 HTML 문자열 대신 전용 프론트페이지 컴포넌트(예: `FrontPage`)로 렌더링되며 0691 스킨(헤더/푸터)을 사용한다.
- 대문에 (1) 눈에 띄는 검색 영역, (2) 최근 편집된 문서 목록(있으면), (3) 사이트 소개/안내 블록을 나무위키풍으로 배치한다.
- 최근 문서 목록은 기존 문서/리비전 저장소(예: Document/Revision `Service`)를 통해 조회하며, DB 미설정/비어있음일 때는 안전하게 빈 상태 안내를 보여준다(러너에서 실패하지 않도록).
- 브랜드 토큰(0689)으로 스타일링하고 반응형에서 깨지지 않는다.
- php 테스트로 프론트페이지 렌더(검색 영역, 최근 문서 목록 유/무 상태, 빈 상태 안내)를 검증한다.

## Out of Scope

- 사이드바/모바일 세부 최적화(0694), NamuMark 렌더링.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 홈은 `index.php`의 `GET '/'`에서 `<form action="/api/documents/by-title">` 인라인. 최근 문서는 기존 Document/Revision 모듈의 조회 API를 사용하고, 범위가 커지면 최근변경 전용 라우트는 후속 태스크로 분리한다.
