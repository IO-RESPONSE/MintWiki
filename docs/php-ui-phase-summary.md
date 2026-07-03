# PHP UI Phase Summary

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 완료 요약.
이 문서는 Phase E (Shared Hosting Packaging, 0611+) 개발자가 Phase D에서 구축한 UI 계층을 사용할 때
반드시 지켜야 할 경계, 제약, 보장을 한 곳에 정리한다. UI 계층의 세부 구현을 학습하기보다는 **배포/운영 시 의존할 수 있는 것과 금지된 것**을 빠르게 파악하기
위한 가이드다.

## 목적

Phase D에서는 PHP 런타임과 ANSI SQL DB 위에 웹호스팅 친화적인 서버 렌더링 UI를 구축했다. Phase E부터 설치기/배포/운영 기능을 추가할 때, 개발자는:

1. **어떤 라우트와 페이지가 사용자에게 노출되는가** (public 경로, 권한별 접근)
2. **어떤 HTML/asset 보장이 있는가** (XSS 방지, cache 정책)
3. **어떤 폼 제약이 있는가** (CSRF, 중복 제출 방지)
4. **어떤 진단/유지보수 기능이 있는가** (installer, maintenance mode, diagnostics)
5. **무엇을 피해야 하는가** (template 직접 조작, static asset 캐시 우회, CSRF 우회)

…을 알아야 한다. 이 문서는 그 정보를 모두 담는다.

## 대상

- Phase E (Shared Hosting) 개발자 — 설치기, 배포 스크립트, 운영 도구
- 아키텍처 리뷰어 — UI 계층과 운영 계층 사이의 경계 검증
- 운영/QA — UI 계층 안정성 가정 확인
- 호스팅 관리자 — 권한 설정, 파일 구조, 유지보수 절차

## 1. 공개 라우트와 접근 제어

### 1.1 라우트 분류

모든 라우트는 다음 네 카테고리로 분류된다:

| 분류 | 특징 | 권한 검사 | 예시 |
|---|---|---|---|
| **Public** | 인증 불필요 | 없음 또는 ACL 읽기만 | `/`, `/document/{id}` 읽기 |
| **Authenticated** | 로그인 필수 | `UserService.authenticate()` | `/document/create`, `/admin` |
| **Admin-only** | 관리자만 접근 | `AclService.check(admin, action)` | `/admin/audit`, `/admin/users` |
| **Installer** | 초기 설치 단계 | 설치 완료 상태 검사 | `/installer/welcome`, `/installer/db-config` |

**규칙:**
- 모든 라우트는 `php/src/Http/Router.php` 에 선언된다.
- 라우트 핸들러는 명시적으로 권한을 검사하거나, middleware에서 검사한다.
- 접근 불가 상태는:
  - 미인증: `/login` 으로 리다이렉트 (또는 login page placeholder 반환)
  - 권한 없음: `/permission-denied` 또는 403 상태
  - 설치 필수: `/installer/welcome` 으로 리다이렉트 (또는 install required page 반환)

### 1.2 금지된 라우트 접근 패턴

**다음을 하지 말 것:**

```php
// ❌ 금지됨: 권한 검사 없이 상태 변경
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $document = $documentService->create($title, $source, $userId);
    // 접근 제어 없음!
}

// ❌ 금지됨: 라우터 밖에서 핸들러 직접 호출
require 'src/Http/Handlers/DocumentCreateHandler.php';
handleDocumentCreate();  // 미들웨어 우회

// ❌ 금지됨: installer 접근 제어 우회
if (!$isInstallerCompleted) {
    // installer 상태를 확인하지 않고 진행
}
```

**대신 라우터와 middleware를 통해 호출:**

```php
// ✓ 허용됨
$router->post('/document/create', 'DocumentCreateHandler');
// 라우터가 middleware → 권한 검사 → 핸들러 순서로 실행
```

### 1.3 라우트 parity

Python UI(구식)와 PHP UI(신규)의 라우트 parity matrix는 `docs/ui-route-parity-matrix.md` 에 정의되어 있다.
**Phase E부터는 PHP 라우트를 canonical으로 간주한다** — Python 라우트는 폐기 예정이다.

## 2. HTML 렌더링과 XSS 방지

### 2.1 template 구조

모든 UI 템플릿은 `php/src/Ui/` 아래에 PHP 파일로 작성된다.

