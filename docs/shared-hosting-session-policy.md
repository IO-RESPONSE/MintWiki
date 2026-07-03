# Shared Hosting Session Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅(shared hosting) 배포에서 PHP 세션 저장 방식을 선택하는
기준을 고정한다. 이 문서는 0633(PHP session adapter skeleton)이 구현할
어댑터의 입력 정책이며, 세션 쿠키 속성은 0634(cookie 보안 정책)가 별도로
정한다.

## 목적

- PHP 기본 세션, 파일 기반 세션, DB 기반 세션 중 어떤 방식을 선택할지
  판단하는 기준을 둔다.
- installer requirement check가 배포 환경에서 확인해야 할 세션 관련
  조건을 고정한다.
- 세션 저장소 선택이 도메인 계층에 새 의존성을 만들지 않도록 경계를
  명확히 한다.

## 적용 범위

- 공용 웹호스팅(cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 런타임.
- 로그인 상태, CSRF 상태, 짧은 수명의 사용자 세션 데이터를 저장하는
  PHP 세션 어댑터.
- installer가 설치 전 확인해야 하는 세션 저장소 요구사항.

적용되지 않는 것:

- 쿠키 `Secure`/`HttpOnly`/`SameSite` 세부 값.
- 세션 어댑터 PHP 코드 구현.
- 관리자 강제 로그아웃 UI, 세션 목록 UI, 운영자 감사 화면.

## 1. 선택 원칙

세션 저장소는 다음 우선순위로 선택한다.

| 선택지 | 채택 조건 | 금지 또는 보류 조건 | 비고 |
|---|---|---|---|
| PHP 기본 세션 | 호스팅의 `session.save_handler`와 `session.save_path`가 document root 밖의 계정 격리 경로를 가리키고, installer가 읽기/쓰기/삭제 테스트를 통과한다. | 저장 경로를 확인할 수 없거나, 다른 호스팅 계정과 공유될 가능성이 있거나, document root 안에 있다. | 가장 단순한 기본값이다. PHP 런타임 설정을 신뢰할 수 있을 때만 쓴다. |
| 파일 기반 세션 | PHP 기본 세션 경로를 신뢰할 수 없지만, `storage/sessions/`를 document root 밖에 만들 수 있고 파일 잠금과 정리 작업을 수행할 수 있다. | `storage/sessions/`를 만들 수 없거나, 파일 잠금이 실패하거나, 호스팅사가 장기 파일 보관을 주기적으로 삭제한다. | shared hosting의 기본 대안이다. 패키지가 직접 소유한 비공개 경로를 사용한다. |
| DB 기반 세션 | 여러 웹 노드, 불안정한 로컬 파일시스템, 호스팅사의 임의 파일 정리 정책, 또는 관리자 세션 무효화 요구가 있다. | PDO MariaDB 연결을 확보하지 못했거나, 세션 갱신마다 DB 쓰기 부하를 감당할 수 없다. | 운영 통제가 가장 좋지만 DB 의존성과 쓰기 부하가 늘어난다. |

기본 권장값은 **PHP 기본 세션을 먼저 검사하고, 실패하면 파일 기반 세션으로
전환**하는 것이다. DB 기반 세션은 위 표의 조건이 실제로 필요한 배포에서만
명시적으로 선택한다.

## 2. 저장소별 세부 기준

### 2.1 PHP 기본 세션

PHP 기본 세션은 `session_start()`와 PHP 내장 세션 ID 생성기를 그대로
사용한다. 단, installer는 다음 조건을 모두 확인해야 한다.

- `session.save_handler`가 PHP 표준 파일 세션이거나 호스팅사가 제공하는
  안전한 핸들러다.
- `session.save_path`가 공개 document root 밖에 있다.
- 해당 경로에 세션 테스트 파일을 생성, 읽기, 삭제할 수 있다.
- 세션 경로가 다른 계정과 공유되는 전역 임시 디렉터리(`/tmp` 등)라면
  계정별 격리 하위 경로가 확인되어야 한다.

위 조건 중 하나라도 확인할 수 없으면 PHP 기본 세션을 채택하지 않는다.

### 2.2 파일 기반 세션

파일 기반 세션은 프로젝트가 소유한 비공개 경로인 `storage/sessions/`를
사용한다. 이 디렉터리는 `docs/writable-directories-policy.md`의 원칙을
따라 document root 밖에 두며, 공개 URL로 직접 접근할 수 없어야 한다.

권한 기준은 기존 writable directory 정책과 같은 방향으로 둔다.

```bash
chmod 750 storage/sessions
```

installer는 다음 조건을 확인한다.

- `storage/sessions/`가 존재하거나 생성 가능하다.
- 디렉터리 여부, 읽기 가능 여부, 쓰기 가능 여부, 삭제 가능 여부를 각각
  검사한다.
- 동시에 두 요청이 같은 세션 파일을 갱신할 때 파일 잠금을 사용할 수 있다.
- 정리 작업은 만료된 세션 파일만 삭제하고, `storage/cache/`,
  `storage/uploads/`, `storage/logs/`를 건드리지 않는다.

### 2.3 DB 기반 세션

DB 기반 세션은 `user_session` 테이블과 `SessionRepository` 계약을 기준으로
한다. 세션 데이터는 로그인 사용자 식별자, 만료 시각, 무효화 상태처럼
서버에서 검증해야 하는 최소 값만 저장한다.

DB 기반 세션을 선택할 때는 다음 조건을 만족해야 한다.

- installer가 PDO MariaDB 연결과 `user_session` 스키마 존재 여부를
  확인할 수 있다.
- 세션 생성, 조회, 갱신, 삭제가 같은 저장소 계약을 통해 수행된다.
- 세션 갱신 주기는 모든 요청마다 무조건 쓰지 않고, 만료 연장이 필요한
  경우로 제한한다.
- 로그아웃과 관리자 무효화는 서버 쪽 레코드를 삭제하거나 만료 처리한다.

## 3. 공통 보안 기준

- 로그인 성공 시 세션 ID를 재발급한다.
- 세션 만료 시각은 Python 이식 원본인 `src/modules/user/session.py`의
  `Session.expires_at` 의미와 일치시킨다.
- 세션 저장소에는 비밀번호, DB 자격증명, 원문 쿠키, 장기 API 토큰을
  저장하지 않는다.
- 세션 처리 코드는 `php/src/Modules/` 도메인 코드에 직접 넣지 않고,
  `php/src/Security/` 같은 어댑터 계층에 둔다.
- 세션 정리 실패는 로그인 성공으로 숨기지 않고 진단 로그 또는 installer
  결과에 별도 경고로 남긴다.

## 4. Installer 검사 기준

installer requirement check는 다음 순서로 세션 저장소를 평가한다.

1. PHP 기본 세션 경로와 핸들러를 검사한다.
2. PHP 기본 세션이 안전하지 않거나 확인 불가하면 `storage/sessions/` 파일
   기반 세션을 검사한다.
3. 배포 설정이 DB 기반 세션을 명시하면 PDO MariaDB 연결과 `user_session`
   스키마를 검사한다.

검사 결과는 선택지별로 분리해서 표시한다. 예를 들어 PHP 기본 세션은
실패했지만 파일 기반 세션이 통과한 경우, installer는 "파일 기반 세션으로
설치 가능"을 표시하고 PHP 기본 세션 실패 사유를 함께 남긴다.

## 이 문서가 하지 않는 것

- PHP session adapter 코드를 작성하지 않는다.
- 쿠키 보안 속성 값을 정하지 않는다.
- 세션 저장소 마이그레이션 도구나 운영 UI를 구현하지 않는다.

## 관련 문서

- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) —
  세션 공통 보안 기준과 도메인 경계.
- [Writable Directories Policy](writable-directories-policy.md) —
  `storage/` 경로와 권한 기준.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) —
  PHP/PDO/MariaDB 공용 웹호스팅 요구사항.
- [Repository Port Contracts](repository-port-contracts.md) —
  `SessionRepository` 계약.
- [Cookie Security Policy](cookie-security-policy.md) — 쿠키
  `Secure`/`HttpOnly`/`SameSite` 속성 기준.
