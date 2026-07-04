# Live Hosting E2E Smoke Log

**Phase F: Live Shared Hosting Porting, 0671+** 문서. 태스크 0672
(iowiki.iwinv.net 라이브 배포본에 대한 API/HTTP 기반 end-to-end smoke
test) 실행 기록이다.

`docs/iowiki-shared-hosting-porting-log.md`가 0671의 배포/설치 절차와
배포 전 baseline HTTP smoke test(루트 응답, 민감 경로 차단)를 다룬다면,
이 문서는 관리자/일반 사용자/읽기 전용 사용자/익명 사용자 네 세션으로
실제 로그인·문서 CRUD·계정 생성·권한 거부까지 확인하는
`php/scripts/live-e2e-smoke-test.sh` 실행 결과를 다룬다.

## 1. 사용한 스크립트

```bash
php/scripts/live-e2e-smoke-test.sh --base-url https://iowiki.iwinv.net
```

- 기존 관리자 계정이 있으면 `SMOKE_ADMIN_USER`/`SMOKE_ADMIN_PASSWORD`
  환경변수로 전달한다. 없으면 스크립트가 `/install`을 통한 신규 관리자
  계정(`smoke_admin_*`) 생성을 먼저 시도한다.
- 테스트 계정은 `smoke_admin_*`/`smoke_user_*`/`smoke_readonly_*`,
  테스트 문서는 `SmokeTest-YYYYMMDD-HHMMSS-*` 접두사를 사용한다.
- 비밀번호는 커맨드라인 인자나 로그에 남기지 않는다(curl config
  `-K -`로만 전달).
- 각 시나리오는 route 미연결(404)이나 이전 단계 실패 시 스크립트를
  중단하지 않고 `blocked`/`skip`으로 기록한 뒤 다음 시나리오로 넘어간다.

## 2. 실행 결과 (2026-07-04, run_id=20260704-192053)

```
base_url=https://iowiki.iwinv.net
run_id=20260704-192053
doc_prefix=SmokeTest-20260704-192053

[blocked] health_check: GET https://iowiki.iwinv.net/health -> status=404 app not deployed yet or /health unreachable
[pass] anonymous_read_home: GET https://iowiki.iwinv.net/ -> status=200 public home page readable
[blocked] admin_login_or_create: GET/POST https://iowiki.iwinv.net/login -> skipped: /health precondition failed
[skip] admin_create_document -> skipped: no authenticated admin session
[skip] admin_edit_document -> skipped: no document id from create step
[skip] admin_delete_or_hide_document -> skipped: no document id from create step
[skip] admin_create_normal_user -> skipped: no authenticated admin session
[skip] admin_create_readonly_user -> skipped: no authenticated admin session
[skip] normal_user_login -> skipped: normal user account not created
[skip] normal_user_document_write_check -> skipped: normal user session not authenticated
[skip] readonly_user_login -> skipped: readonly user account not created
[skip] readonly_user_read_check -> skipped: readonly user session not authenticated
[skip] readonly_user_write_denied_check -> skipped: readonly user session not authenticated

summary: pass=1 fail=0 blocked=2 skip=10
leftover_data: none
live_e2e_smoke_test_status=blocked (exit code 1)
```

수동 `curl` 확인으로 위 결과를 한 번 더 교차 검증했다:

- `GET https://iowiki.iwinv.net/` → `200`, 응답 본문은 이 저장소의 홈
  페이지가 아니라 호스팅사 기본 안내 페이지(`<title>[iwinv] 셋팅
  완료</title>`)다.
- `GET https://iowiki.iwinv.net/index.php` → 동일한 호스팅사 기본
  안내 페이지.
- `GET https://iowiki.iwinv.net/health`, `/login`, `/admin`,
  `/api/documents`, `/documents`, `/install` → 모두 `404`(Apache 기본
  404 페이지이며, 이 저장소의 `ErrorPage`/JSON 404 응답이 아니다).

## 3. 원인 분석

두 가지가 겹쳐서 지금은 시나리오 대부분이 차단된다.

