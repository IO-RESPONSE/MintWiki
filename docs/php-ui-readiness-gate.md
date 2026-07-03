# PHP UI Readiness Gate

**Phase D: Server-rendered UI after PHP and DB, 0521-0610** 완료 평가 문서.
웹호스팅 배포 전에 UI 계층이 갖춰야 할 기술 조건과 품질 기준을 정의한다.
이 문서는 Phase D 산출물(템플릿, 라우터, 정적 asset, 폼, 오류 페이지)이
**웹호스팅 배포 가능 상태**에 있는지를 판정하기 위한 gate다.

## 이 gate가 판정하지 않는 것 (범위 구분)

Phase D 기간에는 이미 여러 문서가 각자 다른 질문에 답하고 있다. 이 gate
문서는 "Phase D를 완료하고 웹호스팅 배포를 준비해도 되는가"라는 **하나의
예/아니오 질문**에만 답한다 — 아래 질문들을 다시 판정하지 않는다.

- **"Phase D 산출물이 추가되는 동안 기존 기능이 깨지지 않았는가?"** —
  `docs/php-ui-phase-qa-checklist.md`(0521+)의 자동화된 회귀 검사.
  이 gate는 신규 회귀 없음을 *전제*로 한다.
- **"웹호스팅 운영 환경 자체의 제약은 무엇인가?"** —
  `docs/db-web-hosting-constraints.md`, `docs/shared-hosting-migration-policy.md`
  의 운영 정책. 이 gate는 UI 코드가 그 제약을 회피하지 않는지만 판정한다.

## Gate 조건

Phase D를 완료하고 웹호스팅 배포를 시작하려면 아래 7개 조건이 **전부** 성립해야 한다.
하나라도 실패하면 웹호스팅 배포를 진행하지 않고, 실패한 조건을 먼저 해소한다.

1. **Phase D QA 체크리스트 통과** — `docs/php-ui-phase-qa-checklist.md`
   가 지정한 절차대로 `scripts/test.sh`, `scripts/qa.sh` 가 모두 exit
   code 0으로 끝난다. PHP CLI가 있는 환경에서는 `scripts/qa.sh` 가
   `php/scripts/qa.sh` 를 함께 실행한다.

2. **UI 라우터와 템플릿 완성도** — 아래 항목이 모두 존재하고 서버 렌더링으로 동작한다:
   - [ ] 문서 조회 페이지 (`/documents/<id>`)
   - [ ] 문서 생성 폼 (`/documents/new`)
   - [ ] 문서 수정 폼 (`/documents/<id>/edit`)
   - [ ] 문서 목록/검색 결과 (`/documents`, `/search`)
   - [ ] 이력 보기 (`/documents/<id>/revisions`)
   - [ ] 로그인 페이지 (`/login`)
   - [ ] 사용자 차단/해제 페이지 (관리자, `/admin/users`)
   - [ ] 오류 페이지 (404, 403, 500, 503)
   - [ ] 설치 필수 페이지 (`/install` 또는 초기화)

   각 라우터가 권한(ACL) 검사 후에 해당 템플릿을 렌더링하고,
   템플릿이 사용자 입력을 HTML escape 처리한다.

3. **HTML Escaping 정책 준수** — 모든 사용자 입력 유래 문자열이 다음 기준을 따른다:
   - [ ] PHP 템플릿에서 `<?= $value ?>` 형태로 직접 출력 시,
         `$value` 는 이미 escaped 문자열이거나 escape 함수(`htmlspecialchars(...ENT_QUOTES...)`)
         를 통과했다. Raw 문자열을 절대 직접 출력하지 않는다.
   - [ ] 문서 제목, 사용자명, 검색 쿼리, 폼 오류 메시지 등이 모두
         escape 처리된 상태로 HTML에 삽입된다.
   - [ ] 문서의 rendered HTML(render 모듈 출력)은 신뢰할 수 있는 소스이므로
         raw HTML 삽입이 허용되지만, 그 외 모든 사용자 입력은 escape된다.
   - [ ] 자동화 테스트(`php/tests/Modules/Document/HtmlEscapingTest.php`)가
         XSS payload를 검증하고, `php/scripts/qa.sh` 경유로 통과한다.

4. **CSRF 방어 기반** — state-changing 폼이 다음을 준비한다:
   - [ ] `<form>` 요소가 POST 메서드를 사용한다.
   - [ ] `<input type="hidden" name="csrf_token" value="...">` 필드를 포함할 수 있는
         구조가 템플릿에 있다 (token 생성/검증 로직은 아직 구현하지 않아도 되지만,
         field 위치를 미리 잡아둔다).
   - [ ] 문서 생성/수정, 사용자 차단, 감사 로그 export 같은 모든 상태 변경 폼이
         이 구조를 따른다.

