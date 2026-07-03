# PHP UI Installer Link Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 서버 렌더링 기본값을 구현할 때,
설치 전/후의 UI 링크(Navigation) 표시 정책을 정의한다.

## 목적

MintWiki는 shared hosting 환경에서 배포되므로, 배포 후 데이터베이스와 스키마가
완전히 준비되기 전에도 일부 페이지에 접근할 수 있어야 한다. 이 문서는 다음을
정의한다:

- **설치 전 상태**: 데이터베이스 연결 또는 스키마 버전 확인 중일 때 노출할 링크
- **설치 중 상태**: 스키마 마이그레이션이 필요할 때 노출할 링크 (운영자만)
- **설치 완료 상태**: 모든 스키마가 준비되었을 때 노출할 링크

설치 상태에 따라 노출되는 링크를 구분함으로써, 사용자가 불완전한 상태의 기능에
접근하는 것을 방지하고, 운영자가 필요한 진단/조작 페이지에 쉽게 도달하게 한다.

## 핵심 원칙

### 1. 설치 상태를 먼저 검사한다

모든 요청에서 데이터베이스 연결과 스키마 버전을 먼저 확인한다. 이 상태에 따라
다음 세 가지 경로로 분기한다:

1. **DB 연결 불가** (`connection_failed`): `/installer/diagnose` 페이지로 리다이렉트
2. **스키마 마이그레이션 필요** (`migration_pending`): `/installer/status` 페이지로 리다이렉트 (관리자만)
3. **설치 완료** (`ok`): 일반 UI로 진행

```php
// 생명 주기 (pseudo-code)
function handleRequest(Request $request): Response {
    $state = $installer->checkState();
    
    if ($state === 'connection_failed') {
        return redirect('/installer/diagnose');
    }
    
    if ($state === 'migration_pending' && !$auth->isAdmin()) {
        return Response::html('<h1>설치 중입니다</h1>', 503);
    }
    
    if ($state === 'migration_pending' && $auth->isAdmin()) {
        return redirect('/installer/status');
    }
    
    // 일반 UI 처리
    return handleNormalRequest($request);
}
```

### 2. 설치 페이지는 관리자만 접근한다

`/installer/*` 경로는 모두 관리자 인증이 필수다. 인증되지 않은 사용자는
503 상태 코드와 "설치 중입니다" 메시지를 받는다.

- 설치 전(`connection_failed`, `migration_pending`): 모든 사용자는 같은 503 메시지
- 설치 완료(`ok`): 인증 확인 없이 일반 UI로 진행

### 3. Layout 내 Navigation 링크

페이지 header/footer의 navigation 링크는 설치 상태에 따라 달라진다.

#### 설치 전 (connection_failed 상태)

설치 진단 페이지만 노출:

```html
<nav>
  <a href="/installer/diagnose">설치 진단</a>
</nav>
```

모든 다른 링크(문서, 관리자 대시보드, 사용자 프로필 등)는 숨긴다.

#### 스키마 마이그레이션 필요 (migration_pending 상태)

관리자는 설치 상태 조회 페이지로 이동할 수 있다:

```html
<nav>
  <a href="/installer/status">스키마 상태</a>
  <a href="/admin">대시보드</a>  <!-- 선택적: 관리자는 볼 수 있음 -->
</nav>
```

일반 사용자는 503을 보고 다른 navigation이 없다.

#### 설치 완료 (ok 상태)

모든 일반 navigation이 표시된다:

```html
<nav>
  <a href="/documents">문서</a>
  <a href="/search">검색</a>
  <a href="/admin">관리자</a>
  <a href="/profile">프로필</a>
</nav>
```

### 4. 링크 조건부 렌더링 패턴

layout 템플릿에서 설치 상태 변수를 받아 조건부로 렌더링한다.

```php
// php/src/Http/LayoutRenderer.php (pseudo-code)
public function renderNavigation(InstallationState $state): string {
    $links = [];
    
    if ($state->isBeforeInstall()) {
        // connection_failed 상태
        $links[] = $this->link('/installer/diagnose', '설치 진단');
    } elseif ($state->isMigrationPending()) {
        // migration_pending 상태
        $links[] = $this->link('/installer/status', '스키마 상태');
        if ($this->auth->isAdmin()) {
            $links[] = $this->link('/admin', '대시보드');
        }
    } else {
        // ok 상태
        $links[] = $this->link('/documents', '문서');
        $links[] = $this->link('/search', '검색');
        if ($this->auth->isAdmin()) {
            $links[] = $this->link('/admin', '관리자');
        }
        if ($this->auth->isAuthenticated()) {
            $links[] = $this->link('/profile', '프로필');
        }
    }
    
    return implode($links, ' | ');
}
```

### 5. Installer 페이지 목록

설치 상태별로 노출되는 페이지:

#### GET /installer/diagnose

**상태**: `connection_failed` (DB 연결 불가)

데이터베이스 연결 오류와 원인을 진단한다. 공개 페이지다 (인증 불필요).

