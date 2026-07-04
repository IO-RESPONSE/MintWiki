# 0672 Add live hosting API E2E smoke

## Goal

iowiki.iwinv.net 라이브 호스팅 배포본을 API/HTTP 기반 end-to-end smoke test로 검증한다.

## Phase

Phase F: Live Shared Hosting Porting, 0671+.

## Scope

- live QA
- API smoke tests
- HTTP form smoke tests
- docs

## Acceptance Criteria

- 라이브 사이트 base URL을 대상으로 자동 smoke test를 실행한다.
- 관리자 계정을 생성하거나, 0671에서 생성한 관리자 계정으로 로그인한다.
- 관리자 세션에서 테스트 문서를 생성한다.
- 관리자 세션에서 테스트 문서를 수정한다.
- 관리자 세션에서 테스트 문서를 삭제하거나 삭제 불가 시 숨김/보호/정리 가능한 상태로 만든다.
- 관리자 세션에서 일반 사용자 계정을 생성한다.
- 관리자 세션에서 읽기 전용 사용자 계정을 생성하거나 읽기 전용 권한 상태를 구성한다.
- 일반 사용자 세션으로 로그인한다.
- 일반 사용자 세션에서 문서 생성 또는 편집이 허용되는지 확인한다.
- 읽기 전용 사용자 세션으로 로그인한다.
- 읽기 전용 사용자 세션에서 문서 읽기가 가능한지 확인한다.
- 읽기 전용 사용자 세션에서 문서 생성 또는 편집이 거부되는지 확인한다.
- 익명 사용자에서 공개 문서 읽기 동작을 확인한다.
- 각 요청의 HTTP status, redirect, 주요 응답 문구, DB 반영 여부를 기록한다.
- API가 없는 기능은 서버 렌더 HTML form flow로 대체한다.
- CSRF 토큰이 필요한 form은 HTML에서 토큰을 추출해 제출한다.
- 테스트 데이터 이름은 고유 prefix를 사용한다.
- 테스트 후 가능한 데이터 정리를 수행하고, 정리하지 못한 데이터는 문서화한다.
- 실패한 시나리오는 0673+ 버그픽스 또는 보강 태스크로 넘긴다.
- 실제 계정 비밀번호는 저장소에 기록하지 않는다.

## Out of Scope

- 대규모 기능 개발.
- 부하 테스트.
- 보안 침투 테스트.
- 실제 운영 콘텐츠 작성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`
- live E2E smoke test against `https://iowiki.iwinv.net/` or the active deployment URL.

## Notes

권장 테스트 계정 이름:

- `smoke_admin_*`
- `smoke_user_*`
- `smoke_readonly_*`

권장 테스트 문서 prefix:

- `SmokeTest-YYYYMMDD-HHMMSS-*`

테스트는 curl 기반 스크립트 또는 PHP CLI 스크립트로 구현한다. FTP-only 호스팅이므로 서버에서 CLI를 실행하지 않는 전제로, 로컬에서 HTTP 요청을 보내 검증한다.
