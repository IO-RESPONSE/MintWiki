# PHP UI Phase (Phase D) QA Checklist

이 문서는 로드맵 **Phase D: Server-rendered UI after PHP and DB, 0521-0610**
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`) 의 산출물이 회귀 없이
유지되고 있는지 확인하기 위한 체크리스트다. `docs/db-phase-qa-checklist.md`
가 Phase C를 다루는 것처럼, 이 문서는 Phase D 산출물(UI 템플릿/라우터/정적
asset/폼/오류 페이지)을 새로 추가·수정한 뒤, 또는 커밋 전 `scripts/qa.sh`
와는 별개로 "웹호스팅 친화적인 서버 렌더링 UI가 접근성/보안/모바일/오류
상태를 모두 만족하는가"를 사람이 다시 훑어볼 때 사용한다.

`docs/php-runtime-phase-qa-checklist.md`, `docs/db-phase-qa-checklist.md`
와 동일한 형식을 따른다 — 각 항목은 "무엇을 확인하는가"와 "어떤 자동화가
이미 이를 커버하는가"를 함께 적는다. 자동화가 있다고 해서 항목을 건너뛰어도
된다는 뜻은 아니다.

이 체크리스트는 Phase D 노트에서 지명한 네 영역 — **접근성(accessibility),
보안(security), 모바일(mobile), 오류 상태(error states)** — 을 절 단위로
다룬다.

## 사용법

```bash
cd php && composer install && cd -
php/scripts/qa.sh
.venv/bin/python -m pytest tests/test_php_qa_scripts.py -v
php -S 127.0.0.1:8000 -t php/public &
# 브라우저에서 http://127.0.0.1:8000 방문 후 아래 절 항목들을 수동 확인
```

위 명령으로 PHP QA 자동 검사를 실행하고, `php -S`로 로컬 서버를 띄운 후
브라우저에서 각 화면을 직접 테스트할 수 있다. 개별 실행 후에는 반드시
`scripts/test.sh`와 `scripts/qa.sh`도 통과해야 한다 — `php` CLI가 있는
환경에서는 `scripts/qa.sh`가 `php/scripts/qa.sh`를 선택 실행하므로(0431),
`php` CLI가 있는 환경에서는 `scripts/qa.sh` 통과만으로 아래 1절 일부가
사실상 자동으로 확인된다. 2~4절(보안/모바일/오류 상태)은 사람이 브라우저
또는 개발자 도구에서 직접 확인해야 하는 항목이 대부분이다.

## 1. 접근성(Accessibility)

UI 화면이 WCAG 2.1 AA 수준의 접근성 기준을 만족하고, 마크업이 의미론적으로
정확한지 확인한다. 해당 태스크: 0528(baseline tests), 0523(escaping tests),
0542(error summary), 0543(flash messages).

### 1.1 HTML 시맨틱 구조

- [ ] 모든 페이지가 `<html lang="ko">` 속성을 가진다 — 화면 낭독기가
      문서 언어를 올바르게 식별한다. See
      `php/tests/UI/AccessibilityBaselineTest.php`.
- [ ] 모든 페이지가 `<meta name="viewport" content="width=device-width, initial-scale=1">`
      을 헤드에 포함한다 — 모바일 브라우저가 스케일을 제대로 설정한다.
- [ ] 페이지 레이아웃이 `<header>`, `<main>`, `<footer>` landmark 요소를
      사용한다 — 스크린 리더 사용자가 영역을 탐색할 수 있다.
- [ ] 각 페이지의 첫 제목이 `<h1>` 이며, 목차(outline) 계층이 순서대로
      내려간다(h1 → h2, h2 → h3). `<h2>`에서 바로 `<h4>`로 뛰지 않는다.
- [ ] 폼 필드(`<input>`, `<textarea>`, `<select>`)가 모두
      `<label for="id">` 로 명시적으로 레이블되어 있다. 숨겨진 placeholder만
      사용하지 않는다.
- [ ] 폼이 존재하면 `<form>` 요소로 감싸고, 제출 버튼이 `type="submit"`이다.
- [ ] 네비게이션 메뉴가 `<nav>` 요소로 감싸진다.
- [ ] 문서 목록/검색 결과/감사 로그 같은 data table이 `<table>` 요소를
      사용하고, `<thead>`/`<tbody>` 등으로 구조화된다. 레이아웃만 위해
      테이블을 남용하지 않는다.

**자동화**: `php/tests/UI/AccessibilityBaselineTest.php`가 `lang`/`viewport`
/landmark 존재를 검증한다 (`php/scripts/qa.sh` 경유). 제목 계층과 라벨은
사람이 HTML을 읽고 확인해야 한다.

### 1.2 폼 오류 표시

- [ ] 폼 제출 시 유효성 오류가 발생하면, 오류 목록이 폼 위에
      `<div role="alert">` 로 감싸진 형태로 먼저 표시된다 — 스크린 리더가
      오류를 먼저 알게 된다. See `php/tests/UI/FormErrorSummaryTest.php`.
- [ ] 오류 목록의 각 항목이 해당 폼 필드로의 링크(`#field-id`)를 포함한다.
- [ ] 오류가 있는 필드의 `<input>` 또는 `<label>` 근처에 시각적 표시(예:
      빨간 테두리, 경고 아이콘)가 있다.
