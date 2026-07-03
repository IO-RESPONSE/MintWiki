# PHP UI Audit Event Hooks

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
UI form action이 감사 이벤트를 기록하는 hook 패턴과 위치를 정의한다.

## 목적

`docs/modules.md`가 audit 모듈의 책임으로 명시한 "document logs", "permission change logs", "admin action logs"를 PHP UI 계층에서 구체화하기 위해, 어느 form action이 어떤 감사 이벤트를 기록해야 하는지, 그리고 기록 실패 시 어떻게 처리할지를 문서화한다.

## 적용 범위

UI form action이 생성/수정/삭제하는 상태 변경 중 다음 세 카테고리를 다룬다:

- **Document create/edit** (document logs) — 문서 생성/편집 form 제출 시
- **Admin actions** (admin action logs) — 사용자 차단, 문서 보호, 신고 제출/처리 등 관리자 form 제출 시
- **Future categories** (ACL, Discussion 등) — 이후 UI form action이 추가될 때의 확장 지점

## Audit Hook 위치

### Document Create Handler

**파일:** `php/src/Http/DocumentCreateHandler.php`
**Action:** `create`
**구조:**
```
POST /documents
  ↓
DocumentCreateHandler.handle()
  ↓
DocumentService.create()
  ↓
[AUDIT HOOK] AuditEvent 기록
  ↓
응답 반환
```

**기록 타이밍:** `DocumentService.create()` 성공 직후, 응답을 반환하기 전에 audit hook을 호출한다.

**이벤트 정보:**
- `module` = `"document"`
- `action` = `"created"`
- `metadata`:
  - `document_id` (생성된 문서 ID)
  - `title` (생성된 문서 제목)
  - `actor_id` (현재 사용자, 선택 사항)

**실패 정책:** audit 기록이 실패하면 예외를 catch하여 로깅만 하고 사용자 요청은 성공으로 처리한다 (audit 실패가 업무 흐름을 막지 않음).

### Document Edit Handler

**파일:** `php/src/Http/DocumentEditHandler.php`
**Action:** `updated`
**구조:**
```
POST /documents/{id}
  ↓
DocumentEditHandler.handle()
  ↓
DocumentService.update()
  ↓
[AUDIT HOOK] AuditEvent 기록
  ↓
응답 반환
```

**기록 타이밍:** `DocumentService.update()` 성공 직후, 응답을 반환하기 전에 audit hook을 호출한다.

**이벤트 정보:**
- `module` = `"document"`
- `action` = `"updated"`
- `metadata`:
  - `document_id` (수정된 문서 ID)
  - `title_before` (수정 전 제목, 변경된 경우만)
  - `title_after` (수정 후 제목, 변경된 경우만)
  - `source_length` (수정된 source의 크기 또는 변경 여부)
  - `actor_id` (현재 사용자, 선택 사항)

**실패 정책:** audit 기록이 실패하면 예외를 catch하여 로깅만 하고 사용자 요청은 성공으로 처리한다.

### Admin Actions

**파일들:** `php/src/Http/AdminRoutes.php` 및 향후 각 handler
**Actions:** `block_user`, `unblock_user`, `protect_page`, `unprotect_page`, `submit_report`, `resolve_report`

**구조:**
```
POST /admin/{action}
  ↓
AdminHandler.handle()
  ↓
AdminService.{action}()
  ↓
[AUDIT HOOK] AuditEvent 기록
  ↓
응답 반환
```

**기록 타이밍:** `AdminService.{action}()` 성공 직후, 응답을 반환하기 전에 audit hook을 호출한다.

**이벤트 정보 (action별):**

**block_user:**
- `module` = `"admin"`
- `action` = `"block_user"`
- `metadata`:
  - `target_user_id` (차단된 사용자 ID)
  - `reason` (차단 사유, 선택 사항)
  - `actor_id` (관리자 사용자 ID, 선택 사항)

**unblock_user:**
- `module` = `"admin"`
- `action` = `"unblock_user"`
- `metadata`:
  - `target_user_id` (차단 해제된 사용자 ID)
  - `reason` (해제 사유, 선택 사항)
  - `actor_id` (관리자 사용자 ID, 선택 사항)