1. **배포 자체가 아직 완료되지 않았다.** `docs/iowiki-shared-hosting-porting-log.md`
   §5가 이미 "배포 패키지 업로드", "설치/schema 적용"을 **대기**로
   기록해 두었다 — 실제 FTP/DB 자격증명이 없어 실행되지 못했다. 이번
   실행에서 확인한 호스팅사 기본 안내 페이지는 그 기록과 일치한다.
2. **배포가 끝나도, 로그인/문서/관리자 route는 아직 프런트 컨트롤러에
   연결되어 있지 않다.** `php/public/index.php`는 현재 `GET /`와
   `GET /health` 두 route만 직접 등록한다. `php/src/Http/AuthRoutes.php`,
   `AdminRoutes.php`, `DocumentApiRoutes.php`, `UiRoutes.php`가 정의하는
   `/login`, `/admin/*`, `/api/documents*`, `/sitemap.xml`은 모두
   `Router::register`만 검증되어 있을 뿐(`php/tests/Http/RouteRegistrationTest.php`),
   `index.php`가 이 클래스들의 `register()`를 호출하지 않는다. 또한
   문서 편집/삭제 폼(`DocumentEditPage`)이 가리키는 `POST /documents/{id}`,
   사용자 생성(관리자용) route는 아직 어떤 클래스에도 정의되어 있지
   않다 — `docs/completion-summary-0351-0670.md` §3이 이미 "실제
   authentication/login: placeholder 페이지만 존재"라고 기록한 상태와
   일치한다.

즉, 지금 이 스모크 테스트가 대부분 `blocked`/`skip`으로 끝나는 것은
스크립트의 결함이 아니라 **의도된 현재 상태**를 그대로 드러낸 것이다.

## 4. 확인된 것 / 남은 데이터

- 확인된 것: 익명 사용자가 루트 URL을 2xx로 읽을 수 있다(현재는 호스팅사
  기본 안내 페이지, 배포 후에는 이 저장소의 홈 페이지가 되어야 한다).
- 생성된 테스트 계정/문서: 없음. 관리자 세션을 확보하지 못해 이후
  모든 계정/문서 생성 시나리오가 스킵되었으므로, 정리(cleanup)가
  필요한 leftover 데이터도 없다.

## 5. 후속 태스크로 넘기는 항목 (0673+)

- **실제 배포 완료**: `docs/iowiki-shared-hosting-porting-log.md` §5의
  "대기" 항목(패키지 업로드, 설치/schema 적용, 배포 후 HTTP 스모크
  테스트, 설치 후 점검)을 실제 FTP/DB 자격증명이 주어지는 세션에서
  이어서 수행해야 한다.
- **route 연결**: `php/public/index.php`에
  `AuthRoutes::register()`/`AdminRoutes::register()`/
  `DocumentApiRoutes::register()`/`UiRoutes::register()`를 연결하고,
  실제 인증/세션/ACL 로직을 뒤에 붙여야 `admin_login_or_create` 이후
  시나리오를 실제로 검증할 수 있다.
- **누락된 route 추가**: 문서 생성 폼(GET) 진입점, 문서 편집/삭제
  route(`POST /documents/{id}`, 삭제 또는 숨김), 관리자용 사용자 생성
  route(`/admin/users` 등, 일반/읽기 전용 역할 구분 포함), 사용자
  삭제/비활성화 route가 현재 어디에도 없다 — 위 route 연결 작업과 함께
  설계해야 한다.
- 위 세 가지가 끝난 뒤 `php/scripts/live-e2e-smoke-test.sh --base-url
  https://iowiki.iwinv.net`를 다시 실행해 이 문서를 갱신하고, 그때
  실제로 실패하는 시나리오가 있으면 별도 버그픽스 태스크로 넘긴다.

## 관련 문서

- `docs/iowiki-shared-hosting-porting-log.md` — 0671 FTP 배포 실행
  기록, 배포 전 baseline HTTP smoke test 결과.
- `docs/completion-summary-0351-0670.md` — 0351-0670 구간 산출물 중
  아직 placeholder/skeleton 상태인 항목 목록(§3).
- `php/scripts/README.md` — `live-e2e-smoke-test.sh`,
  `live-http-smoke-test.sh`, `post-cutover-validate.sh` 등 스크립트 상세.
- `docs/hosting-phase-qa-checklist.md` — Phase E QA 체크리스트.