- [ ] 오류 메시지 자체가 스크린 리더가 읽을 수 있는 텍스트이지, 색상만으로
      구분되지 않는다.

**자동화**: `php/tests/UI/FormErrorSummaryTest.php`가 `role="alert"` 및
링크 존재를 검증한다 (`php/scripts/qa.sh` 경유). 시각적 표시와 색상 사용은
사람이 브라우저에서 확인한다.

### 1.3 이미지와 아이콘

- [ ] 모든 `<img>` 요소가 의미 있는 `alt` 텍스트를 가진다 — 이미지 없이도
      문서 내용을 이해할 수 있어야 한다.
- [ ] 순수 장식 이미지(예: 배경 패턴)는 `alt=""`로 표시하거나, CSS 배경
      이미지로 처리한다.
- [ ] 아이콘이 텍스트 버튼과 함께 있으면 아이콘에만 `aria-hidden="true"`
      를 주어 낭독을 피한다. 아이콘만 있으면 `aria-label` 로 레이블한다.

**자동화**: 자동 검사 없음. 사람이 HTML과 브라우저 DevTools를 통해 확인.

### 1.4 포커스와 키보드 네비게이션

- [ ] 모든 상호작용 요소(버튼, 링크, 폼 입력)이 탭(Tab) 키로 접근 가능하다.
- [ ] 포커스 가능한 요소에 시각적 포커스 표시기(예: outline, 배경색 변화)가
      있다. 기본 브라우저 포커스 스타일을 완전히 제거하지 않는다.
- [ ] 모달이나 dropdown이 나타났을 때 포커스가 그 요소 안에 갇혀 있고,
      escape 키나 닫기 버튼으로 이전 포커스로 돌아간다(포커스 트레핑).
- [ ] 긴 폼에서 submit 버튼이 보이는 위치에 항상 접근 가능하거나, 스크롤하지
      않고도 키보드로 제출할 수 있다.

**자동화**: 자동 검사 없음. QA 시 개발자 도구의 Accessibility inspector나
키보드 네비게이션 직접 테스트로 확인.

### 1.5 색상과 명도 대비

- [ ] 모든 텍스트(일반 텍스트, 폼 라벨, 버튼 레이블, 링크, 오류 메시지)가
      배경과 4.5:1 이상의 명도 대비를 가진다(WCAG AA). 큼지막한 텍스트는
      3:1 이상. 참고: `docs/ui-design-token-css.md`.
- [ ] 색상만으로 정보를 전달하지 않는다 — 오류는 빨간색 + 텍스트, 경고는
      노란색 + 텍스트 아이콘, 성공은 초록색 + 체크마크 등으로 표시한다.

**자동화**: 자동 검사 없음. WebAIM Contrast Checker나 WebStorm의 color
checker로 확인. CSS token에서 색상을 정의한 경우는 이미 기준을 만족해야 한다
(0527: design token CSS).

### 1.6 동적 콘텐츠와 ARIA

- [ ] AJAX나 JavaScript로 콘텐츠가 동적으로 업데이트되면
      `aria-live="polite"` 또는 `aria-live="assertive"` 로 표시하여 스크린
      리더가 업데이트를 알게 된다.