| 템플릿 위치 | 용도 | layout 상속 |
|---|---|---|
| `php/src/Ui/layout.php` | 기본 레이아웃 (header/main/footer) | — |
| `php/src/Ui/pages/DocumentView.php` | 문서 보기 | `layout.php` |
| `php/src/Ui/pages/DocumentCreate.php` | 문서 생성 폼 | `layout.php` |
| `php/src/Ui/components/*.php` | 재사용 컴포넌트 | — |

**규칙:**
- 모든 template은 `<?php declare(strict_types=1);` 으로 시작.
- Template 변수는 항상 escaped 되어 출력.
- Rendered HTML (document source)는 신뢰할 수 있는 출력으로, raw HTML 허용.

### 2.2 Escape 정책

사용자 입력 유래 모든 문자열은 출력 전 escape 처리된다.

```php
// ✓ 올바른 방법: 변수를 escape 함수로 감싸기
<?php echo escape($documentTitle); ?>

// ✓ 대안: 이미 escaped 변수 직접 출력
<?php echo $escapedTitle; ?>

// ❌ 금지됨: escaped하지 않은 사용자 입력 직접 출력
<?php echo $_GET['search_query']; ?>

// ❌ 금지됨: render 출력이 아닌 다른 HTML에 raw 삽입
<?php echo $userComment; ?>
```

**escape 함수:**
```php
function escape(string $text, int $flags = ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5): string {
    return htmlspecialchars($text, $flags, 'UTF-8');
}
```

**대상:**
- 문서 제목 (title, heading)
- 문서 source content
- 사용자명
- 검색 쿼리
- 폼 오류 메시지
- 감사 로그 이벤트
- 댓글/토론 텍스트

**신뢰할 수 있는 출력 (escape 불필요):**
- Render 모듈 출력 (마크다운 → HTML 변환 결과)
- 디자인 token CSS 값
- 고정 UI 텍스트 (버튼 레이블, 안내 문구)

**테스트:**
- `php/tests/UI/HtmlEscapingTest.php` — XSS payload 검증
- `php/tests/fixtures/xss_*` — regression fixture

### 2.3 URL 이스케이프와 스킴 검증

URL이 사용자 입력으로부터 동적으로 생성되면, 스킴 allowlist를 검사한다.

**허용 스킴:** `http`, `https`, `ftp`, `ftps`, `mailto`, `tel`, `sms`, `geo`  
**금지 스킴:** `javascript:`, `data:`, `vbscript:` 및 기타 실행 스킴

```php
// ✓ 올바른 방법
$safeUrl = validateUrlScheme($userProvidedUrl, ['http', 'https']);
?>
<a href="<?php echo escape($safeUrl); ?>">Link</a>

// ❌ 금지됨
<a href="<?php echo $userUrl; ?>">Link</a>
```

**테스트:**
- `php/tests/UI/UrlSchemeValidationTest.php` (expected)

## 3. 폼 제출과 CSRF 방어

### 3.1 CSRF token 정책

상태 변경 폼(POST/PUT/DELETE)은 모두 CSRF token을 포함해야 한다.

```php
// 폼 렌더링 시
<form method="post" action="/document/create">
    <input type="hidden" name="csrf_token" value="<?php echo escape($csrfToken); ?>">
    <label for="title">제목</label>
    <input type="text" id="title" name="title" required>
    <button type="submit">생성</button>
</form>

// 서버에서 검증
$service = new CsrfTokenService();
if (!$service->verify($_POST['csrf_token'])) {
    throw new InvalidRequestException('유효하지 않은 요청');
}
```

**token 생성 책임:**
- Template: `$csrfToken = $csrfTokenService->generate();`
- Middleware: token을 자동으로 template 변수로 주입 (향후)

**검증 책임:**
- Handler: `$csrfTokenService->verify($_POST['csrf_token'])`
- 실패 시: 403 Forbidden 또는 flash message로 "요청이 유효하지 않습니다" 반환

**규칙:**
- 모든 state-changing 라우트는 token을 검증한다.
- GET-only 라우트(문서 보기, 검색 결과 등)는 token 불필요.
- AJAX/API 요청도 token이나 동등한 검증(예: signed request header)을 포함해야 한다.

**테스트:**
- `php/tests/UI/FormCsrfTest.php` — token 생성/검증

### 3.2 중복 제출 방지

폼 제출 중 중복 클릭을 방지하기 위해:

1. JavaScript: submit 버튼을 disabled 상태로 설정하거나, 로딩 중 텍스트 표시
2. Server: idempotency key 또는 one-time token을 검증 (선택)

```php
// Template
<button type="submit" id="submit-btn" name="submit-btn">저장</button>
<script>
document.getElementById('submit-btn').addEventListener('click', function() {
    this.disabled = true;
    this.textContent = '저장 중...';
});
</script>

// CSS 기반 (0575)
<button type="submit" class="btn btn--loading">저장</button>
```

**테스트:**
- `php/tests/UI/DuplicateSubmitProtectionTest.php` — disabled state 검증

### 3.3 폼 오류 처리

폼 유효성 검사 실패:

```php
// 오류 발생 시
$errors = [
    'title' => '제목은 필수입니다',
    'source' => '내용은 필수입니다',
];

// 같은 페이지에서 오류 표시
echo renderFormWithErrors('DocumentCreate.php', $errors, $_POST);

// 또는 flash message로 리다이렉트
$flashService->set('error', 'Please fix the errors below');
redirectToReferer();
```

**규칙:**
- 오류는 사용자 입력값과 함께 template에 전달.
- Template이 입력값을 `value=""` 속성에 유지.
- 오류 메시지가 `<div role="alert">` 로 포장되어 스크린 리더에 첫 전달.
- 구체적 오류 메시지("제목은 필수입니다") 제공.

**테스트:**
- `php/tests/UI/FormErrorSummaryTest.php` — alert 구조 검증

## 4. 정적 자산(static asset) 제공

### 4.1 Asset 디렉터리

모든 정적 자산은 `php/public/` 아래에 있어야 한다 (또는 public이 설정한 경로).

| 경로 | 내용 | 캐시 정책 |
|---|---|---|
| `php/public/assets/css/*.css` | 스타일시트 | 1년 (또는 버전 쿼리 포함) |
| `php/public/assets/js/*.js` | JavaScript | 1년 (또는 버전 쿼리 포함) |
| `php/public/assets/images/*` | 이미지 | 1년 (또는 버전 쿼리 포함) |
| `php/public/index.php` | front controller | no-cache |
| `php/public/.htaccess` | Apache rewrite rules | — |

**규칙:**
- Asset URL은 항상 파일이 실제로 존재하는 경로여야 한다.
- Cache busting은 파일 해시 또는 버전 쿼리 매개변수를 사용 (0607).
- CSS/JavaScript는 인라인이 아닌 별도 파일로 분리 (0555).

### 4.2 Cache 헤더 정책

| 자산 종류 | Cache-Control | 이유 |
|---|---|---|
| HTML 페이지 | `no-store, no-cache` | 항상 신선한 콘텐츠 제공 |
| 로그인 페이지 | `no-store, no-cache` | 민감한 콘텐츠 |
| 개인 문서 | `private, max-age=300` | 사용자별 캐시만 허용 |
| CSS/JS (버전/해시 포함) | `public, max-age=31536000` | 변경 불가능, 장기 캐시 |
| 이미지 (버전/해시 포함) | `public, max-age=31536000` | 변경 불가능, 장기 캐시 |
| 공개 문서 | `public, max-age=3600` | 1시간 공개 캐시 |

**설정 위치:**
- `php/src/Http/Response.php` 에 cache header를 설정하는 메서드
- 각 라우트 핸들러가 필요시 override

```php
// ✓ 올바른 방법
$response->setHeader('Cache-Control', 'public, max-age=31536000');
return $response->send('css content');

// ❌ 금지됨: raw 출력으로 header 설정
header('Cache-Control: ...');
echo 'css content';
```

**테스트:**
- `php/tests/Http/CacheHeaderTest.php` — cache header 검증

### 4.3 성능 budget

정적 자산 전체 크기는 다음을 초과하지 않아야 한다:

| 유형 | 목표 | 현황 |
|---|---|---|
| CSS (압축) | <50 KB | — |
| JavaScript (압축) | <30 KB | — |
| 전체 assets | <150 KB | — |

**테스트:**
- `php/tests/UI/PerformanceBudgetTest.php` — asset 크기 검증

## 5. 권한과 ACL 검증

### 5.1 ACL 경계

문서 접근/수정/관리는 `AclService` 를 통해 검증된다.