**표시 정보**:
- 연결 오류 메시지
- DSN (host, database, charset)
- 권장 조치

**Navigation**:
- `/installer/diagnose` (현재 페이지)

#### GET /installer/status

**상태**: `migration_pending` (스키마 마이그레이션 필요)

관리자만 접근 가능. 필요한 마이그레이션을 확인하고 진행한다.

**표시 정보**:
- 현재 스키마 버전
- 필요한 스키마 버전
- 대기 중인 마이그레이션 목록
- 필요한 SQL (호스팅사에 전달할 용도)

**Navigation**:
- `/installer/status` (현재 페이지)
- `/admin` (관리자 기능) — 선택적

**후속 액션**:
- `POST /installer/migration/<version_id>/apply` — 호스팅사가 SQL을 적용한 후,
  운영자가 "마이그레이션 확인" 버튼을 클릭

#### 일반 페이지들

**상태**: `ok` (설치 완료)

모든 일반 페이지(문서, 검색, 관리자 대시보드 등)에 접근 가능.

**Navigation** (완전):
- `/documents` (문서 목록)
- `/documents/<id>` (문서 보기)
- `/search` (검색)
- `/admin` (관리자 대시보드) — 관리자만
- `/profile` (사용자 프로필) — 로그인 사용자만

## 구현 위치

### InstallationState 클래스

설치 상태를 추상화하는 value object.

```php
namespace MintWiki\Installer;

final class InstallationState
{
    private function __construct(
        readonly string $status,  // 'connection_failed', 'migration_pending', 'ok'
        readonly ?string $error = null,  // 오류 메시지
        readonly ?string $currentVersion = null,  // 현재 스키마 버전
        readonly ?string $requiredVersion = null,  // 필요한 스키마 버전
    ) {}
    
    public static function connectionFailed(string $error): self {
        return new self('connection_failed', error: $error);
    }
    
    public static function migrationPending(
        string $current,
        string $required
    ): self {
        return new self('migration_pending', 
            currentVersion: $current,
            requiredVersion: $required);
    }
    
    public static function installed(): self {
        return new self('ok');
    }
    
    public function isBeforeInstall(): bool {
        return $this->status === 'connection_failed';
    }
    
    public function isMigrationPending(): bool {
        return $this->status === 'migration_pending';
    }
    
    public function isOk(): bool {
        return $this->status === 'ok';
    }
}
```

### Request Handler 미들웨어

모든 요청에서 설치 상태를 먼저 확인하고 리다이렉트한다.

```php
namespace MintWiki\Http\Middleware;

final class InstallationCheckMiddleware
{
    /**
     * 요청을 처리하기 전에 설치 상태를 확인한다.
     * 
     * connection_failed 또는 migration_pending 상태면 해당 페이지로 리다이렉트한다.
     * ok 상태면 다음 핸들러로 진행한다.
     * 
     * @param Request $request 들어온 요청.
     * @param callable $next 다음 핸들러.
     * @param InstallerService $installer 설치 상태 서비스.
     * 
     * @return Response
     */
    public function handle(
        Request $request,
        callable $next,
        InstallerService $installer
    ): Response {
        $state = $installer->checkState();
        
        // installer 페이지는 상태 확인을 건너뜀
        if (str_starts_with($request->path(), '/installer/')) {
            return $next($request);
        }
        
        if ($state->isBeforeInstall()) {
            return Response::redirect('/installer/diagnose');
        }
        
        if ($state->isMigrationPending()) {
            // 관리자만 진행 가능 — 아니면 503
            if (!$auth->isAdmin()) {
                return Response::html('<h1>설치 중입니다</h1>', 503);
            }
            return Response::redirect('/installer/status');
        }
        
        // ok 상태 — 일반 UI로 진행
        return $next($request);
    }
}
```

## 테스트 전략

### 상태별 Navigation 테스트

각 설치 상태에서 노출되는 링크를 확인한다.

```php
// php/tests/Installer/NavigationTest.php
namespace MintWiki\Tests\Installer;

class NavigationTest extends TestCase
{
    /** @test */
    public function showsOnlyDiagnoseLink_whenConnectionFailed(): void
    {
        $state = InstallationState::connectionFailed('Connection refused');
        
        $nav = $this->renderer->renderNavigation($state);
        
        $this->assertStringContainsString('href="/installer/diagnose"', $nav);
        $this->assertStringNotContainsString('href="/documents"', $nav);
        $this->assertStringNotContainsString('href="/admin"', $nav);
    }
    
    /** @test */
    public function showsMigrationStatus_whenMigrationPending(): void
    {
        $state = InstallationState::migrationPending('1', '3');
        
        $nav = $this->renderer->renderNavigation($state);
        
        $this->assertStringContainsString('href="/installer/status"', $nav);
        $this->assertStringNotContainsString('href="/documents"', $nav);
    }
    
    /** @test */
    public function showsNormalLinks_whenInstallationOk(): void
    {
        $state = InstallationState::installed();
        
        $nav = $this->renderer->renderNavigation($state);
        
        $this->assertStringContainsString('href="/documents"', $nav);
        $this->assertStringContainsString('href="/search"', $nav);
        $this->assertStringNotContainsString('href="/installer/diagnose"', $nav);
    }
}
```

