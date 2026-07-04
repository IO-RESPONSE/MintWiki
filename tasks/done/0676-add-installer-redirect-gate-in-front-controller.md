# 0676 Add installer redirect gate in front controller

## Goal

DB는 설정됐지만 아직 설치되지 않은 경우(스키마 미적용), 프론트 컨트롤러가 요청을 설치 마법사로 유도하도록 게이트를 추가한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Installer
- php/tests/Http

## Acceptance Criteria

- `index.php`가 `InstallerRouteGate`(및 `DBCheck`)를 사용해 설치 완료 여부를 판단한다.
- DB가 설정되어 있고 미설치 상태이면, 일반 UI 요청을 설치 진입점(`/install`)으로 유도한다(리다이렉트 또는 설치 안내 페이지).
- 설치가 완료된 경우 설치 라우트 접근은 게이트로 차단된다.
- DB 미설정 상태에서는 설치 게이트가 앱을 막지 않는다(홈·헬스체크 계속 동작, 0674 계약 유지).
- php 테스트로 (1) 미설치→설치유도, (2) 설치완료→설치라우트 차단, (3) 미설정→게이트 비활성을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 설치 각 단계 페이지/폼 라우트 등록 — 0677+에서 수행.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Installer\InstallerRouteGate`, `MintWiki\Installer\DBCheck`, `MintWiki\Installer\InstallerLock`. `schema_version` 테이블 존재/데이터로 설치 완료를 판정하는 기존 로직을 그대로 사용한다.
