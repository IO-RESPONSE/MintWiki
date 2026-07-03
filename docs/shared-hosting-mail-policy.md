# Shared Hosting Mail Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅(shared hosting) 배포에서 알림 메일을 전송할 때 SMTP와 PHP
`mail()` 함수 중 어떤 방식을 선택할지 고정한다. 이 문서는 0637(email adapter
skeleton)이 구현할 어댑터의 입력 정책이며, 알림 기능 자체의 종류와 화면은
후속 태스크에서 다룬다.

## 목적

- shared hosting에서 재현 가능한 메일 전송 기본값을 정한다.
- installer requirement check가 확인해야 할 SMTP와 `mail()` 조건을 고정한다.
- 메일 전송 실패가 도메인 로직에 프레임워크나 호스팅사별 API 의존성을 만들지
  않도록 경계를 명확히 한다.

## 적용 범위

- 계정 확인, 비밀번호 재설정, 관리자 알림처럼 애플리케이션이 발송하는
  트랜잭션 메일.
- PHP 웹호스팅 패키지에서 사용할 메일 전송 어댑터 선택.
- installer가 설치 전에 확인해야 하는 메일 전송 요구사항.

적용되지 않는 것:

- 뉴스레터, 대량 발송, 마케팅 자동화.
- 외부 메일 서비스의 과금, 반송 처리, 수신 거부 관리.
- 메일 템플릿 디자인과 발송 화면 구현.

## 1. 선택 원칙

메일 전송 방식은 다음 우선순위로 선택한다.

| 선택지 | 채택 조건 | 금지 또는 보류 조건 | 비고 |
|---|---|---|---|
| 인증 SMTP | 호스팅사 또는 운영자가 SMTP host, port, encryption, username, password를 제공하고 installer가 연결·인증·테스트 발송을 통과한다. | SMTP 자격증명을 저장할 비공개 설정 경로가 없거나, TLS 검증을 끄지 않으면 연결할 수 없다. | 기본 권장값이다. 호스팅사 변경과 PHP 런타임 설정 차이를 가장 적게 탄다. |
| PHP `mail()` | 호스팅사가 `mail()` 사용을 명시적으로 허용하고 envelope sender 설정, 발신 도메인 정합성, 테스트 발송을 모두 확인할 수 있다. | `mail()`이 비활성화되어 있거나, 발신자 변조 제한을 알 수 없거나, 전송 성공 여부를 운영자가 추적할 수 없다. | SMTP를 제공하지 않는 저가 shared hosting의 제한적 대안이다. |
| 발송 비활성화 | SMTP와 `mail()`이 모두 확인되지 않았고, 설치가 메일 기능 없이 진행되도록 운영자가 명시적으로 선택한다. | 비밀번호 재설정처럼 메일이 필요한 기능을 활성화해야 하는 배포. | installer는 설치 가능 여부와 기능 제한을 분리해서 표시한다. |

기본 권장값은 **인증 SMTP를 먼저 검사하고, 실패하면 PHP `mail()`을 제한적
대안으로 검사**하는 것이다. `mail()`은 PHP 표준 함수라는 이유만으로 기본값으로
채택하지 않는다.

## 2. SMTP 기준

SMTP 방식은 호스팅사 메일 계정이나 운영자가 지정한 외부 SMTP 계정을 사용한다.
설정 파일에는 다음 값을 둔다.

- SMTP host
- SMTP port
- encryption mode (`tls`, `ssl`, `none`)
- username
- password
- default sender address
- default sender name

운영 배포에서는 `tls` 또는 `ssl`을 기본으로 요구한다. `none`은 로컬 개발이나
호스팅사 내부 relay처럼 별도 네트워크 통제가 있는 환경에서만 허용하며, installer
결과에 경고를 남긴다. TLS 인증서 검증을 끄는 설정은 패키지 기본값으로 제공하지
않는다.

