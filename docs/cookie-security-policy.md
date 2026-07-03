# Cookie Security Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅(shared hosting) 배포에서 인증·세션 쿠키에 적용할 보안 속성
기준을 고정한다. 이 문서는 0634(cookie 보안 정책)의 산출물이며,
`docs/shared-hosting-session-policy.md`가 다루는 세션 저장소 선택과는
별개로 쿠키 전달 정책만 정한다.

## 목적

- 세션 쿠키의 `Secure`, `HttpOnly`, `SameSite` 기준을 둔다.
- installer requirement check와 PHP session adapter가 같은 쿠키 속성
  기본값을 쓰도록 한다.
- shared hosting 환경에서도 HTTPS 배포를 기본 전제로 두고, 예외를 명확히
  제한한다.

## 적용 범위

- 로그인 세션 쿠키.
- CSRF 상태를 세션과 묶어 검증할 때 쓰는 서버 관리 쿠키.
- PHP 런타임의 `session_set_cookie_params()` 또는 동등한 응답 쿠키 설정.

적용되지 않는 것:

- 세션 저장소 선택(PHP 기본 세션, 파일 기반 세션, DB 기반 세션).
- Remember-me 같은 장기 로그인 토큰 설계.
- 서드파티 분석, 광고, 외부 위젯 쿠키.

## 1. 기본 속성

| 속성 | 기본값 | 기준 |
|---|---|---|
| `Secure` | `true` | HTTPS 요청에서만 쿠키를 전송한다. |
| `HttpOnly` | `true` | 브라우저 JavaScript에서 세션 쿠키를 읽지 못하게 한다. |
| `SameSite` | `Lax` | 일반 탐색 로그인 흐름은 유지하면서 교차 사이트 요청의 자동 전송을 줄인다. |

세션 쿠키는 위 세 속성을 모두 명시해야 한다. 브라우저 기본값에 기대거나,
호스팅사의 PHP 기본 설정에 맡기지 않는다.

## 2. Secure 기준

- 운영 배포는 HTTPS를 전제로 하며 세션 쿠키는 `Secure=true`로 발급한다.
- installer requirement check는 현재 설치 URL이 HTTPS인지 확인하고,
  HTTPS가 아니면 운영 설치 통과로 취급하지 않는다.
- 로컬 개발이나 CLI 테스트처럼 HTTPS가 없는 환경은 별도 개발 설정에서만
  `Secure=false`를 허용한다. 이 예외는 패키지 기본값이 아니며 운영
  설정 파일에 저장하지 않는다.
- 프록시나 shared hosting 제어판 뒤에서 동작할 때도 앱이 신뢰할 수 있는
  HTTPS 판정 값이 없으면 `Secure=false`로 낮추지 않고 설치 경고를 낸다.

## 3. HttpOnly 기준

- 세션 식별자와 서버 관리 인증 쿠키는 `HttpOnly=true`로 발급한다.
- UI 코드가 로그인 상태를 알아야 할 때는 쿠키 값을 읽지 않고 서버 렌더링
  상태나 별도 응답 모델을 사용한다.
- CSRF 토큰을 JavaScript가 읽어야 하는 설계는 이 정책의 기본 범위가
  아니다. 그런 쿠키가 필요해지는 태스크는 세션 쿠키와 이름, 수명, 용도를
  분리해서 별도 정책으로 다룬다.

## 4. SameSite 기준

- 기본값은 `SameSite=Lax`다.
- 일반 로그인, 로그아웃, 문서 생성·수정 폼 제출은 같은 사이트 요청과
  최상위 탐색 흐름에서 동작해야 하므로 `Lax`를 기준으로 검증한다.
- `SameSite=None`은 외부 도메인 iframe, 교차 사이트 SSO 콜백처럼 명확한
  요구가 생긴 경우에만 허용하며, 반드시 `Secure=true`와 함께 사용한다.
- `SameSite=Strict`는 보안상 더 강하지만 외부 링크에서 돌아오는 로그인
  흐름을 깨뜨릴 수 있으므로 패키지 기본값으로 쓰지 않는다.

## 5. Installer 검사 기준

installer requirement check는 쿠키 정책을 다음 순서로 확인한다.

1. 설치 URL 또는 감지된 public base URL이 HTTPS인지 확인한다.
2. PHP 런타임이 `Secure`, `HttpOnly`, `SameSite` 속성을 명시해서 쿠키를
   발급할 수 있는지 확인한다.
3. 기본 세션 쿠키 설정이 `Secure=true`, `HttpOnly=true`, `SameSite=Lax`
   인지 표시한다.
4. 개발 환경 예외가 켜져 있으면 운영 설치가 아니라는 경고를 표시한다.

## 이 문서가 하지 않는 것

- PHP session adapter 코드를 수정하지 않는다.
- 세션 저장소나 `user_session` 스키마를 바꾸지 않는다.
- Remember-me 토큰, OAuth/SSO 예외, 서드파티 쿠키 동의 UI를 설계하지
  않는다.

## 관련 문서

- [Shared Hosting Session Policy](shared-hosting-session-policy.md) —
  세션 저장소 선택 기준.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) —
  PHP 런타임 보안 기준과 세션 경계.
- [Public Docroot Policy](public-docroot-policy.md) — 공개 웹 루트 기준.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) —
  PHP/PDO/MariaDB 공용 웹호스팅 요구사항.