- [ ] 페이지 제목(`<title>`)이 내용을 반영하고, 새 페이지 로드 또는 SPA
      라우트 변경 시 제목이 변경된다.
- [ ] 로딩 상태나 버튼 비활성화 상태가 `aria-busy="true"` 또는
      `aria-disabled="true"` 로 표시되고, 스크린 리더가 상태 변화를 감지할 수
      있다.

**자동화**: 자동 검사 없음. 동적 콘텐츠가 아직 없는 Phase D 초반에는 주로
폼 제출 직후 오류/성공 메시지 표시에만 적용된다 (0543: flash messages).

## 2. 보안(Security)

UI 계층에서 XSS, CSRF, 보안 헤더, 오류 정보 노출 등을 막는지 확인한다.
해당 태스크: 0523(escaping tests), 0554(security headers), 0541(CSRF),
0567(XSS fixtures), 0571(search snippet escape).

### 2.1 HTML Escaping

- [ ] 모든 사용자 입력 유래 문자열이 HTML로 출력되기 전에 escape 처리된다.
      기준: `htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5, 'UTF-8')`
      또는 동등한 함수. 특히:
      - 문서 제목 (document title, create/edit 폼)
      - 문서 source/content
      - 사용자명
      - 검색 쿼리
      - 폼 오류 메시지
  모두 escape 처리된 문자열로만 HTML에 삽입된다.
- [ ] PHP 템플릿이 `<?= $value ?>` 형태로 직접 출력할 때, `$value` 는 이미
      escaped 문자열이거나, 헬퍼 함수(`escape()` 또는 유사)를 통해 escape된다.
      Raw 문자열을 절대 직접 출력하지 않는다.
- [ ] 문서의 rendered HTML(`render()` 모듈 출력)은 신뢰할 수 있는 소스이므로
      raw HTML 삽입이 허용되지만, 다른 모든 사용자 입력은 escape된다. See
      `php/src/Http/Response.php`, `docs/php-runtime-security-baseline.md`.
- [ ] Escape 함수 테스트(`php/tests/Modules/Document/HtmlEscapingTest.php` 또는
      `php/tests/UI/HtmlEscapingTest.php`)가 XSS payload(`<script>`,
      `" onclick="`, `&#x27;` 등)를 검증한다. See 0523.

**자동화**: `php/tests/Modules/Document/HtmlEscapingTest.php`와 0567(XSS
regression fixtures)이 이미 PHP fixture 러너로 escape를 검증한다 (`php/scripts/qa.sh`
경유). 그 외 새로운 UI 화면에 대해서는 사람이 소스 코드의 escape 호출을
리뷰해야 한다.

### 2.2 URL Escaping과 스킴 검증

- [ ] 사용자 입력으로부터 만든 URL(검색 결과 링크, 문서 링크 등)이
      Python 쪽 `src/modules/render/url_sanitizer.py` 의 allowlist 원칙을 따른다.
      허용 스킴: `http`, `https`, `ftp`, `ftps`, `mailto`, `tel`, `sms`, `geo`.
      위험 스킴(`javascript:`, `data:`, `vbscript:`) 차단.
- [ ] 동적으로 생성된 폼의 `action` 속성이나 리다이렉트 target도 같은
      원칙의 검증을 거친다.

**자동화**: 자동 검사 없음. 사람이 링크와 폼 action 정의를 코드 리뷰로 확인.

### 2.3 CSRF 방어

- [ ] 상태 변경 폼(문서 생성/수정, 사용자 차단, 감사 로그 export 등)이 모두
      CSRF token을 포함한다. Token은 session 또는 signed value로 생성되고,
      `<input type="hidden" name="csrf_token" value="...">` 형태로 폼에 포함된다.
- [ ] 폼 제출 시 서버가 token을 검증하고, 검증 실패 시 폼 제출을 거부한다.
  오류 응답은 403 Forbidden이거나, flash message로 "유효하지 않은 요청"을 표시한다.
- [ ] GET 요청만 발생하는 화면(문서 보기, 검색 결과, 최근 변경 등)에는
      token이 불필요하다. 변경이 일어나는 모든 폼에만 token이 있다.
