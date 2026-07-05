# php/scripts

`php/` 트리 전용 QA 명령을 모아 두는 디렉터리. Phase B: PHP Runtime
Skeleton, 0391-0440 의 0430 산출물이다
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

- `test.sh` — `php/tests/` 아래 모든 `*Test.php`를 찾아 `php` CLI로
  하나씩 실행하고(`docs/php-test-bootstrap.md`가 정한 실행 방식과 동일),
  파일별 `PASS`/`FAIL`과 전체 통과 개수를 출력한다. 하나라도 실패하면
  실패한 파일의 stderr/stdout을 함께 출력하고 exit code 1로 끝난다.
  `vendor/autoload.php`가 없으면(=`composer install` 미실행) 바로 안내
  메시지와 함께 exit code 1로 끝난다. `php/`에서
  `scripts/test.sh`로, 저장소 루트에서 `php/scripts/test.sh`로 실행할 수
  있다(스크립트가 자기 위치 기준으로 `php/`로 이동한다).
- `qa.sh` — `test.sh`를 호출하는 단일 진입점. 정적 분석 도구(PHPStan/
  Psalm)는 아직 도입 전이므로(`docs/php-static-analysis-plan.md`) 지금은
  테스트 실행만 하지만, 그 문서의 도입 트리거 조건이 성립하면 정적
  분석 단계를 이 스크립트에 추가한다. "test/static check 명령을 한 곳에
  둔다"는 0430 Notes 요구사항을 충족하는 지점이다.
- `build-package.sh` — 공유 호스팅 배포 패키지 빌드의 골격 스크립트.
  `php/deployment-package-manifest.json`을 읽고 기본 `--without-vendor`
  모드와 `--with-vendor` 모드의 입력 목록을 분리해 출력한다. 실제
  아카이브 생성은 후속 패키징 태스크에서 추가한다.
- `cache-clear.sh` — 애플리케이션 캐시 비우기 명령의 골격 스크립트.
  현재 PHP 캐시 포트는 `get`/`set`/`delete` 기본 계약만 고정되어 있어
  전체 삭제 백엔드 연결은 아직 없다. 이 스크립트는 실행 가능한 CLI
  진입점과 help/오류 처리를 먼저 고정하고, 실제 캐시 삭제는 후속
  태스크에서 추가한다.
- `post-cutover-validate.sh` — Python에서 PHP로 최종 cutover 후 실행할
  검증 명령의 골격 스크립트. `--base-url`로 공개 URL을 받아 `/health`,
  DB 연결/schema 준비 상태, 문서 생성, 생성 문서 조회 순서의 검증 계획을
  출력한다. 실제 HTTP 요청, DB 진단, 문서 쓰기 자동화는 후속 태스크에서
  추가한다.
- `ftp-deploy.sh` — SSH/Composer를 쓸 수 없는 plain FTP 계정(0671
  iowiki.iwinv.net 등)에 배포 패키지를 올리는 스크립트.
  `--local-public-dir`을 원격 docroot(`--docroot-name`, 기본
  `public_html`)로 미러링하기 전에 기존 `index.php`를 `--backup-dir`로
  먼저 백업하고, `--private-map LOCAL:NAME`으로 docroot 밖 형제
  디렉터리(config/src/vendor/storage/db 등)를 함께 올릴 수 있다. FTP
  비밀번호는 `FTP_PASSWORD` 환경변수 또는 `--password-file`로만 받고
  커맨드라인 인자로 노출하지 않는다. `--dry-run`으로 연결 없이 실행될
  `lftp` 명령을 미리 확인할 수 있다.
- `phpinfo-probe.sh` — 임시 `phpinfo()` 진단 파일을 FTP로 올리고(선택적
  으로 `--fetch --base-url`로 즉시 curl 확인) 성공/실패와 무관하게 원격
  파일과 로컬 임시 파일을 모두 삭제하는 스크립트(trap 기반 cleanup).
  PHP 버전, 확장, loaded config, document root, rewrite 환경 확인 후
  진단 파일이 남는 사고를 막는다.
- `smoke-ui-skin.sh` — 스킨(Phase H, 0689-0694) 통합 연기 테스트
  (`tests/Http/UiSkinSmokeTest.php`). GET `/`, GET `/wiki/{title}` route
  응답에 상단바(`site-nav`)/문서 액션 탭(`document-tabs`) 마크업이
  있는지, 배포되는 `design-tokens.css`/`sidebar.css`가 브랜드색
  (`#008485`)/반응형 `@media` 규칙을 담고 있는지 DB·자격 증명 없이
  확인한다(태스크 0695).
- `live-http-smoke-test.sh` — 배포된 공개 URL에 대해 실제 `curl` 요청으로
  루트 응답(2xx)과 `config/`, `vendor/`, `storage/`, `db/`,
  `composer.json`, `composer.lock`, `.env` 같은 민감 경로 차단(403/404)을
  확인하는 스모크 테스트. `post-cutover-validate.sh`와 달리 골격이 아니라
  실제 HTTP 요청을 보낸다.
- `live-e2e-smoke-test.sh` — 배포된 공개 URL에 대해 설치 마법사 접속
  상태(`/install`) 확인 → 관리자 콘솔 보호 확인(`/admin` 익명 차단,
  관리자 세션의 `/admin`, `/admin/maintenance`, `/admin/backup`,
  `/admin/restore`, `/admin/diagnostics`, `/admin/diagnostics/files` 도달성)
  → 관리자 로그인(`/login`) → 문서 생성/편집/조회
  (`/wiki/{title}`, `/wiki/{title}/edit`) → 권한 확인(익명 사용자의 읽기
  허용/쓰기 거부)까지 실사용 흐름을 curl로 수행하는 API/폼 E2E smoke
  test(태스크 0672, 0673-0687에서 실제로 연결된 route에 맞춰 0688에서
  갱신, 0695에서 스킨(상단바/브랜드색/문서 액션 탭/반응형) 확인 시나리오
  추가). `--base-url`이 필수이며, 기존 관리자 계정은
  `SMOKE_ADMIN_USER`/`SMOKE_ADMIN_PASSWORD` 환경변수로 전달한다 — 이
  환경변수가 없으면 로그인이 필요한 모든 단계를 실패 없이 안전하게
  skip한다(설치 마법사로 최초 관리자 계정을 만드는 것은 자격 증명을 가진
  운영자가 브라우저로 수행할 절차이며, 이 스크립트가 대신 만들지 않는다).
  계정 비밀번호는 커맨드라인 인자나 로그에 남기지 않고 curl
  config(`-K -`)로만 전달한다. 각 시나리오는 route가 아직 연결되지
  않았거나(404) 이전 단계가 실패하면 실패로 스크립트를 중단하지 않고
  `blocked`/`skip`으로 기록한 뒤 다음 단계로 넘어간다. 실행 결과와 현재
  알려진 차단 사유는 `docs/live-hosting-e2e-smoke-log.md`에 기록되어
  있다.

공유 호스팅에서 CLI 실행 권한이 없으면, 호스팅 파일 관리자나 SFTP로
설정된 캐시 디렉터리의 **내용만** 비우는 운영 절차를 사용한다. 캐시
디렉터리 자체는 삭제하지 않는다. 디렉터리 권한과 경로는 설치/운영
문서가 정한 값을 따른다.

저장소 루트의 `scripts/qa.sh`가 이 스크립트를 선택 실행하도록 연결하는
것은 이 태스크의 범위가 아니다 — 0431(Add root QA hook for optional PHP)
이 담당한다.