### Request Routing 테스트

요청 시 설치 상태에 따른 라우팅이 올바른지 확인한다.

```php
// php/tests/Http/Middleware/InstallationCheckTest.php
namespace MintWiki\Tests\Http\Middleware;

class InstallationCheckTest extends TestCase
{
    /** @test */
    public function redirectsToDiagnose_whenConnectionFailed(): void
    {
        $installer = \Mockery::mock(InstallerService::class);
        $installer->shouldReceive('checkState')
            ->andReturn(InstallationState::connectionFailed('error'));
        
        $response = $this->middleware->handle(
            $this->getRequest('GET', '/documents'),
            fn() => Response::ok()
        );
        
        $this->assertEquals(302, $response->statusCode());
        $this->assertEquals('/installer/diagnose', $response->location());
    }
    
    /** @test */
    public function redirectsToStatus_whenMigrationPending_asAdmin(): void
    {
        $state = InstallationState::migrationPending('1', '3');
        
        $response = $this->asAdmin()->middleware->handle(
            $this->getRequest('GET', '/documents'),
            fn() => Response::ok()
        );
        
        $this->assertEquals(302, $response->statusCode());
        $this->assertEquals('/installer/status', $response->location());
    }
    
    /** @test */
    public function returns503_whenMigrationPending_asNonAdmin(): void
    {
        $state = InstallationState::migrationPending('1', '3');
        
        $response = $this->asGuest()->middleware->handle(
            $this->getRequest('GET', '/documents'),
            fn() => Response::ok()
        );
        
        $this->assertEquals(503, $response->statusCode());
        $this->assertStringContainsString('설치 중입니다', $response->body());
    }
    
    /** @test */
    public function allowsInstallerPages_withoutRedirect(): void
    {
        $state = InstallationState::connectionFailed('error');
        
        $response = $this->middleware->handle(
            $this->getRequest('GET', '/installer/diagnose'),
            fn() => Response::ok()
        );
        
        // 리다이렉트하지 않음 — 200
        $this->assertEquals(200, $response->statusCode());
    }
}
```

## 제약과 트레이드오프

### 설치 중 일반 사용자 차단

설치 중(`migration_pending`)에 일반 사용자는 503 상태로 완전히 차단된다.

**장점**:
- 불완전한 스키마로 인한 데이터 손상 방지
- 오류 페이지 단순화 (상태가 불안정한 이유를 설명할 필요 없음)

**단점**:
- 호스팅사가 SQL을 적용하는 동안(수 시간 가능) 모든 사용자가 접근 불가
- 설치 상태를 운영자만 모니터링 가능

권장 조치: 호스팅사와 협력하여 설치 시간을 최소화하거나, 설치 전에 테스트 환경에서
마이그레이션 시간을 미리 측정한다.

### Installer 페이지의 비인증 접근

`/installer/diagnose`는 비인증 사용자도 접근 가능하다.

**장점**:
- DB 연결 실패 상황에서도 진단 정보 제공 가능
- 호스팅 관리자가 인증 설정 전에 진단 가능

**단점**:
- 연결 오류 메시지에서 DB 정보(host, charset)가 공개될 수 있음
- 보안 감지 도구에서 정보 노출로 플래그 가능

권장 조치: `/installer/diagnose` 페이지는 로그에만 기록하고, 공개 공간에 배치하지 않는다.
또는 설치 후 비인증 접근을 차단하는 옵션을 추가한다 (`ok` 상태에서 `/installer/*`는 404).

### 링크와 상태의 불일치

설치 상태가 변경되어도 이전 HTML이 캐시되어 있을 수 있다.

**방지 방법**:
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md)에 따라 HTML은 `Cache-Control: no-cache`를
  설정하므로, 브라우저/프록시가 항상 재검증한다
- 설치 중(`migration_pending`)인 페이지는 추가로 `Pragma: no-cache` 헤더를 추가할 수 있다

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — 서버 렌더링 기본값
- [PHP UI No-JavaScript Fallback Policy](php-ui-no-js-fallback-policy.md) — 링크와 form 구분
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — HTML 캐시 정책
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — 인증과 CSRF
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 마이그레이션 절차
- [PHP UI Phase QA Checklist](php-ui-phase-qa-checklist.md) — 설치 상태 UI 테스트

## 후속 태스크 연결

- 0574: PHP installer diagnostics page는 이 정책의 `/installer/diagnose` 페이지를 구현한다.
- 0575: PHP installer status page는 이 정책의 `/installer/status` 페이지를 구현한다.
- 0576: PHP layout navigation은 이 정책의 조건부 렌더링 패턴을 구현한다.
- 0577: PHP installation check middleware는 이 정책의 상태 확인 미들웨어를 구현한다.