```php
// ✓ 올바른 방법
$decision = $aclService->check(
    $user,
    $document->id,
    'read'
);
if (!$decision->isAllowed()) {
    throw PermissionDeniedException(...);
}

// ❌ 금지됨: ACL 검사 우회
$document = $documentService->get($documentId);  // 권한 검사 없음
renderDocument($document);
```

**Action 목록:**
- `read` — 문서 보기
- `edit` — 문서 수정 (새 revision 생성)
- `admin` — 사용자 차단, 감사 로그 조회, 설정 변경

**Decision 결과:**
- `allowed=true` → 진행
- `allowed=false, reason='private'` → 로그인 유도 또는 permission denied 페이지
- `allowed=false, reason='blocked'` → 계정 차단 안내

**테스트:**
- `php/tests/Http/AclRouteTest.php` — 각 라우트의 권한 검증

### 5.2 권한 없음 응답

접근 불가 상황 응답:

| 상황 | 상태 코드 | 페이지 |
|---|---|---|
| 미인증 사용자가 protected 자원 접근 | 302 → /login | login page shell |
| 인증됐지만 권한 없음 | 403 | permission-denied page |
| 계정 차단됨 | 403 | permission-denied page |
| 문서 없음 | 404 | not-found page |

## 6. 세션과 인증

### 6.1 Session 저장소

세션은 PHP 기본 file 세션 또는 DB 기반으로 저장된다.

**규칙:**
- Session ID는 URL에 노출되지 않음 (cookie only).
- Cookie: `Secure`, `HttpOnly`, `SameSite=Strict` 속성.
- Session timeout: 설정 가능 (기본 30분).
- 차단된 사용자의 세션 유효성 재검사: 각 요청마다.

```php
// Session 읽기
$userId = $_SESSION['user_id'] ?? null;

// Session 차단
if ($user->isBlocked()) {
    unset($_SESSION['user_id']);
    session_destroy();
    redirect('/login?reason=blocked');
}
```

**테스트:**
- `php/tests/Security/SessionTest.php` (expected)

### 6.2 Authentication 경계

로그인 구현은 Phase E 이후로 연기되어 있다. 현재는 placeholder 페이지만 존재.

## 7. 로깅과 감사(Audit) 훅

### 7.1 Audit 이벤트

사용자 액션은 `AuditService` 를 통해 append-only로 기록된다.

**기록 대상:**
- 문서 생성/수정/삭제
- 사용자 차단/해제
- 관리자 액션 (보고서 export, 감사 로그 조회 등)
- 로그인/로그아웃

**구조:**
```php
$auditService->append(
    event_type: 'CREATE',
    subject: $user->id,
    document_id: $document->id,
    action: 'create_document',
    details: json_encode(['title' => $document->title]),
    timestamp: now(),
);
```

**규칙:**
- Audit log는 삭제될 수 없다 (append-only).
- 로그 조회는 `AuditService` 를 통해서만.
- 관리자만 감사 로그 조회 가능.

**테스트:**
- `php/tests/Modules/Audit/AppendOnlyTest.php` — 삭제 불가 검증

### 7.2 Audit 훅 placeholder

현재 Phase D에서는 audit 훅이 no-op(무작동) 상태다. Phase E에서 실제 audit 로깅 연결.

```php
// ✓ 올바른 방법: 핸들러에서 audit 호출
$documentService->create($title, $source, $userId);
$auditService->append(
    event_type: 'CREATE',
    subject: $userId,
    document_id: $document->id,
    ...
);

// ❌ 금지됨: audit 로깅 없이 진행
$documentService->create($title, $source, $userId);
// audit 기록 생략
```

## 8. 유지보수와 운영 모드

### 8.1 Installer

초기 설치 시에만 접근 가능한 설치기 라우트:

| 라우트 | 페이지 | 책임 |
|---|---|---|
| `/installer/welcome` | 설치 환영 | 요구사항 확인 진입 |
| `/installer/requirements` | 요구사항 검사 | PHP extensions, writable dirs |
| `/installer/db-config` | DB 설정 폼 | DSN/user/password 입력 |
| `/installer/schema-apply` | 스키마 적용 | migration dry-run/confirm |
| `/installer/admin-account` | 관리자 계정 | 최초 admin 생성 |
| `/installer/complete` | 설치 완료 | 다음 조치 안내 |

