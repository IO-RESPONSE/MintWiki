# 0689 Add mint brand design tokens and NamuWiki-style palette

## Goal

MintWiki 브랜드 색상 `#008485`(민트/틸)을 디자인 토큰에 도입하고, 나무위키풍(밝은 배경 + 좁은 콘텐츠 폭 + 또렷한 링크색)의 기본 팔레트/타이포 토큰을 정리해, 이후 스킨 태스크(0690+)가 일관되게 참조할 기반을 만든다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/public/assets/css/design-tokens.css
- php/public/assets/css/buttons.css
- php/tests/Ui

## Acceptance Criteria

- `design-tokens.css`에 브랜드 색 토큰(`--color-brand: #008485` 및 hover/active용 명암 변형, 대비를 만족하는 on-brand 텍스트색)을 추가한다.
- 나무위키풍 링크색/방문색, 콘텐츠 최대 폭(`--content-max-width`), 헤더 높이 등 스킨에서 재사용할 레이아웃 토큰을 정의한다.
- `buttons.css`의 기본/주요 버튼이 하드코딩 색 대신 브랜드 토큰을 사용하도록 갱신한다.
- 기존 토큰(`--color-bg-*`, `--color-text-*`)은 유지하되 필요한 경우에만 나무위키풍으로 조정한다(회귀 최소화).
- php 테스트로 `design-tokens.css`에 `--color-brand`와 `#008485`가 존재함을 검증하고, 기존 CSS 관련 테스트가 계속 통과한다.

## Out of Scope

- 상단바/문서 탭 등 실제 스킨 마크업(0690+에서).
- NamuMark 문법 렌더링.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

브랜드 색은 `#008485`(메모리/프로젝트 규칙). 색 대비는 WCAG AA를 목표로 한다. 토큰만 도입하고 실제 사용은 후속 스킨 태스크에서 확대한다.
