# 0682 Finalize installer lock and completion route

## Goal

설치를 마무리해 installer lock을 기록하고 완료 페이지를 보여주며, 이후 설치 라우트 접근을 차단한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Installer
- php/src/Ui
- php/tests

## Acceptance Criteria

- 관리자 생성(0681) 이후 완료 단계에서 `InstallerLock`으로 lock을 기록한다(비공개 경로).
- `GET /install/complete`가 `InstallCompletionPage`를 렌더한다.
- 완료 후에는 `InstallerRouteGate`가 모든 `/install*` 라우트 접근을 차단한다(설치 재실행 방지).
- lock 파일과 `schema_version` 중 하나라도 설치 완료를 나타내면 재설치가 막힌다.
- php 테스트로 lock 기록, 완료 페이지, 설치 후 라우트 차단을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 문서/인증 라우트 — 0683+에서 수행.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Installer\InstallerLock`, `MintWiki\Ui\InstallCompletionPage`, `MintWiki\Installer\InstallerRouteGate`. lock 경로는 docroot 밖 비공개 위치를 사용한다.
