# 0691 Integrate skin header and footer into Layout

## Goal

`Layout`이 현재 빈 `<header></header>`/`<footer></footer>`만 렌더링하는 문제를 고쳐, 0690 상단 네비게이션 바를 헤더에 주입하고 나무위키풍 푸터(라이선스/사이트 정보 + 기존 요청ID)를 렌더링하도록 한다. 모든 페이지가 일관된 스킨을 갖게 프론트 컨트롤러 호출부를 갱신한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/src/Ui/Layout.php
- php/public/index.php
- php/public/assets/css
- php/tests

## Acceptance Criteria

- `Layout::render()`가 상단 네비게이션 바(0690)를 헤더에 포함하도록 확장한다. 기존 시그니처를 유지하되 navigation/헤더 콘텐츠를 받는 방식으로 확장하고(선택 인자 또는 전용 메서드), 기존 인자(`title`, `body`, `lang`, `requestId`, `seo`)와 하위 호환을 지킨다.
- 푸터에 나무위키풍 사이트 정보(사이트명, 간단한 라이선스/안내 문구)를 렌더링하고 기존 `requestId` 표시를 유지한다.
- `index.php`의 페이지 렌더 호출부(홈, 로그인, 문서 보기 등 Layout을 쓰는 경로)가 새 헤더/푸터를 사용하도록 갱신한다.
- 콘텐츠는 0689의 `--content-max-width` 등 토큰으로 중앙 정렬된 나무위키풍 폭을 갖는다.
- 기존 Layout/페이지 관련 php·py 테스트가 계속 통과하도록 갱신하고, 헤더에 상단바가, 푸터에 사이트 정보가 포함됨을 검증하는 테스트를 추가한다.

## Out of Scope

- 문서 상단 액션 탭(0692), 홈 프론트페이지 개편(0693), 사이드바/모바일(0694).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `src/Ui/Layout.php`의 `render(string $title, string $body, string $lang='ko', ?string $requestId=null, ?SeoMetadata $seo=null)`. 헤더/푸터가 비어있는 것이 현재 라이브에서 상단바가 없는 원인이다. 상단바는 0690 렌더러를 재사용한다. 하위 호환을 위해 navigation 미전달 시에도 깨지지 않게 한다.
