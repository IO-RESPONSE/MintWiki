# 0674 Wire bootstrap into front controller with no-DB fallback

## Goal

프론트 컨트롤러(`index.php`)가 0673 부트스트랩으로 PDO를 획득하되, DB 미설정/미가용이어도 홈과 헬스체크는 계속 동작하도록 연결한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/tests/Http

## Acceptance Criteria

- `php/public/index.php`가 0673의 부트스트랩을 호출해 PDO(또는 미설정 상태)를 얻는다.
- DB 설정이 없거나 접속이 실패해도 `index.php`가 치명적 오류로 죽지 않고, 기존 `GET /`와 `GET /health`는 계속 200으로 응답한다.
- `GET /health` 응답에 DB 연결 가능 여부를 나타내는 필드를 추가한다(예: `db: "connected" | "unconfigured" | "error"`).
- php 테스트를 추가해 (1) DB 미설정 시 `/`·`/health`가 200, (2) health가 db 상태를 보고하는지 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 설치 마법사 라우트 등록 — 0676+에서 수행.
- 문서/인증 라우트.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

핵심 제약: 설정/DB가 없는 환경(로컬 내장 서버, 배포 직후 미설치 상태)에서도 앱이 로드돼야 한다. 접속 실패를 삼켜서 미설정으로 취급한다. 부트스트랩은 0673의 `AppBootstrap`을 사용한다.
