# Shared Hosting QA Checklist

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅 배포본을 설치, 업그레이드, 롤백하거나 운영 화면을 점검할
때 사용하는 최소 QA 체크리스트를 정의한다. 범위는 shared hosting 제약 안에서
반드시 사람이 확인해야 하는 설치 흐름, 업그레이드 흐름, rollback 흐름, forms,
admin 화면이다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, installer QA 담당자, admin 화면 QA
  담당자.
- **다루는 것**:
  - 새 설치와 재설치 차단 확인.
  - 릴리스 업그레이드와 cache clear 확인.
  - 장애 발생 시 rollback 가능 여부와 복구 후 smoke test 확인.
  - 서버 렌더링 forms의 검증, CSRF, 오류 표시 확인.
  - admin/diagnostics 화면의 상태 표시와 민감값 비노출 확인.
- **다루지 않는 것**:
  - 호스팅사별 제어판 자동화.
  - 패키지 빌드 스크립트 구현.
  - 운영 서버 배포 대행 절차.

## 사용법

공용 웹호스팅 QA는 자동 검사와 수동 브라우저 확인을 함께 수행한다. 로컬에서 가능한
검사는 먼저 실행하고, 실제 호스팅 환경에서는 아래 체크리스트를 릴리스 기록에 남긴다.

```bash
scripts/qa.sh
```

작업 전후에는 error log, schema version, installer lock file, writable directory
상태를 기록한다. 실패가 하나라도 있으면 일반 트래픽을 열기 전에 maintenance mode를
유지하고 관련 절차 문서의 중단 기준을 따른다.

## 1. 설치 QA

새 설치는 document root, 설정 파일, DB 연결, 쓰기 디렉터리, installer lock file을
한 번에 검증한다.

- [ ] document root가 `php/public/`을 가리키고 `php/src/`, `php/config/`,
      `php/vendor/`, `storage/`, `db/`가 URL로 열리지 않는다.
- [ ] installer requirement check가 PHP 버전, PDO MariaDB 드라이버, URL rewrite,
      writable directories, 설정 파일 생성 가능 여부를 표시한다.
- [ ] DB 연결 정보 저장 후 schema 생성 또는 schema version 확인이 성공한다.
- [ ] `storage/cache/`, `storage/uploads/`, `storage/logs/`가 각각 쓰기 가능하고
      서로 다른 용도로 분리되어 있다.
- [ ] 설치 완료 후 `storage/installer/install.lock`이 document root 밖에 생성된다.
- [ ] lock file이 있는 상태에서 `/installer`는 재실행되지 않고 403 또는
      `installation_already_complete` 상태를 반환한다.
- [ ] 설치 실패 화면과 로그에 DB 비밀번호, DSN 전체 문자열, API key 같은 민감값이
      노출되지 않는다.

## 2. 업그레이드 QA

업그레이드는 새 코드, 의존성, schema version, cache가 같은 릴리스 기준으로 맞는지
확인한다.

- [ ] 업그레이드 전 현재 코드, `php/config/`, `storage/uploads/`, 데이터베이스 백업을
      확보했다.
- [ ] 새 패키지의 `php/src/`, `php/public/`, `php/vendor/`, `php/composer.lock`이 같은
      릴리스에서 나온 파일이다.
- [ ] 운영 설정 파일과 `storage/uploads/`가 새 패키지 파일로 덮이지 않았다.
- [ ] `/installer` 또는 `/admin/diagnostics`에서 현재 schema version과 필요한 schema
      version이 일치한다.
- [ ] 필요한 마이그레이션을 적용한 뒤 schema version을 다시 확인했다.
- [ ] `storage/cache/`, PHP opcode cache, static asset cache를 정리했다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색이 업그레이드 후 정상 응답한다.
- [ ] 오류 로그에 `Class not found`, `Failed opening required vendor/autoload.php`,
      migration failure가 새로 쌓이지 않는다.

## 3. Rollback QA

Rollback은 이전 릴리스 전체와 현재 DB schema가 함께 동작 가능한지 확인한 뒤 진행한다.

- [ ] rollback 전 현재 document root, 실패한 릴리스 식별자, 이전 릴리스 식별자,
      schema version, 최근 error log를 보존했다.
