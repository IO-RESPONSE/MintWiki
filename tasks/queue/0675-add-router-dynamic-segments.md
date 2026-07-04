# 0675 Add dynamic path segments to Router

## Goal

정적 완전일치만 지원하는 `Router`에 `/wiki/{title}` 같은 동적 세그먼트 매칭을 추가한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/src/Http
- php/tests/Http

## Acceptance Criteria

- `MintWiki\Http\Router`가 `{name}` 형태의 동적 세그먼트를 포함한 경로를 등록·매칭할 수 있다.
- 매칭된 세그먼트 값을 핸들러가 받을 수 있도록 전달한다(예: 핸들러 인자 또는 `Request`의 route params).
- 기존 정적 경로 등록·매칭 동작은 그대로 유지된다(하위 호환).
- 정적 경로가 동적 경로보다 우선하도록 매칭 우선순위를 정의한다.
- php 테스트를 추가해 동적 매칭, 파라미터 추출, 정적 우선순위, 미매칭 시 null을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 개별 문서/설치 라우트 등록 — 이후 태스크에서 수행.
- 정규식 제약이나 optional 세그먼트 등 고급 기능.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`src/Http/Router.php`의 현재 구조(method → path → handler 맵)를 최소 변경으로 확장한다. 세그먼트는 슬래시로 구분되며 `{...}`는 한 세그먼트를 매칭한다. 나머지 route 연결이 이 기능에 의존한다.
