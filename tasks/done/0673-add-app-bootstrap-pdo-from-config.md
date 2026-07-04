# 0673 Add app bootstrap that builds PDO from local config

## Goal

LocalConfigLoader가 읽은 설정으로 PDO 연결을 만들어 주는 애플리케이션 부트스트랩 진입점을 추가한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/src/App
- php/tests/App

## Acceptance Criteria

- `php/src/App`에 부트스트랩 클래스(예: `AppBootstrap`)를 추가해 `LocalConfigLoader` → `ConnectionConfig` → `PdoConnectionFactory` 순으로 설정을 읽어 PDO를 생성한다.
- DB 설정(`.env`의 `WIKI_MARIADB_DSN`/`WIKI_DATABASE_URL` 또는 `config/local-config.php`)이 없으면 예외를 던지지 않고 "미설정" 상태(예: `null` PDO)를 반환한다.
- 설정 디렉터리 경로를 주입 가능하게 만들어, 테스트에서 fixture 설정을 사용할 수 있게 한다.
- php 테스트를 추가해 (1) 설정이 있을 때 PDO 생성, (2) 설정이 없을 때 미설정 반환을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- `index.php`(프론트 컨트롤러) 수정 — 0674에서 수행.
- 실제 라이브 배포.
- 이후 태스크 번호의 작업.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트를 재사용한다: `MintWiki\App\LocalConfigLoader`, `MintWiki\Persistence\ConnectionConfig`, `MintWiki\Persistence\PdoConnectionFactory`. 실제 DB 서버 접속 없이도 단위 테스트가 가능하도록, 설정 파싱과 실제 접속 시도를 분리한다. 범위가 커지면 확장하지 말고 후속 큐 태스크로 분리한다.