- [ ] DB 변경이 없거나 이전 코드가 무시할 수 있는 additive 변경인지 확인했다.
- [ ] destructive migration, 부분 적용된 migration, 새 데이터 형식 변경이 있으면 코드만
      rollback하지 않고 보정 계획을 먼저 세웠다.
- [ ] 이전 릴리스의 `php/src/`, `php/public/`, `php/vendor/`, `php/composer.lock`을 같은
      릴리스 기준으로 복원했다.
- [ ] 운영 설정 파일, 사용자 업로드, export 파일은 rollback 중 삭제하거나 덮어쓰지
      않았다.
- [ ] `storage/cache/`와 opcode cache를 정리하고 이전 asset version이 응답하는지
      확인했다.
- [ ] rollback 후 `/installer` 또는 `/admin/diagnostics`, 로그인, 문서 보기, 문서 편집,
      검색이 정상 응답한다.

## 4. Forms QA

Forms는 JavaScript 없이도 제출 가능해야 하며, shared hosting의 세션과 보안 제약을
만족해야 한다.

- [ ] 모든 상태 변경 form은 `POST`를 사용하고 CSRF token을 포함한다.
- [ ] CSRF token 누락 또는 불일치 요청은 403 또는 명확한 오류 메시지로 거부된다.
- [ ] 필수값 누락, 길이 초과, 잘못된 타입 입력은 field-level 오류와 form-level 오류
      요약을 함께 표시한다.
- [ ] 오류 요약은 `role="alert"`로 표시되고 각 오류가 해당 입력 필드로 이동할 수 있는
      링크를 제공한다.
- [ ] 사용자가 입력한 제목, 본문, 검색어, 사용자명은 HTML escape된 상태로 다시
      출력된다.
- [ ] 새로고침 또는 뒤로가기 후 중복 제출이 발생하지 않도록 성공 시 redirect 또는
      flash message 흐름을 사용한다.
- [ ] 모바일 폭에서도 label, input, button, 오류 메시지가 겹치거나 잘리지 않는다.

## 5. Admin QA

Admin과 diagnostics 화면은 운영자가 상태를 판단할 수 있는 충분한 정보를 제공하되,
민감값은 노출하지 않는다.

- [ ] admin 진입은 인증된 관리자에게만 허용되고 일반 사용자 또는 익명 요청은 403 또는
      로그인 화면으로 이동한다.
- [ ] `/admin/diagnostics`가 PHP 버전, DB driver, schema version, writable directory,
      installer lock file 상태를 표시한다.
- [ ] diagnostics 화면은 DB 비밀번호, DSN 전체 문자열, 세션 ID, 쿠키, API key를 원문으로
      출력하지 않는다.
- [ ] admin의 상태 변경 form은 CSRF token과 권한 검사를 모두 수행한다.
- [ ] audit 또는 운영 로그 화면은 검색/페이지네이션 후에도 HTML escape와 접근 제어를
      유지한다.
- [ ] maintenance mode 또는 installer lock 상태가 admin 화면에서 운영자가 이해할 수
      있는 문구로 표시된다.
- [ ] admin 화면의 실패 상태는 서버 로그에 기록되며, 브라우저 응답에는 stack trace나
      절대 경로를 표시하지 않는다.

## 관련 문서

- [Shared Hosting Security Checklist](shared-hosting-security-checklist.md) — public path,
  config, installer, permissions 보안 점검.
- [Shared Hosting Upgrade Procedure](shared-hosting-upgrade-procedure.md) — 업그레이드
  절차와 cache clear 기준.
- [Shared Hosting Rollback Procedure](shared-hosting-rollback-procedure.md) — rollback
  결정 기준과 복원 절차.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — shared hosting
  마이그레이션 적용 경로.
- [PHP UI Manual QA Script](php-ui-manual-qa-script.md) — 서버 렌더링 UI 수동 QA 흐름.
- [PHP UI Phase QA Checklist](php-ui-phase-qa-checklist.md) — forms, 보안, 접근성, 모바일
  UI 회귀 점검.
- [Installer Lock File Policy](installer-lock-file-policy.md) — 설치 완료 후 installer
  차단 기준.