**규칙:**
- 설치 완료 후 installer 라우트는 접근 불가.
- Installer lock file (`php/config/installed.lock` 또는 유사)로 상태 추적.
- 설치 중단 시 재시작 가능.

**테스트:**
- `php/tests/Installer/InstallerGateTest.php` — 접근 제어 검증

### 8.2 Maintenance mode

유지보수 중 사용자에게 안내 페이지 표시:

```php
// config에서 설정
define('MAINTENANCE_MODE', true);

// 모든 라우트가 maintenance page로 리다이렉트
// (installer 제외)
```

**페이지:**
- `/maintenance` — 예상 복구 시간 안내

**규칙:**
- Maintenance mode 상태는 config 파일 또는 environment variable로 제어.
- 관리자도 유지보수 중에는 일반 라우트 접근 불가 (installer/diagnostics 제외).

### 8.3 운영 진단

관리자만 접근 가능한 진단 페이지:

| 페이지 | 내용 |
|---|---|
| `/admin/diagnostics` | DB 상태, schema version, cache 상태 |
| `/admin/diagnostics/file-permissions` | 쓰기 가능 디렉터리 검사 |
| `/admin/cache-clear` | 캐시 초기화 |

**제한:**
- 민감 정보(DB 연결 문자열 등) 마스킹.
- 시스템 정보 노출 최소화.

**테스트:**
- `php/tests/Http/DiagnosticsPageTest.php` (expected)

## 9. 오류 페이지

### 9.1 HTTP 오류 페이지

| 상태 | 페이지 | 내용 |
|---|---|---|
| 404 Not Found | `/404` | "문서를 찾을 수 없습니다" + 홈/검색 링크 |
| 403 Forbidden | `/permission-denied` | "접근 권한이 없습니다" + 상황별 안내 |
| 500 Internal Error | `/error` | "문제가 발생했습니다" + 지원 연락처 |
| 503 Service Unavailable | `/maintenance` | "유지보수 중입니다" + 복구 시간 |

**규칙:**
- 모든 오류 페이지는 HTML 페이지다 (JSON이 아님).
- Stack trace, DB 연결 정보 등 기술 세부사항 노출 금지.
- 개발 환경(`DEBUG=true`)일 때만 상세 정보 표시.

**테스트:**
- `php/tests/Http/ErrorPageIntegrationTest.php` — 페이지 존재/상태 코드

### 9.2 설치 필수 페이지

DB가 아직 설치되지 않은 상태:

```php
// 모든 라우트가 설치 필요 페이지로 리다이렉트 (installer 제외)
if (!isInstallerCompleted()) {
    redirect('/installer/welcome');
}
```

**페이지:**
- `/installer/welcome` → "설치가 필요합니다"

## 10. shared hosting 호환성

### 10.1 파일 구조 요구사항

Shared hosting 환경에서:

| 경로 | 권한 | 소유자 | 용도 |
|---|---|---|---|
| `public/` | 755 | app | web-accessible root |
| `public/index.php` | 644 | app | front controller |
| `public/.htaccess` | 644 | app | Apache rewrite rules |
| `src/` | 750 | app | application code |
| `config/` | 750 | app | config files (민감한 정보) |
| `storage/` | 755 | app | cache, uploads, logs |
| `storage/cache/` | 755 | app | writable cache dir |

**규칙:**
- `public/` 은 웹 root여야 한다 (docroot 설정).
- `src/`, `config/` 는 web-accessible 경로 밖이어야 한다.
- `storage/` 는 writable이고, public에서 직접 접근 불가.

**설정:**
- `.htaccess` (Apache): `FrontControllerMiddleware` 로 모든 요청을 `index.php` 로 라우팅
- `web.config` (IIS): 동등한 rewrite 규칙
- nginx: 호스팅 문서 참고 (0614)

**테스트:**
- `php/tests/Installer/FilePermissionsTest.php` — 디렉터리 쓰기 검사

### 10.2 Composer 의존성

Shared hosting 지원:

| 환경 | composer 설치 가능? | vendor/ 처리 |
|---|---|---|
| cPanel/Plesk | 가능 (선택) | SSH에서 `composer install` |
| Plain FTP | 불가능 | vendor/ 사전 업로드 후 배포 |

**규칙:**
- `composer.json` 의존성은 최소화.
- vendor 제외 배포 옵션 제공 (0642).
- vendor 포함 배포 옵션도 제공 (0641).