SMTP 자격증명은 `docs/config-file-permission-policy.md`의 원칙에 따라 공개
document root 밖의 비공개 설정 파일에 저장한다. 로그에는 SMTP password,
인증 토큰, 전체 DSN을 남기지 않는다.

## 3. PHP `mail()` 기준

PHP `mail()`은 다음 조건을 모두 만족할 때만 선택할 수 있다.

- `mail` 함수가 `disable_functions`에 포함되어 있지 않다.
- 호스팅사가 `sendmail_path` 또는 내부 MTA를 제공한다.
- 운영자가 발신 도메인의 SPF, DKIM, DMARC 설정 상태를 확인할 수 있다.
- default sender address가 설치 도메인 또는 호스팅사가 허용한 도메인과
  일치한다.
- installer 테스트 발송이 성공하고, 운영자가 실제 수신 또는 메일 로그를
  확인할 수 있다.

`mail()` 반환값만으로 배달 성공을 판단하지 않는다. PHP `mail()`의 성공은
대개 로컬 MTA에 메시지를 넘겼다는 뜻일 뿐이며, 실제 수신함 도착이나 반송
상태를 보장하지 않는다.

## 4. Installer 검사 기준

installer requirement check는 다음 순서로 메일 전송 환경을 평가한다.

1. 메일 기능을 사용할지, 또는 발송 비활성화로 설치할지 운영자 선택을 받는다.
2. SMTP 설정이 있으면 host, port, encryption, 인증 정보를 검사한다.
3. SMTP 연결과 인증에 성공하면 테스트 메일을 발송하고 결과를 기록한다.
4. SMTP가 없거나 실패하면 `mail()` 사용 가능 여부, `sendmail_path`,
   `disable_functions`, 발신자 주소를 검사한다.
5. `mail()` 테스트 발송을 수행하되, 반환값과 운영자 수신 확인을 분리해서
   표시한다.
6. 두 방식이 모두 실패하면 메일 기능 비활성화 상태로 설치할 수 있는지와
   제한되는 기능을 표시한다.

검사 결과는 SMTP와 `mail()`을 분리해서 보여준다. 예를 들어 SMTP 인증은
실패했지만 `mail()` 테스트가 통과한 경우, installer는 "`mail()` 제한 모드로
설치 가능"을 표시하고 SMTP 실패 사유를 함께 남긴다.

## 5. 어댑터 경계

- 도메인 계층은 메일 발송 라이브러리, SMTP 클라이언트, PHP `mail()` 함수를
  직접 호출하지 않는다.
- PHP 구현은 `php/src/Modules/` 도메인 코드가 아니라 `php/src/App/` 또는
  동등한 어댑터 계층에서 전송 방식을 선택한다.
- 도메인 로직은 "메일 발송 요청"과 "발송 실패"를 의미 있는 결과로 다루고,
  호스팅사별 오류 메시지 파싱에 의존하지 않는다.
- 발송 실패는 사용자에게 민감 정보를 노출하지 않고, 운영 로그에는 수신자,
  메시지 종류, 실패 코드처럼 진단에 필요한 최소 정보만 남긴다.

## 이 문서가 하지 않는 것

- email adapter PHP 코드를 작성하지 않는다.
- 비밀번호 재설정, 계정 확인, 관리자 알림 기능을 구현하지 않는다.
- 외부 메일 서비스별 상세 설정 화면을 설계하지 않는다.
- 대량 메일 발송 정책이나 반송 처리 파이프라인을 정의하지 않는다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) —
  PHP/PDO/MariaDB 공용 웹호스팅 요구사항.
- [Config File Permission Policy](config-file-permission-policy.md) —
  SMTP 자격증명과 로컬 설정 파일 보호 기준.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) —
  PHP 런타임 보안 경계.
- [Writable Directories Policy](writable-directories-policy.md) —
  로그와 임시 파일을 둘 수 있는 비공개 저장 경로 기준.
