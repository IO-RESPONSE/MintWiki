# 0690 Render NamuWiki-style top navigation bar

## Goal

`Navigation`/`NavigationItem` 모델(현재 데이터만 보유하고 HTML을 만들지 않음)을 실제 상단 네비게이션 바 HTML로 렌더링하는 컴포넌트를 만들고, 나무위키풍 상단바(브랜드 로고 → 홈, 검색창, 로그인/로그아웃 상태 링크)를 출력한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/src/Ui (Navigation 렌더러 또는 Navigation 렌더 메서드, NavigationBar 등)
- php/tests/Ui

## Acceptance Criteria

- `Navigation`의 항목들을 `<nav>` 상단바 HTML로 렌더링하는 방법을 추가한다(별도 `NavigationBar`/`SkinHeader` 컴포넌트 또는 기존 컴포넌트 확장 — 기존 코드 관례에 맞게 선택).
- 상단바는 나무위키풍으로 (1) 좌측 브랜드 로고 텍스트 "MintWiki"가 `/`로 링크, (2) 검색 입력(제출 시 문서 검색), (3) 우측에 로그인 상태에 따라 "로그인" 또는 "로그아웃(사용자명)" 링크를 보여준다.
- 현재 경로/권한에 따른 항목 활성화·필터링은 기존 `Navigation` API(`isActive`, 권한 필터)를 사용한다.
- 모든 사용자 입력/출력은 기존 `Escaper`로 이스케이프한다(XSS 방지).
- 0689의 브랜드 토큰(`--color-brand`)으로 상단바를 스타일링한다(필요 CSS는 assets에 추가).
- php 테스트로 로그인/비로그인 각각의 상단바 렌더 결과(로고 링크, 검색, 로그인/로그아웃 표시, 이스케이프)를 검증한다.

## Out of Scope

- Layout 통합 및 전체 페이지 반영(0691에서).
- 문서 상단 탭(0692), 사이드바(0694).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `src/Ui/Navigation.php`(불변 컬렉션, `items()`/`isActive`/권한 필터), `src/Ui/NavigationItem.php`(`href`/`label`/`id`/`requiredPermission`/`isActive`). 로그인 상태는 세션(0686 `PhpSessionAdapter`)에서 얻는다. 렌더러는 순수 함수적으로 HTML 문자열을 반환해 Layout(0691)이 헤더에 주입할 수 있게 한다.