- [ ] JavaScript로 폼을 동적으로 조작하는 경우에도 token이 포함되거나, API
      요청이 token을 검증한다. See `php/src/Security/CsrfTokenService.php` (0540),
      `php/tests/UI/FormCsrfTest.php` (0541).

**자동화**: `php/tests/UI/FormCsrfTest.php`가 폼 token 존재와 검증 실패 처리를
테스트한다 (`php/scripts/qa.sh` 경유). 새로운 state-changing 라우트마다
체크리스트 항목으로 수동 확인.

### 2.4 보안 HTTP 헤더

- [ ] 모든 HTTP 응답이 다음 헤더들을 포함한다 — See 0554:
      - `X-Content-Type-Options: nosniff` — MIME 스니핑 방지.
      - `X-Frame-Options: DENY` 또는 `SAMEORIGIN` — clickjacking 방지.
      - `X-XSS-Protection: 1; mode=block` — 구식 브라우저의 XSS 필터 활성화.
- [ ] Content-Security-Policy(CSP) 헤더는 아직 선택이지만, 기본값은
      `default-src 'self'` 같은 제한적 정책이다. inline script와 eval을 금지한다.
- [ ] 쿠키가 있으면 `Secure`, `HttpOnly`, `SameSite=Strict` 또는
      `SameSite=Lax` 속성을 가진다. See 0634.
- [ ] 민감한 캐시(로그인 페이지, 개인 문서)에는 `Cache-Control: no-store, no-cache`
      를 반환하고, 공개 콘텐츠는 짧은 캐시 시간을 설정한다.

**자동화**: `php/tests/Http/SecurityHeadersTest.php`(0554에서 예상)가 header
존재를 검증한다. 실제 헤더 설정은 사람이 브라우저 DevTools(Network tab)에서
확인한다.

### 2.5 오류 정보 노출 방지

- [ ] 5xx 오류 페이지에서 stack trace, 데이터베이스 연결 문자열, 절대 경로 등
      민감한 기술 정보를 노출하지 않는다.
- [ ] 개발 환경이 아닌 한, 오류 페이지는 일반적인 메시지("문제가 발생했습니다")
      만 표시하고, 기술 세부사항은 서버 로그에만 기록한다.
- [ ] 4xx 오류(404 Not Found, 403 Forbidden 등)에 민감한 정보 없음 확인.

**자동화**: 자동 검사 없음. 운영자가 5xx 오류 트리거 후 응답을 확인하거나,
로그 설정을 사람이 리뷰.

## 3. 모바일(Mobile)

UI가 다양한 화면 크기에서 반응형으로 동작하고, 터치 입력을 지원하는지 확인한다.
해당 태스크: 0566(mobile CSS tests), 0556(print stylesheet).

### 3.1 반응형 디자인

