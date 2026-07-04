# 0679 Implement installer database config write

## Goal

설치 마법사 DB 폼 제출을 처리해, 입력된 접속 정보를 검증한 뒤 비공개 `config/local-config.php`로 기록한다. (현재 빠져 있는 글루)

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Installer
- php/config
- php/tests

## Acceptance Criteria

- `POST /install/database`가 CSRF 토큰을 검증한다.
- 제출된 접속 정보로 `PdoConnectionFactory` 접속을 시험한다. 실패하면 폼으로 되돌아가 오류를 표시하고 아무것도 기록하지 않는다.
- 접속 성공 시 `config/local-config.php`(또는 동등한 비공개 설정 파일)를 `database.php.sample` 구조로 기록한다. 파일은 docroot 밖 경로를 사용하고, 권한을 제한한다(예: 0600).
- 비밀번호를 로그나 응답 본문에 노출하지 않는다.
- 기록 후 다음 단계(스키마 적용, 0680)로 진행하는 링크/리다이렉트를 제공한다.
- php 테스트로 (1) 잘못된 CSRF 거부, (2) 접속 실패 시 미기록, (3) 성공 시 설정 파일 생성/내용을 임시 디렉터리로 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 실제 스키마 적용 — 0680에서 수행.
- 관리자 계정 생성.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`LocalConfigLoader`(0674 부트스트랩)가 읽는 것과 동일한 경로/형식으로 기록해야 설치 후 앱이 같은 설정을 읽는다. `config/database.php.sample`의 배열 구조를 따른다. 테스트는 실제 DB 없이 접속 시험을 mock/skip할 수 있게 접속 로직을 주입 가능하게 만든다.