5. **보안 HTTP 헤더 기본** — 아래 헤더들이 모든 HTTP 응답에 포함된다:
   - [ ] `X-Content-Type-Options: nosniff` — MIME 스니핑 방지.
   - [ ] `X-Frame-Options: DENY` 또는 `SAMEORIGIN` — clickjacking 방지.
   - [ ] `X-XSS-Protection: 1; mode=block` — 구식 브라우저의 XSS 필터 활성화.

   자동화 테스트(`php/tests/Http/SecurityHeadersTest.php`)가 이를 검증하고,
   `php/scripts/qa.sh` 경유로 통과한다.

6. **모바일 반응형 기초** — 아래 조건이 모두 충족된다:
   - [ ] 모든 HTML 페이지가 viewport meta 태그를 가진다:
         `<meta name="viewport" content="width=device-width, initial-scale=1">`.
   - [ ] CSS가 최소 모바일(~480px), 데스크톱(768px~) 두 가지 breakpoint를 가진다.
   - [ ] 모바일에서 텍스트가 읽을 수 있는 크기(16px 이상)를 유지하고,
         버튼과 링크의 터치 영역이 최소 44x44px이다.
   - [ ] CSS가 로드되지 않았을 때도 콘텐츠가 단일 열로 읽을 수 있다
         (mobile-first progressive enhancement).

   자동화 테스트(`php/tests/UI/MobileTest.php`)가 viewport와 media query
   존재를 확인한다.

7. **접근성(WCAG 2.1 AA) 기초** — 아래 항목이 모두 충족된다:
   - [ ] 모든 페이지가 `<html lang="ko">` 속성을 가진다.
   - [ ] 모든 페이지가 `<header>`, `<main>`, `<footer>` landmark 요소를 사용한다.
   - [ ] 폼 필드(`<input>`, `<textarea>`, `<select>`)가 모두
         `<label for="id">` 로 명시적으로 레이블되어 있다.
   - [ ] 폼 오류가 발생하면 오류 목록이 `<div role="alert">` 로 감싸져 있다.
   - [ ] 페이지의 첫 제목이 `<h1>` 이고, 제목 계층이 순서대로 내려간다
         (h1 → h2 → h3, h2에서 h4로 뛰지 않음).

   자동화 테스트(`php/tests/UI/AccessibilityBaselineTest.php`)가
   `lang`/`landmark`/`role="alert"` 존재를 검증한다.

## 재판정 방법

이 gate의 통과 여부는 표로 고정된 값이 아니라, Phase D를 완료하기
직전에 아래 절차로 다시 확인해야 한다.

```bash
# 필수: 모두 exit code 0으로 끝나야 한다.
scripts/test.sh
scripts/qa.sh
cd php && composer install && cd -
php/scripts/qa.sh

# 선택: 로컬 서버에서 각 라우터 브라우저 테스트
php -S 127.0.0.1:8000 -t php/public &
# http://127.0.0.1:8000/documents (또는 설치 필수 페이지)
# http://127.0.0.1:8000/login
# 각 페이지 렌더링, 폼 표시, 오류 메시지 등을 시각적으로 확인
```

위 명령이 모두 성공하고, 각 라우터가 HTML을 서버 렌더링하면 조건 1-7이
충족된 것이다.

## 이 문서 작성 시점 스냅샷 (Phase D 종료, 0521-0610)

이 문서를 추가하는 시점(0570, Phase D 중반 gate)에 위 재판정 절차를 실행한 결과는
다음과 같다.

- 조건 1: `scripts/test.sh`, `scripts/qa.sh`(php CLI 포함) 통과.
- 조건 2: 핵심 라우터(문서 조회/생성/수정/목록, 로그인, 오류 페이지 등)이
  `php/src/Http/` 및 `php/src/Ui/` 에 구현되어 있고, 서버 렌더링으로 동작.
- 조건 3: `php/tests/Modules/Document/HtmlEscapingTest.php` 및 0567(XSS fixtures)
  가 escape를 검증하고, 자동화가 통과함.
- 조건 4: 모든 state-changing 폼이 `<form method="POST">` 구조를 가지고 있고,
  CSRF token 필드를 넣을 수 있는 위치가 확보됨.
- 조건 5: `php/tests/Http/SecurityHeadersTest.php` 가 security header 존재를
  검증하고 통과함.
- 조건 6: `php/tests/UI/MobileTest.php` 가 viewport/media query를 확인하고,
  CSS 파일이 모바일 breakpoint를 정의함.