- [ ] 모든 페이지가 viewport meta 태그를 가진다 (1.1절 참고):
      `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- [ ] CSS가 미디어 쿼리(`@media (max-width: ...)`)를 사용하여, 모바일(~480px),
      태블릿(480px~768px), 데스크톱(768px~) 세 가지 breakpoint에서 레이아웃을
      조정한다.
- [ ] 모바일에서:
      - 텍스트가 읽기 좋은 크기(16px 이상)를 유지한다.
      - 버튼과 클릭 가능 요소의 touch target이 최소 44x44px이다.
      - 네비게이션 메뉴가 hamburger 메뉴로 접힌다.
      - 수평 스크롤이 없다.
- [ ] 태블릿에서 2열 레이아웃이 가능하다면 활용하고, 여전히 터치 친화적이다.
- [ ] CSS 파일이 로드되지 않았을 때도 콘텐츠가 단일 열로 읽을 수 있다
      (mobile-first progressive enhancement).

**자동화**: `php/tests/UI/MobileTest.php` (0566)가 media query와 viewport
존재를 확인한다 (`php/scripts/qa.sh` 경유). 실제 반응형 동작과 touch
target 크기는 브라우저 DevTools(device emulation) 또는 실제 모바일 기기에서
검증.

### 3.2 터치 입력

- [ ] 폼 입력(텍스트 필드, select, checkbox 등)이 모바일에서 명확한
      터치 영역을 가진다. 작은 아이콘 버튼이나 radio의 경우, hidden
      `<label>` 로 감싸서 터치 영역을 확대한다.
- [ ] 호버 상태(`:hover`)에만 표시되는 정보(tooltip 등)가 아래 대안을
      가진다:
      - 터치 기기에서는 이 정보가 자동으로 표시되거나,
      - 탭하면 표시되거나,
      - 호버 정보 대신 항상 표시된 다른 표시(예: 아이콘)가 있다.
- [ ] 링크나 버튼이 의도하지 않은 double-tap 확대를 트리거하지 않는다 —
  또는 CSS `touch-action` 으로 확대를 명시적으로 제어한다.

**자동화**: 자동 검사 없음. 모바일 기기나 브라우저 devtools의 device
emulation에서 수동 확인.

### 3.3 프린트 스타일

- [ ] CSS `@media print` 규칙이 인쇄 환경에서 보이면 안 되는 요소(네비게이션,
      폼, 사이드바 등)를 숨긴다.
- [ ] 문서 보기 페이지의 프린트 스타일(`php/public/assets/css/print.css`, 0556)이
      문서 본문은 보이게 하고 액션 버튼/네비게이션은 숨긴다.
- [ ] 프린트 스타일에서 배경색이나 이미지가 인쇄 환경에서 낭비되지 않도록
      최소화되어 있다.

**자동화**: `php/tests/UI/PrintStyleTest.php` (0556)가 파일 존재를 확인한다.
실제 프린트 결과는 브라우저의 Print Preview에서 확인.

## 4. 오류 상태(Error States)

사용자가 에러를 마주했을 때 명확한 안내와 회복 경로를 제공하는지 확인한다.
해당 태스크: 0539(permission denied), 0542(error summary), 0588(install required),
0592(error page integration).

### 4.1 HTTP 오류 페이지

- [ ] 404 Not Found 오류일 때, 사용자가 찾는 문서가 없음을 명확히 설명하고,
      홈으로 돌아가기, 검색, 최근 변경 같은 복구 옵션을 제공한다.
- [ ] 403 Forbidden(접근 권한 없음)일 때:
      - 현재 사용자가 로그인되어 있는지 표시한다.
      - 로그아웃 상태면 "로그인하면 접근할 수 있습니다" 안내.
      - 로그인했으나 권한 없으면 "이 문서는 비공개입니다" 또는 "관리자에게 문의하세요" 안내.
- [ ] 500 Internal Server Error일 때, 기술 세부사항 없이 "문제가 발생했습니다"
      메시지와 지원 연락처(이메일, 티켓 링크 등)를 제시한다.
- [ ] 503 Service Unavailable (maintenance 중)일 때, "현재 유지보수 중입니다"
      메시지와 예상 복구 시간(가능하면)을 표시한다.
- [ ] 모든 오류 페이지가 일관된 페이지 레이아웃(header/main/footer)을 유지하고,
      CSS가 로드되지 않았을 때도 가독성 있는 텍스트로 메시지가 표시된다.

**자동화**: `php/tests/Http/ErrorPageIntegrationTest.php` (0592)가 페이지
존재와 상태 코드를 검증한다. 사용자 경험(안내 명확성, 복구 옵션)은 사람이
브라우저에서 직접 테스트.

### 4.2 폼 유효성 검사 오류

- [ ] 필수 필드가 비어 있으면: "제목은 필수입니다" 같은 구체적 메시지.
- [ ] 중복된 제목이면: "같은 제목의 문서가 이미 있습니다" 안내와, 기존 문서로의 링크.
- [ ] 폼 오류 시 페이지를 리로드하지 않고 같은 페이지에서 오류를 표시한다
      (또는 리로드해도 이전 입력값이 폼에 남아 있다).
- [ ] 오류 메시지가 `<div role="alert">` 로 포장되어 스크린 리더가 오류를
      먼저 알게 된다 (2절 참고).

**자동화**: `php/tests/UI/FormErrorSummaryTest.php` (0542)가 오류 요약 페이지
구조를 검증한다. 실제 폼 동작은 사람이 테스트.

### 4.3 데이터베이스 연결 오류

- [ ] 데이터베이스 연결 실패 시, 사용자에게 stack trace 대신 "일시적 오류"
      메시지를 보여준다.
- [ ] 설치 전 처음 방문한 사용자에게는 0588(install required) 페이지로 안내한다.
- [ ] 유지보수 화면(0589)에 진입할 수 있어야, 관리자가 상태를 확인하고
      복구할 수 있다.

**자동화**: 자동 검사 없음. 운영자가 DB 서비스를 중단한 후 UI 동작을 확인.

### 4.4 Session/Authentication 오류

- [ ] 세션 timeout일 때: "세션이 만료되었습니다. 다시 로그인하세요" 메시지.
- [ ] CSRF token 검증 실패: "요청이 유효하지 않습니다. 다시 시도하세요" 메시지.
- [ ] 차단된 사용자가 로그인 시도: "이 계정은 차단되었습니다" 안내.
- [ ] 사용자가 차단된 후 이전 세션에서 페이지에 접근: 0539(permission denied)
      페이지로 안내.

**자동화**: 자동 검사 없음. QA가 세션 설정/차단 상태를 테스트.

### 4.5 Disabled/Loading 상태

- [ ] 폼 제출 중 submit 버튼이 비활성화(disabled)되거나, 로딩 상태 표시
      (`aria-busy="true"` + 스피너 아이콘/텍스트)가 나타난다 — 중복 제출 방지.
- [ ] 로딩 중 버튼 텍스트가 "저장 중..." 같이 상태를 반영한다.
- [ ] 로딩이 완료되면 버튼이 다시 활성화되고, 성공/실패 메시지가 표시된다.
- [ ] 로딩 상태가 너무 길어지지 않도록, 서버 응답 timeout은 적절한 값으로
      설정된다 (보통 30초 이내).

**자동화**: `php/tests/UI/ButtonLoadingStateTest.php` (0575)가 CSS 클래스 존재를
검증한다. 실제 로딩 UX는 폼 제출 테스트로 확인.

## 5. 자동 검사 통합

아래 명령들이 위 체크리스트의 자동화 항목들을 모두 커버한다.

```bash
# 로컬 개발 중 (언제든 수동 실행)
php/scripts/qa.sh              # PHP QA (escaping, security headers 등)
.venv/bin/python -m pytest tests/test_php_qa_scripts.py -v
.venv/bin/python -m pytest tests/test_qa_script_php_hook.py -v