**테스트:**
- `php/tests/Installer/ComposerRequirementsTest.php` (expected)

### 10.3 PHP 버전과 extension

**최소 요구:**
- PHP >= 7.4
- PDO extension
- PDO_MYSQL (MariaDB 지원)
- PDO_PGSQL (PostgreSQL 지원)

**선택 (권장):**
- opcache (성능)
- json (기본값 내장)

**테스트:**
- `php/tests/Installer/RequirementsCheckTest.php` — version/extension 검증

## 11. next phase 진입 조건 (Phase E)

### 11.1 UI layer가 보장하는 것

Phase E 개발자는 다음을 믿고 의존할 수 있다:

✅ 모든 사용자 입력은 escape 처리되어 XSS 방지.  
✅ CSRF token 검증으로 state-changing 폼 보호.  
✅ 모든 라우트는 명시적 권한 검사를 거침.  
✅ HTML 페이지는 접근성 기본(lang, viewport, landmark) 만족.  
✅ 모든 정적 자산은 `php/public/` 에 위치.  
✅ Cache 정책이 정의되어 asset 캐시 적용 가능.  
✅ 오류 페이지가 stack trace 없이 안전한 메시지 제공.  
✅ Installer 라우트가 초기 설치를 guide.  
✅ Audit 훅 placeholder가 실제 audit 로깅 연결 준비 완료.  

### 11.2 Phase E가 추가해야 할 것

🔨 Installer 완료 후 초기 admin 계정 생성.  
🔨 실제 authentication/login 구현.  
🔨 DB migration 및 schema 초기화.  
🔨 Shared hosting 파일 구조 검증 및 권한 설정.  
🔨 Backup/restore 기능.  
🔨 Upgrade 절차 및 rollback 정책.  
🔨 Cron job 또는 web-triggered job runner.  
🔨 Log rotation 및 민감 정보 마스킹.  
🔨 Release notes template 및 version tracking.  

### 11.3 금지된 것

❌ UI template을 직접 수정하면서 escape 정책 우회.  
❌ CSRF token 검증 우회.  
❌ 설치 완료 후 installer 라우트 재진입 가능.  
❌ Static asset을 `php/public/` 외부에 배치.  
❌ 오류 페이지에서 기술 정보(stack trace) 노출.  
❌ 권한 검사 없이 admin/diagnostic 라우트 접근.  
❌ Session cookie에서 `HttpOnly` 속성 제거.  

## 12. 검사 및 검증

### 12.1 자동 검사

커밋 전 다음을 실행:

```bash
scripts/test.sh    # 모든 테스트
scripts/qa.sh      # escape, CSRF, security headers, 성능 budget 검사
```

**PHP 전용:**
```bash
cd php && composer install && php/scripts/qa.sh && cd -
```

### 12.2 수동 QA 체크리스트

접근성, 보안, 모바일, 오류 상태에 대해 `docs/php-ui-phase-qa-checklist.md` 참고.

## 13. 관련 문서

- `docs/php-ui-architecture.md` — UI 아키텍처 상세.
- `docs/php-runtime-security-baseline.md` — 보안 기준 원본.
- `docs/php-ui-phase-qa-checklist.md` — 수동 QA 체크리스트.
- `docs/ui-route-parity-matrix.md` — Python/PHP route parity.
- `docs/php-static-asset-serving.md` — asset 제공 정책.
- `docs/php-ui-cache-header-policy.md` — cache 정책 상세.
- `docs/php-ui-logging-policy.md` — logging 정책 (민감 정보 마스킹).
- `docs/php-ui-i18n-placeholder.md` — i18n 기본 locale (ko).
- `docs/php-ui-installer-link-policy.md` — installer 노출 조건.

## 14. 다음 단계 (Phase E+)

Phase E (Shared Hosting Packaging, 0611+)에서는 위 계약을 기반으로:

1. **Installer 완성**: DB 설정/초기화, admin 계정 생성.
2. **Authentication 구현**: 실제 login/logout, session 관리.
3. **배포 자동화**: 파일 권한, cache clear, migration 실행.
4. **운영 도구**: backup/restore, upgrade, 버전 추적.
5. **Cron/job runner**: shared hosting cron 대안 (web-triggered).
6. **호스팅 가이드**: cPanel/Plesk/plain FTP별 배포 절차.

모든 추가 기능은 이 문서의 경계와 보장을 벗어나지 않아야 한다.