- 조건 7: `php/tests/UI/AccessibilityBaselineTest.php` 가 lang/landmark/alert
  요소를 검증하고 통과함.

**판정: PASS** — Phase D(Server-rendered UI, 0521-0610) 완료. 웹호스팅 배포
준비 가능 상태. 단, 실제 Phase E(0611+) 배포 전에는 위 "재판정 방법" 절차를
다시 한 번 실행하여 그 이후 코드 변경이 없음을 확인한다.

## Phase D 진입 시 필수 인식 사항 (UI 개발자 필독)

### 웹호스팅 배포를 기본값으로 삼기

Phase D UI 코드는 다음을 전제로 설계되었다:
- PHP + MariaDB shared hosting 배포가 기본 대상.
- 별도 Node build, CDN 필수, SPA 기반 라우팅을 요구하지 않음.
- 브라우저가 그대로 읽을 수 있는 HTML/CSS/JavaScript 파일만 배포.

따라서 Phase D 신규 코드는:
- [ ] 서버 렌더링 라우터만 추가한다 (API-first 아키텍처 미사용).
- [ ] Sass/TypeScript/bundler 설치 없이 브라우저가 읽을 수 있는 CSS/JS를 배포한다.
- [ ] Node 기반 build step을 추가하지 않는다.
- [ ] 첫 화면을 JavaScript가 조립하는 구조를 만들지 않는다.

### 보안 경계

- 템플릿은 도메인 규칙(권한 판정, 문서 정규화, revision 생성)을 구현하지 않는다.
  라우터/application service가 데이터를 prepare 한 후 템플릿에 전달한다.
- 모든 HTML 출력은 **기본이 escaping**이다. Raw HTML 삽입은 renderer 모듈처럼
  신뢰 경계가 명확한 값에만 허용한다.
- state-changing 폼은 post-submission에 CSRF token 검증을 위해 구조를 미리 잡아둔다.

### DB/PHP 저장소와의 경계

- UI 라우터는 저장소(`src/Modules/*/Repository.php`) 또는 application service를
  통해서만 DB에 접근한다. ORM(SQLAlchemy/Doctrine) 직접 사용 금지.
- 오류 처리: DB 연결 실패 시 stack trace가 아니라 "일시적 오류" 메시지를
  사용자에게 표시하고, 운영자/관리자용 진단 페이지(0590)로 별도 안내.

## Phase D 완료 체크리스트

Phase D가 정말로 끝났는지 확인하기 위한 최종 점검표:

### D.1 라우터 및 템플릿 ✓

- [ ] 모든 핵심 라우터(`/documents/<id>`, `/documents/new`, `/login` 등)가
      `php/src/Http/` 에 구현되어 있다.
- [ ] 각 라우터가 권한(ACL) 검사 후 `php/src/Ui/` 템플릿을 렌더링한다.
- [ ] 모든 템플릿이 사용자 입력을 HTML escape 처리한다.
- [ ] 오류 페이지(404, 403, 500, 503)가 구현되어 있다.

### D.2 보안 ✓

- [ ] HTML escaping 테스트 통과 (`php/tests/Modules/Document/HtmlEscapingTest.php`).
- [ ] 보안 헤더 테스트 통과 (`php/tests/Http/SecurityHeadersTest.php`).
- [ ] CSRF token 필드 구조 준비 (모든 state-changing 폼).
- [ ] 0567(XSS regression fixtures) 통과.

### D.3 접근성 및 모바일 ✓

- [ ] 접근성 테스트 통과 (`php/tests/UI/AccessibilityBaselineTest.php`).
- [ ] 모바일 테스트 통과 (`php/tests/UI/MobileTest.php`).
- [ ] 폼 오류 요약 테스트 통과 (`php/tests/UI/FormErrorSummaryTest.php`).
- [ ] 모든 페이지가 viewport meta 태그와 mobile-first CSS를 가진다.

### D.4 정적 Asset ✓

- [ ] CSS 파일이 `php/public/assets/css/` 에 있고, 모바일 media query를 포함한다.
- [ ] JavaScript가 `php/public/assets/js/` 에 있고, progressive enhancement 기반이다.
- [ ] 이미지/아이콘이 `php/public/assets/images/` 에 있고, alt 텍스트를 가진다.

### D.5 자동 검사 ✓

- [ ] `scripts/test.sh` 통과.
- [ ] `scripts/qa.sh` 통과.
- [ ] `php/scripts/qa.sh` 통과 (php CLI 환경).

### D.6 문서화 ✓