# 또는 루트 QA (PHP CLI가 있는 경우 자동 포함)
scripts/qa.sh
scripts/test.sh
```

### CI 경로

Runner가 매 태스크 완료 후 자동 실행:

```bash
scripts/test.sh   # 전체 테스트 포함 (php 클래스 테스트도 포함)
scripts/qa.sh     # PHP QA 자동 선택 실행
```

## 6. 이 체크리스트가 다루지 않는 것

- Phase E(Shared Hosting Packaging, 0611-0670)의 배포/운영 조건 —
  웹호스팅 권한/파일 구조/설정 파일은 별도 phase.
- 접근성 WCAG 2.1 AAA 수준 — AA 수준만 목표.
- 국제화(i18n) 다국어 지원 — 현재 기본 locale은 ko (0558).
- 성능 최적화(캐시 전략, CDN, lazy loading) — 성능 budget은 0579/0580.
- 검색 엔진 최적화(SEO) 상세 구현 — 기본만 0594/0595.
- 마이그레이션, 복구, 백업 UI — 설치기와 운영 페이지는 후속.

## 관련 문서

- `docs/php-ui-architecture.md` — Phase D 전체 UI 아키텍처 원본.
- `docs/php-static-asset-serving.md` — asset 서빙 정책.
- `docs/php-runtime-security-baseline.md` — security 기준의 원본.
- `docs/php-runtime-phase-qa-checklist.md` — Phase B QA 체크리스트 형식.
- `docs/db-phase-qa-checklist.md` — Phase C QA 체크리스트 형식.
- `docs/portability-phase-qa-checklist.md` — Phase A QA 체크리스트 형식.
- `docs/php-replacement-readiness-checklist.md` — 모듈별 ready 기준.
- `php/tests/UI/` — UI 자동 테스트 디렉터리.
- `php/src/Ui/` — 템플릿/라우터 구현 위치.
- `php/public/assets/` — 정적 asset 위치.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase D(0521-0610)
  전체 태스크 목록.
