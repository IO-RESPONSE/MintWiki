# 0717 Operational diagnostics real data and environment export

## Goal

운영 진단 화면(`/admin/diagnostics`)이 하드코딩된 `placeholder` 대신 실제 DB/스키마/캐시/환경 상태를 보여주게 하고, 준비 중이던 환경 진단 export를 실제로 내려받을 수 있게 구현한다.

## Phase

Phase K: Delete + audit logging + backup download, 0714+.

## Scope

- php/src/Ui/OperationalDiagnosticsPage.php
- php/public/index.php (진단 라우트에 실데이터 주입 + export 라우트)
- php/src/App (진단 값 수집기, 필요 시)
- php/tests

## Acceptance Criteria

- `OperationalDiagnosticsPage`가 실제 값을 표시한다: **DB 상태**(연결/미설정/오류 + 드라이버·서버버전), **스키마 상태**(`schema_version` 최신 버전/마이그레이션 적용 여부), **캐시 상태**(설정된 백엔드/도달 가능 여부), **APP_ENV/앱 버전**(설정·`VERSION` 기준). 하드코딩 `placeholder` 문자열을 제거한다.
- 진단 값 수집을 `AppBootstrap`/`StoragePathConfig`/`ConfigLoader`와 PDO로 수행하는 수집기(또는 route 조립)를 만들고, `index.php`의 `/admin/diagnostics` 라우트가 실데이터를 페이지에 주입한다. DB 미연결 시에도 죽지 않고 "미설정/오류"로 표기.
- **환경 진단 export**: `GET /admin/diagnostics/export`를 등록해 진단 스냅샷(앱/PHP/확장/DB드라이버/스키마버전/환경 등)을 파일(JSON)로 다운로드하게 한다. 관리자 게이트로 보호하고, **민감정보(DB 비밀번호·DSN 자격·시크릿·토큰)는 반드시 제외**한다(`excludeSensitive` 로직 실동작). "준비 중" 비활성 버튼을 실제 export 링크/버튼으로 교체.
- 모든 출력 `Escaper` 이스케이프. export 응답은 `Content-Disposition: attachment` + 적절한 Content-Type.
- php 테스트로 (1) 페이지가 실제 DB/스키마/캐시/환경 값을 렌더(placeholder 문자열 부재), (2) export가 민감값을 제외한 진단 스냅샷을 다운로드로 반환, (3) 관리자 게이트(익명 302/비관리자 403), (4) DB 미연결 시 안전한 표기를 검증한다.

## Out of Scope

- 실시간 메트릭/그래프, 외부 모니터링 연동.
- 파일 권한 진단(`FilePermissionDiagnosticsPage`는 별도, 이미 존재).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

현재 `OperationalDiagnosticsPage`의 `renderSchemaStatusSection`/`renderCacheStatusSection`/`defaultEnvironmentDiagnostics`가 전부 `placeholder`를 반환하고 export는 `disabled` "준비 중" 버튼이다. `render(?array $environmentDiagnostics)`가 이미 주입 지점을 열어두었으니 route가 실데이터를 넘기면 된다. DB 서버버전은 `PDO::ATTR_SERVER_VERSION`, 스키마버전은 `schema_version` 테이블, APP_ENV/버전은 config·`VERSION`. 민감값 제외는 기존 `excludeSensitive` 계열 로직을 실제 동작하게 완성.