**protect_page:**
- `module` = `"admin"`
- `action` = `"protect_page"`
- `metadata`:
  - `document_id` (보호된 문서 ID)
  - `protection_level` (보호 수준, 선택 사항)
  - `actor_id` (관리자 사용자 ID, 선택 사항)

**unprotect_page:**
- `module` = `"admin"`
- `action` = `"unprotect_page"`
- `metadata`:
  - `document_id` (보호 해제된 문서 ID)
  - `actor_id` (관리자 사용자 ID, 선택 사항)

**submit_report:**
- `module` = `"admin"`
- `action` = `"submit_report"`
- `metadata`:
  - `target_type` ("document", "comment", "user" 등)
  - `target_id` (신고 대상 ID)
  - `reason` (신고 사유)
  - `actor_id` (신고자 사용자 ID, 선택 사항)

**resolve_report:**
- `module` = `"admin"`
- `action` = `"resolve_report"`
- `metadata`:
  - `report_id` (처리된 신고 ID)
  - `resolution` (처리 결과)
  - `actor_id` (관리자 사용자 ID, 선택 사항)

**실패 정책:** audit 기록이 실패하면 예외를 catch하여 로깅만 하고 사용자 요청은 성공으로 처리한다.

## Audit Hook 구현 패턴

### 현재 단계: No-op Audit Recorder (태스크 0586)

Phase D 초반에는 `MintWiki\Audit\NoOpAuditRecorder`를 사용하여 hook 위치를 확보하되 실제 저장은 하지 않는다.

```php
// DocumentCreateHandler.php
public function handle(string $title, string $idempotencyKey = ''): Response
{
    // ... 기존 로직 ...
    
    $document = $this->documentService->create($title);
    
    // Audit hook (현재는 no-op)
    try {
        $event = new AuditEvent(
            id: self::generateId(),
            module: 'document',
            action: 'created',
            occurredAt: new \DateTimeImmutable('now'),
            actorId: null, // 현재 사용자 ID, 이후 session layer에서 주입
            metadata: ['document_id' => $document->id(), 'title' => $document->title()]
        );
        $this->auditRecorder->record($event);
    } catch (\Exception $e) {
        // audit 기록 실패는 로깅만 하고 request는 계속 진행
        \error_log('Audit recording failed: ' . $e->getMessage());
    }
    
    $html = $this->documentViewPage->render($document);
    return Response::html($html, 201);
}
```

### 미래 단계: Database Audit Repository (0586 이후)

Phase D 후반에는 `MintWiki\Audit\DatabaseAuditRepository`가 `AuditRecorder` 인터페이스를 구현하여 events를 DB에 저장한다. Handler 코드는 변경하지 않는다 — 저장소 구현이 바뀔 뿐이다.

```php
// 의존성 주입 시점에만 변경됨
$auditRecorder = new DatabaseAuditRepository($database);
$documentCreateHandler = new DocumentCreateHandler(
    $documentService,
    null,
    null,
    $auditRecorder  // ← 구현체만 교체됨
);
```

## 에러 처리 원칙

**audit hook 실패는 user-facing 요청 실패가 아니다.**

1. **기록 실패 시:** `\Exception`을 catch하여 application log에만 기록한다.
2. **사용자 응답:** document create/update/admin action은 정상 성공 응답을 반환한다.
3. **근거:** audit 로그는 사후 감시/분석용이며, 사용자의 즉각적인 업무 흐름을 막을 이유가 없다. audit 장애 시에도 문서는 저장되어야 한다.

다만 운영 단계에서 audit 기록 실패가 지속되면 모니터링 alert이 작동하여 관리자가 인지할 수 있도록 한다 (이후 운영 태스크).

## Idempotency와 Audit

Idempotency key를 사용하는 form action에서는 다음 순서를 지킨다:

1. Idempotency key 검증
2. 비즈니스 로직 실행 (DocumentService.create 등)
3. **Audit hook 호출 (최초 제출 시에만 호출)**
4. 응답 반환

재제출 감지 시 (2)-(3)을 건너뛰고 캐시된 이전 응답을 반환하므로, audit event는 최초 제출 1회만 기록된다.

