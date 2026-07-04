# Production Error Handling Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅 production 배포에서 오류를 사용자에게 표시하고 로그에 남기는
기준을 고정한다. 이 문서는 0650 production error handler skeleton의 입력
정책이며, debug off 상태를 전제로 한다.

## 목적

- production 화면과 API 응답에는 내부 예외 메시지, SQL, 파일 경로, stack
  trace를 노출하지 않는다.
- 사용자가 복구할 수 있는 안내와 운영자가 진단할 수 있는 로그를 분리한다.
- PHP UI, installer, HTTP adapter가 같은 error code와 request id 기준으로
  오류를 연결하도록 한다.

## 적용 범위

- 공용 웹호스팅에 배포된 PHP front controller와 HTTP adapter.
- HTML 오류 page, JSON 오류 응답, installer 오류 화면.
- 애플리케이션 로그에 남기는 production 오류 이벤트.

적용되지 않는 것:

- development debug page와 stack trace 표시.
- 배포 스크립트, 웹서버 설정, 모니터링 서비스 구현.
- 개별 도메인 예외의 error code 추가.

## 1. 기본 원칙

production error handler는 다음 원칙을 따른다.

- `debug=false`일 때 원본 예외 메시지를 사용자 응답에 그대로 넣지 않는다.
- 사용자 메시지는 짧고 일반적인 복구 행동을 알려준다.
- 로그 메시지는 원인 진단에 필요한 기술 세부 정보를 담되 민감 정보를
  마스킹한다.
- 사용자 응답과 로그는 같은 request id와 안정적인 error code로 연결한다.
- 오류 처리 중 추가 오류가 발생해도 사용자에게는 같은 안전한 fallback
  메시지를 반환한다.

## 2. 사용자 메시지와 로그 메시지 분리

사용자 메시지는 화면과 API 응답에 들어가는 문구다. 로그 메시지는
`error_log()` 또는 이후 로거 어댑터에 남기는 운영 진단 문구다. 두 메시지는
같은 문자열을 공유하지 않는다.

| 상황 | 사용자 메시지 | 로그 메시지 |
|---|---|---|
| 404 not found | `요청한 페이지를 찾을 수 없습니다.` | `not_found path=/missing request_id=...` |
| 권한 없음 | `이 작업을 수행할 권한이 없습니다.` | `permission_denied user=... action=... request_id=...` |
| 검증 실패 | `입력값을 확인해 주세요.` | `validation_failed code=document.empty_title field=title request_id=...` |
| DB 연결 실패 | `일시적인 서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.` | `database_connection_failed driver=pdo_mysql message=... request_id=...` |
| 예상하지 못한 예외 | `서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.` | `unhandled_exception class=... message=... file=... request_id=...` |

사용자 메시지에는 다음 값을 포함하지 않는다.

- 원본 예외 메시지와 stack trace.
- DB driver 오류 문자열, SQL, DSN, 사용자명, 비밀번호.
- 서버 파일 경로, PHP class autoload 경로, document root 경로.
- 세션 ID, CSRF token, 쿠키 원문, 이메일 주소 같은 민감 정보.

로그 메시지는 `docs/php-ui-logging-policy.md`의 마스킹 규칙을 따른다.

## 3. 응답 형식

### 3.1 HTML 응답

HTML 요청은 공통 오류 page를 반환한다.

- 404는 404 상태 코드와 "페이지를 찾을 수 없습니다" 계열 메시지를 사용한다.
- 403은 403 상태 코드와 권한 안내 메시지를 사용한다.
- 422 또는 400은 입력값 확인 메시지와 필드별 안전한 validation 메시지를
  사용한다.
- 500은 500 상태 코드와 일반 서버 오류 메시지만 사용한다.

500 page에는 request id를 표시할 수 있지만, 원본 예외 메시지는 표시하지
않는다.

### 3.2 JSON 응답

JSON 요청은 다음 필드를 기본으로 한다.

```json
{
  "error": {
    "code": "app.internal_error",
    "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    "request_id": "req_..."
  }
}
```

- `code`는 안정적인 error code 또는 HTTP 범주 code를 사용한다.
- `message`는 사용자 메시지다.
- `request_id`는 로그 검색용 상관 id다.
- `debug`, `trace`, `exception`, `sql` 필드는 production 응답에 포함하지
  않는다.

## 4. Error Code 기준

이미 안정적인 도메인 error code가 있는 예외는 해당 code를 유지한다. 예를
들어 `document.empty_title`, `document.duplicate_title`,
`document.not_found`는 응답과 로그 양쪽에 같은 code로 남긴다.

아직 도메인 code가 없는 infrastructure 오류는 handler 내부에서 HTTP 범주
code로 매핑한다.

| 범주 | 기본 code | 상태 코드 |
|---|---|---|
| 찾을 수 없음 | `http.not_found` | 404 |
| 권한 없음 | `http.forbidden` | 403 |
| 잘못된 요청 | `http.bad_request` | 400 |
| 검증 실패 | `http.validation_failed` | 422 |
| 내부 오류 | `app.internal_error` | 500 |

이 매핑은 사용자 메시지 선택과 로그 상관관계를 위한 것이며, 새 도메인 예외
상수를 이 문서에서 추가하지 않는다.

## 5. Production Logging

production error handler는 오류마다 다음 정보를 로그에 남긴다.

- UTC timestamp.
- log level: 사용자 입력 또는 권한 오류는 `WARN`, 시스템 오류는 `ERROR`.
- request id.
- HTTP method, path, status code.
- 안정적인 error code.
- 예외 class와 마스킹된 원본 메시지.
- 사용자 식별자는 가능한 경우 마스킹된 id 또는 역할 수준으로 제한한다.

로그 예시:

```text
2026-07-04T00:00:00Z [ERROR] ErrorHandler code=app.internal_error status=500 request_id=req_123 class=PDOException message="SQLSTATE[HY000] ..."
```

로그에도 비밀번호, token, 원문 쿠키, 요청 body, 응답 body는 남기지 않는다.

## 6. Installer와 운영 진단

installer 오류 화면은 사용자가 조치할 수 있는 설정 항목을 알려주되 내부 값을
노출하지 않는다.

- DB 연결 실패: host/port가 설정되었는지와 자격증명 확인이 필요하다는
  안내를 표시한다. 비밀번호와 DSN 전체는 표시하지 않는다.
- writable directory 실패: 실패한 공개 이름(`storage/logs/` 등)과 필요한
  권한을 표시한다. 서버 절대 경로는 로그에만 남긴다.
- PHP extension 누락: extension 이름과 설치 필요 여부를 표시한다.

운영 진단 page가 추가되더라도 production 사용자 응답보다 더 많은 내부 값을
공개하지 않는다. 관리자에게 필요한 세부 원인은 로그 파일 확인 절차로
연결한다.

## 이 문서가 하지 않는 것

- production error handler PHP 코드를 작성하지 않는다.
- debug mode UI 또는 stack trace renderer를 정의하지 않는다.
- 웹서버의 custom error page 설정을 변경하지 않는다.

## 관련 문서

- [PHP UI Logging Policy](php-ui-logging-policy.md) — 로그 형식과 민감 정보
  마스킹 기준.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) —
  production 런타임 보안 기준.
- [Portable Exception Code Policy](portable-exception-code-policy.md) —
  안정적인 error code 형식.
- [Config File Permission Policy](config-file-permission-policy.md) — 설정 파일
  노출 방지 기준.
