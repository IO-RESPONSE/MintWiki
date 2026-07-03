# PHP UI Logging Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
UI 요청과 응답, 오류를 애플리케이션 로그에 남기는 정책을 정의한다.
민감 정보(비밀번호, 토큰, 개인 데이터)는 마스킹하여 안전성을 보장한다.

## 목적

MintWiki PHP UI는 각 요청-응답을 시간 순서대로 애플리케이션 로그에 남겨야 한다.
이 로그는 운영 단계에서 다음을 지원한다.

- **문제 진단**: 사용자 보고 오류를 추적하고 재현
- **성능 모니터링**: 느린 요청이나 만료된 작업 감지
- **보안 감시**: 비정상 접근 패턴 발견
- **감사(audit)와의 구분**: audit은 비즈니스 규칙 위반을 기록하지만, logging은 기술 이벤트(요청/응답/오류)를 기록

## 로깅 대상

### 1. UI 요청 로깅

다음 정보를 각 요청의 시작 시점에 기록한다:

- **메서드와 경로**: `POST /documents`, `GET /documents/123` 등
- **클라이언트 IP**: 요청 출처 추적 (공유 호스팅에서는 X-Forwarded-For 고려)
- **요청 크기**: Content-Length 헤더 (대용량 업로드 감지용)
- **타임스탬프**: ISO 8601 형식 (`2025-07-03T12:34:56Z`)

```php
// DocumentCreateHandler.php 예시 (실제 구현은 middleware/front-controller에서 수행)
error_log(sprintf(
    '[REQUEST] %s %s from %s size=%d',
    'POST',
    '/documents',
    $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    (int)($_SERVER['CONTENT_LENGTH'] ?? 0)
));
```

### 2. UI 응답 로깅

요청 처리 완료 후 응답을 기록한다:

- **상태 코드**: 200, 404, 500 등
- **응답 크기**: 출력 바이트 수
- **처리 시간**: request 시작부터 response 반환까지 경과 시간(ms 단위)
- **캐시 상태**: hit/miss/no-cache 등 (정적 asset에만 해당)

```php
// 응답 기록 예시
error_log(sprintf(
    '[RESPONSE] %d %d bytes in %dms',
    $response->status(),
    strlen($response->body()),
    $elapsedMs
));
```

### 3. 오류 로깅

예외 또는 비정상 상황을 기록한다:

- **핸들러 수준**: form validation 오류, not found, conflict 등
  - 로그 레벨: WARNING (사용자 오류)
  - 예: "Document not found: 123abc"

- **시스템 수준**: database 연결 실패, 권한 오류 등
  - 로그 레벨: ERROR (기술 오류)
  - 예: "Database connection failed: Lost connection to MySQL server"

- **감사 기록 실패**: audit event 저장 실패 (이미 구현됨)
  - 로그 레벨: WARNING (업무 흐름은 계속됨)
  - 예: "Audit recording failed: Connection timeout"

```php
// 사용자 오류 (validation 실패)
error_log('[WARN] Document create failed: empty title');

// 시스템 오류
error_log('[ERROR] Database error: ' . $e->getMessage());

// 감사 기록 실패 (이미 구현된 패턴)
error_log('Audit recording failed: ' . $e->getMessage());
```

### 4. 로깅 제외 대상

다음 정보는 로깅하지 않는다:

- **요청 본문(body)**: POST 데이터, 쿼리 파라미터 등 (민감 정보 포함 가능)
- **응답 본문(body)**: HTML 문서 내용 (로그 크기 폭증)
- **개인 식별 정보(PII)**: 사용자 이름, 이메일, 주소 (마스킹 필수)
- **인증 토큰**: CSRF token, session token, API key

## 민감 정보 마스킹 규칙

로깅이 필요한 정보 중 민감한 데이터는 마스킹한다.

### 1. 비밀번호 및 인증 정보

**규칙**: 전체 제거 또는 길이만 표시

```php
// 마스킹 전
$password = "secret123";
error_log("User login attempt with password: $password");  // ❌ 절대 금지

// 마스킹 후 (옵션 1: 전체 제거)
error_log("User login attempt");

// 마스킹 후 (옵션 2: 길이만 표시)
error_log("User login attempt with password (${passwordLength} chars)");
```

### 2. 토큰 및 세션

**규칙**: 첫 6자만 표시, 나머지는 `*`로 치환

```php
$csrfToken = "abc123def456xyz789...";
$masked = substr($csrfToken, 0, 6) . str_repeat('*', strlen($csrfToken) - 6);
error_log("CSRF token validation: $masked");  // abc123**...
```