```php
if (!$this->idempotencyKeyService->validate($idempotencyKey)) {
    // 캐시된 이전 응답 반환 — audit hook 호출 안 함
    return $this->idempotencyKeyService->getCachedResponse($idempotencyKey);
}

$document = $this->documentService->create($title);

// audit hook은 validate 통과 후에만 호출
// 따라서 중복 제출은 audit event를 발생시키지 않음
$this->auditRecorder->record($event);
```

## 현재 구현 상태

| 컴포넌트 | 파일 | 상태 | 비고 |
|---|---|---|---|
| NoOpAuditRecorder | `php/src/Modules/Audit/NoOpAuditRecorder.php` | 태스크 0586 | placeholder 구현, 아무 작업 안 함 |
| AuditEvent | `php/src/Modules/Audit/AuditEvent.php` | 완료 (0413) | immutable value object |
| DocumentCreateHandler audit hook | `php/src/Http/DocumentCreateHandler.php` | 태스크 0586 | handler에 hook 추가 |
| DocumentEditHandler audit hook | `php/src/Http/DocumentEditHandler.php` | 태스크 0586 | handler에 hook 추가 |
| AdminRoutes/AdminHandler audit hooks | `php/src/Http/AdminRoutes.php` 등 | 태스크 0586+ | admin 실제 구현 이후 |
| DatabaseAuditRepository | 미정 | 태스크 0586+ | 실제 저장소 구현 |
| Audit module service layer | 미정 | 태스크 0586+ | record/list_events 계약 |

## 테스트 전략 (태스크 0586)

audit hook을 추가하는 handler/service 테스트에서:

1. **정상 경로:** form 제출 성공 시 audit hook이 호출되는지 확인
2. **audit 실패 resilience:** audit 기록이 실패해도 handler는 성공 응답을 반환하는지 확인
3. **Idempotency + audit:** 재제출 시 audit event가 중복으로 기록되지 않는지 확인
4. **metadata completeness:** 기록된 event의 metadata가 필수 필드를 모두 포함하는지 확인

```php
// DocumentCreateHandlerTest.php
public function test_audit_event_recorded_on_document_create(): void
{
    // NoOpAuditRecorder를 MockAuditRecorder로 교체
    $mockRecorder = new MockAuditRecorder();
    $handler = new DocumentCreateHandler($service, null, null, $mockRecorder);
    
    $response = $handler->handle('새 문서', '...');
    
    $this->assertEqual(201, $response->statusCode());
    $this->assertEqual(1, $mockRecorder->recordCallCount());
    $event = $mockRecorder->lastRecordedEvent();
    $this->assertEqual('document', $event->module());
    $this->assertEqual('created', $event->action());
}

public function test_document_create_succeeds_when_audit_fails(): void
{
    $failingRecorder = new FailingAuditRecorder();
    $handler = new DocumentCreateHandler($service, null, null, $failingRecorder);
    
    // audit 기록이 실패해도 handler는 성공
    $response = $handler->handle('새 문서', '...');
    
    $this->assertEqual(201, $response->statusCode());
}
```

## 관련 문서

- [Audit Portable Repository Plan](audit-portable-repository-plan.md) — audit event 모델과 저장소 설계 (0457)
- [PHP UI Architecture](php-ui-architecture.md) — UI handler/service 아키텍처
- [modules.md#audit](modules.md#audit) — audit 모듈의 책임과 목표 아키텍처
- [service-method-contracts.md](service-method-contracts.md) — document/admin 서비스 계약

## 이 문서 이후 단계

- **0586** ([Add PHP UI audit hook placeholders](php-db-ui-micro-job-prompts-0351-0670.md)): 이 문서에서 정의한 hook 위치와 구조를 DocumentCreateHandler/DocumentEditHandler에 구현한다. NoOpAuditRecorder를 사용하여 아직 실제 저장은 하지 않는다.
- **0586+ 이후:** admin 서비스 실제 구현 시 admin handler에도 동일 패턴으로 audit hook을 추가한다.
- **0586+ 이후:** DatabaseAuditRepository 구현 시 NoOpAuditRecorder를 교체한다.