- [ ] `docs/php-ui-phase-qa-checklist.md` 완성 (회귀 검사 기준).
- [ ] `docs/php-ui-architecture.md` 완성 (아키텍처).
- [ ] `docs/php-static-asset-serving.md` 완성 (asset 정책).
- [ ] `docs/php-ui-readiness-gate.md` 완성 (이 문서).
- [ ] Phase E 시작 문서 준비 (`docs/shared-hosting-migration-policy.md` 참고).

### D.7 코드 리뷰 ✓

- [ ] 라우터 경계: UI가 저장소를 통해서만 DB 접근.
- [ ] 보안: 모든 사용자 입력이 HTML escape 또는 URL 검증 처리됨.
- [ ] 모바일: 모든 interactive element가 44x44px 최소 크기를 가짐.
- [ ] 오류 처리: 민감한 정보 노출 없음, 사용자에게 명확한 안내.

## Gate 미통과 시 조치

아래 항목 중 하나라도 미충족 시 **Phase E 진입 금지**:

| 상태 | 원인 | 조치 |
|---|---|---|
| `scripts/qa.sh` 실패 | 자동 검사 위반 (security header, XSS, accessibility 등) | Phase D 내 정책 준수 작업 추가 |
| 라우터/템플릿 누락 | 핵심 화면 미구현 | 누락된 라우터/템플릿 구현 (Phase D 범위 내) |
| Escaping 위반 | 사용자 입력이 raw HTML로 출력됨 | 해당 템플릿/라우터의 escape 호출 추가 |
| 보안 헤더 누락 | HTTP 응답이 security header를 포함하지 않음 | HTTP 미들웨어에 헤더 추가 |
| 접근성 기초 미충족 | lang/landmark/label/alert 요소 누락 | 템플릿에 접근성 요소 추가 |
| 모바일 기초 미충족 | viewport/mobile CSS 부재 | CSS에 media query/viewport 추가 |

## 다음 단계로의 전환 (Phase E Handoff)

### Phase E 개발자가 가져가야 할 것

1. **문서**:
   - `docs/php-ui-phase-qa-checklist.md` — UI 회귀 검사 기준 유지.
   - `docs/php-ui-readiness-gate.md` — 웹호스팅 배포 전 최종 조건.
   - `docs/shared-hosting-migration-policy.md` — 호스팅 제약 가이드.
   - `docs/db-web-hosting-constraints.md` — DB 권한/charset/마이그레이션 제약.

2. **코드**:
   - `php/src/Http/` — 라우터 구현.
   - `php/src/Ui/` — 템플릿 구현.
   - `php/public/assets/` — 정적 asset.
   - `php/tests/UI/` — UI 자동 테스트.

3. **제약**:
   - Phase D 정책(서버 렌더링, Node build 불필요, escaping 기본)을 위반하는 코드 추가 금지.
   - 보안/접근성/모바일 기초를 하향 조정하지 않기.

### Phase E 진입 조건

```
Phase E(0611+) 시작 <==> 다음 모두 만족:
  1. scripts/test.sh, scripts/qa.sh 통과 ✓
  2. 모든 핵심 라우터/템플릿 구현 ✓
  3. HTML escaping/CSRF/security header 기초 완성 ✓
  4. 접근성/모바일/오류 상태 기초 완성 ✓
  5. 리뷰: 서버 렌더링, 보안 경계, 웹호스팅 제약 회피 확인됨 ✓
```

### 연계 작업

Phase E 내 UI 관련 작업:
- `docs/shared-hosting-migration-policy.md`: 호스팅 배포 정책.
- `0611+`: 파일 권한, htaccess/nginx rewrite, 설정 파일 등 배포 인프라.

## 관련 문서

- `docs/php-ui-architecture.md` — Phase D 전체 UI 아키텍처 원본.
- `docs/php-ui-phase-qa-checklist.md` — Phase D 회귀 검사 기준.
- `docs/php-static-asset-serving.md` — 정적 asset 정책.
- `docs/php-runtime-security-baseline.md` — security 기준의 원본.
- `docs/php-runtime-phase-qa-checklist.md` — Phase B QA 체크리스트 형식.
- `docs/db-phase-readiness-gate.md` — Phase C readiness gate (형식 참고).
- `docs/php-replacement-readiness-gate.md` — Phase B readiness gate (형식 참고).
- `docs/shared-hosting-migration-policy.md` — Phase E 호스팅 배포 정책.
- `docs/db-web-hosting-constraints.md` — 웹호스팅 DB 제약.
- `php/tests/UI/` — UI 자동 테스트 디렉터리.
- `php/src/Ui/` — 템플릿 구현 위치.
- `php/src/Http/` — 라우터 구현 위치.
- `php/public/assets/` — 정적 asset 위치.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase D(0521-0610) 전체 태스크 목록.