### 3. 개인 식별 정보(이메일, 전화, 주소)

**규칙**: 도메인/국가 부분만 표시, 개인 부분은 마스킹

```php
// 이메일
$email = "user@example.com";
$masked = preg_replace('/^[^@]*/', '***', $email);
error_log("Invitation sent to: $masked");  // ***@example.com

// 전화번호 (없으면 생략, 필요시 국가 코드만 표시)
$phone = "+82-10-1234-5678";
$masked = preg_replace('/[0-9]/', '*', $phone);
error_log("SMS sent to: $masked");  // +82-***-****-****
```

### 4. 문서 제목 및 컨텐츠

**규칙**: 길이와 카테고리만 표시

```php
// 제목
$title = "Confidential Project Plan";
$titleLength = strlen($title);
error_log("Document created with title (${titleLength} chars)");

// 컨텐츠(source)
$source = "...";
$contentLength = strlen($source);
error_log("Document updated with content (${contentLength} bytes)");
```

### 5. 사용자 ID와 특수 ID

**규칙**: UUID/hash는 첫 8자만 표시, 정수 ID는 숫자 범위만 표시

```php
// UUID
$documentId = "550e8400-e29b-41d4-a716-446655440000";
$masked = substr($documentId, 0, 8) . "...";
error_log("Document accessed: $masked");  // 550e8400...

// 정수 ID (범위만 표시)
$userId = 12345;
$masked = floor($userId / 1000) . "000-" . floor($userId / 1000) . "999";
error_log("User blocked: ID in range $masked");  // 12000-12999
```

## 로그 형식

### 구조화된 로깅

PHP `error_log()`는 단순 문자열만 지원하므로, 로그 구문 분석을 위해 다음 형식을 지킨다:

```
[TIMESTAMP] [LEVEL] [COMPONENT] message
```

예:

```
2025-07-03T12:34:56Z [INFO] HTTP POST /documents 201 1234 bytes 45ms
2025-07-03T12:34:57Z [WARN] DocumentCreateHandler Document not found: abc123...
2025-07-03T12:35:00Z [ERROR] Database MySQL connection lost
2025-07-03T12:35:01Z [WARN] AuditRecorder Audit recording failed: timeout
```

### 타임스탬프

- 형식: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- 타임존: UTC (Z로 표시)
- PHP 코드:
  ```php
  date('c')  // 예: 2025-07-03T12:34:56+00:00
  // 또는 명시적으로:
  (new DateTimeImmutable('now', new DateTimeZone('UTC')))->format('Y-m-d\TH:i:s\Z')
  ```

### 로그 레벨

4가지 기본 레벨을 사용한다:

| 레벨 | 설명 | 예시 |
|---|---|---|
| INFO | 정상 요청/응답 | `[INFO] HTTP POST /documents 201` |
| WARN | 사용자 오류, audit 실패 | `[WARN] Document not found`, `[WARN] Audit recording failed` |
| ERROR | 시스템 오류 | `[ERROR] Database connection failed` |
| DEBUG | 개발/디버깅용 (프로덕션 미사용) | `[DEBUG] Document service called with title=...` |

## 구현 위치

### 1. 프론트 컨트롤러 (Request/Response 로깅)

**파일**: `php/src/App/FrontController.php` (미래 구현)
**담당**: 모든 요청-응답 쌍의 로깅

```php
public function handle(Request $request): Response
{
    $startTime = microtime(true);
    
    // 요청 로깅
    error_log(sprintf(
        '[REQUEST] %s %s from %s',
        $request->method(),
        $request->path(),
        $_SERVER['REMOTE_ADDR'] ?? 'unknown'
    ));
    
    try {
        $response = $this->dispatch($request);
    } catch (Exception $e) {
        error_log('[ERROR] Unhandled exception: ' . $e->getMessage());
        $response = new Response(500, [], 'Internal Server Error');
    }
    
    // 응답 로깅
    $elapsedMs = (int)((microtime(true) - $startTime) * 1000);
    error_log(sprintf(
        '[RESPONSE] %d %d bytes in %dms',
        $response->status(),
        strlen($response->body()),
        $elapsedMs
    ));
    
    return $response;
}
```

### 2. 핸들러 (업무 로직 오류 로깅)

**파일**: `php/src/Http/DocumentCreateHandler.php`, `php/src/Http/DocumentEditHandler.php` 등
**담당**: validation 실패, 비즈니스 오류

```php
public function handle(string $title): Response
{
    try {
        $document = $this->documentService->create($title);
        // ... audit hook ...
        return Response::html($html, 201);
    } catch (EmptyTitleError) {
        error_log('[WARN] DocumentCreateHandler Document create failed: empty title');
        return Response::html($errorHtml, 400);
    } catch (DuplicateNormalizedTitleError) {
        error_log('[WARN] DocumentCreateHandler Document create failed: duplicate title');
        return Response::html($errorHtml, 409);
    }
}
```

### 3. 감사 레코더 (Audit 기록 실패)

**파일**: `php/src/Modules/Audit/DatabaseAuditRepository.php` (미래 구현)
**담당**: audit 이벤트 저장 실패

현재는 handler에서 try-catch로 처리하고 있음:

```php
try {
    $this->auditRecorder->record($event);
} catch (Exception $e) {
    error_log('[WARN] Audit recording failed: ' . $e->getMessage());
}
```

## 로깅과 감사(Audit)의 구분

로깅(logging)과 감사(audit)는 서로 다른 목적을 가진다:

| 속성 | Logging (기술 로그) | Audit (비즈니스 로그) |
|---|---|---|
| **목적** | 운영 진단, 성능 모니터링, 보안 감시 | 비즈니스 규칙 준수, 규정 감시 |
| **기록 시점** | 모든 요청/응답 | 상태 변경(생성/수정/삭제) |
| **저장소** | 애플리케이션 로그 파일 또는 syslog | 데이터베이스 (audit_events 테이블) |
| **보존 기간** | 며칠~주 (운영팀 설정) | 장기 (규정상 요구) |
| **접근 권한** | 운영팀, 보안팀 | 규정준수팀, 감사팀, 관리자 |
| **예시** | "POST /documents 201 45ms", "Document not found" | "Document abc123 created by user 456, title 'Plan'" |

**구현상 영향**:
- Logging만 실패해도 request는 성공 처리 (운영 비용 최소화)
- Audit 기록 실패도 request는 성공하지만, 오류는 로그됨

## 로그 저장소

### PHP 표준 환경

`php.ini`의 `error_log` 설정에 따라 저장된다:

```ini
# 파일로 저장
error_log = /var/log/php-errors.log

# 시스템 syslog로 저장
error_log = syslog

# 표준 에러(stderr)로 저장 (컨테이너 환경)
error_log = /dev/stderr
```

### Shared Hosting 환경

공유 호스팅에서는:
- 호스팅사가 제공하는 error log 디렉터리 사용 (예: `/home/username/logs/`)
- 일반적으로 cPanel/Plesk UI에서 확인 가능
- 로그 로테이션은 호스팅사 관리

### Docker 환경

```dockerfile
# Dockerfile에서
ENV PHP_LOG_ERRORS=1
ENV PHP_ERROR_LOG=/dev/stderr

# 또는 시작 스크립트에서
echo "error_log = /dev/stderr" >> /usr/local/etc/php/conf.d/logging.ini
```

## 테스트 전략

### 1. 로깅 출력 확인 (수동)

```bash
# 애플리케이션 실행 후 로그 스트림 확인
tail -f /var/log/php-errors.log

# 테스트 요청 실행
curl -X POST http://localhost/documents -d "title=Test"

# 로그에 다음 패턴이 있는지 확인
# [REQUEST] POST /documents from ...
# [RESPONSE] 201 ... bytes in ...ms
```

### 2. 민감 정보 마스킹 테스트

```php
// tests/Logging/SensitiveDataMaskingTest.php
final class SensitiveDataMaskingTest
{
    public function test_password_is_not_logged(): void
    {
        // 비밀번호를 포함한 요청을 로깅할 때
        $logger = new TestLogger();
        $password = "secret123";
        
        // 로그에 비밀번호 문자열이 없어야 함
        $this->assertStringNotContainsString($password, $logger->getOutput());
    }

    public function test_email_is_masked(): void
    {
        $logger = new TestLogger();
        $email = "user@example.com";
        
        // 도메인은 있지만 사용자명은 마스킹되어야 함
        $this->assertStringContainsString('@example.com', $logger->getOutput());
        $this->assertStringNotContainsString('user', $logger->getOutput());
    }

    public function test_token_is_partially_masked(): void
    {
        $logger = new TestLogger();
        $token = "abc123def456xyz789";
        
        // 처음 6자는 있고 나머지는 마스킹
        $this->assertStringContainsString('abc123', $logger->getOutput());
        $this->assertStringNotContainsString('def456', $logger->getOutput());
    }

    public function test_document_id_is_partially_masked(): void
    {
        $logger = new TestLogger();
        $docId = "550e8400-e29b-41d4-a716-446655440000";
        
        // 처음 8자만 표시
        $this->assertStringContainsString('550e8400', $logger->getOutput());
        $this->assertStringNotContainsString('-e29b-', $logger->getOutput());
    }
}
```

### 3. 로그 포맷 테스트

```php
// tests/Logging/LogFormatTest.php
final class LogFormatTest
{
    public function test_request_log_format(): void
    {
        $logger = new TestLogger();
        
        // REQUEST 로그는 [REQUEST] 레벨, 메서드, 경로, IP를 포함해야 함
        $this->assertStringContainsString('[REQUEST]', $logger->getOutput());
        $this->assertStringContainsString('POST', $logger->getOutput());
        $this->assertStringContainsString('/documents', $logger->getOutput());
    }

    public function test_response_log_contains_status_and_time(): void
    {
        $logger = new TestLogger();
        
        // RESPONSE 로그는 상태 코드와 경과 시간을 포함해야 함
        $this->assertStringContainsString('[RESPONSE]', $logger->getOutput());
        $this->assertStringContainsString('201', $logger->getOutput());
        $this->assertStringContainsString('ms', $logger->getOutput());
    }

    public function test_timestamp_is_iso8601(): void
    {
        $logger = new TestLogger();
        $output = $logger->getOutput();
        
        // ISO 8601 타임스탐프 패턴 확인
        $this->assertMatchesRegularExpression(
            '/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/',
            $output
        );
    }
}
```

### 4. 오류 로깅 테스트

```php
// tests/Http/DocumentCreateHandlerLoggingTest.php
final class DocumentCreateHandlerLoggingTest
{
    public function test_validation_error_is_logged(): void
    {
        $logger = new TestLogger();
        $handler = new DocumentCreateHandler($service, logger: $logger);
        
        // 빈 제목으로 요청
        $response = $handler->handle('');
        
        // 로그에 경고 메시지가 있어야 함
        $this->assertStringContainsString('[WARN]', $logger->getOutput());
        $this->assertStringContainsString('empty title', $logger->getOutput());
    }

    public function test_system_error_is_logged(): void
    {
        $logger = new TestLogger();
        $service = new FailingDocumentService();  // DB 오류 시뮬레이션
        $handler = new DocumentCreateHandler($service, logger: $logger);
        
        $response = $handler->handle('Valid Title');
        
        // 로그에 ERROR 레벨이 있어야 함
        $this->assertStringContainsString('[ERROR]', $logger->getOutput());
        $this->assertEqual(500, $response->status());
    }
}
```

## 주의사항

### 1. 로그 인젝션(Log Injection) 방지

사용자 입력을 로그에 쓸 때는 newline 문자를 제거해야 한다 (로그 위조 방지):

```php
// ❌ 위험: 사용자가 "\n[WARN] Admin access granted" 삽입 가능
error_log("Document created: $userInput");

// ✅ 안전: newline 제거
$sanitizedInput = str_replace(["\r", "\n"], ' ', $userInput);
error_log("Document created: $sanitizedInput");
```

### 2. 로그 크기 관리

대용량 응답이나 오류 메시지는 길이를 제한한다:

```php
$message = $exception->getMessage();
$maxLength = 500;
if (strlen($message) > $maxLength) {
    $message = substr($message, 0, $maxLength) . '...';
}
error_log('[ERROR] ' . $message);
```

### 3. 순환 로깅(Log Loops) 방지

로깅 시스템 자체의 오류가 무한 루프를 만들지 않도록 주의:

```php
// ❌ 위험: 로깅 실패 시 또 로깅
try {
    error_log($message);
} catch (Exception $e) {
    error_log('Failed to log: ' . $e->getMessage());  // 루프 위험
}

// ✅ 안전: 로깅 실패는 무시 (운영 흐름 계속)
try {
    error_log($message);
} catch (Exception $e) {
    // 로깅 실패는 무시하고 애플리케이션 계속 실행
}
```

## 관련 문서

- [PHP UI Audit Event Hooks](php-ui-audit-event-hooks.md) — 비즈니스 이벤트 감사 로그
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — 보안 헤더, 입력 검증
- [PHP Coding Standard](php-coding-standard.md) — 코딩 규칙
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 호스팅 환경 구성

## 이 문서 이후 단계

- **0591** (이 태스크): UI 로깅 정책 문서화. 실제 구현은 아직 미루어짐.
- **0591 이후** (미래 태스크): FrontController, handler 등에 실제 로깅 코드 추가
- **0591 이후** (미래 태스크): 로깅 마스킹 유틸리티 클래스 구현
- **0591 이후** (미래 태스크): 로깅 테스트 작성
