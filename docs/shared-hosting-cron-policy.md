# Shared Hosting Cron Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

공용 웹호스팅(shared hosting) 배포에서 jobs sync runner를 어떻게 예약하고,
cron을 제공하지 않는 호스팅에서 어떤 웹 트리거 대안을 둘지 고정한다. 이 문서는
job 실행 정책과 운영 경계를 다루며, runner URL 형식과 제어판별 설정 예시는
후속 문서에서 다룬다.

## 목적

- shared hosting에서 상시 daemon 없이 job을 처리하는 기본 방식을 정한다.
- cron job을 사용할 수 있는 환경과 사용할 수 없는 환경의 대안을 분리한다.
- jobs sync runner가 짧게 실행되고 안전하게 종료되는 운영 기준을 둔다.
- 웹 트리거가 공개 공격면이 되지 않도록 최소 보안 요구사항을 명시한다.

## 적용 범위

- 검색 색인, 최근 변경, 캐시 정리처럼 `jobs` 큐에 쌓인 비동기 작업.
- PHP shared hosting 패키지에서 제공할 짧은 sync runner 실행 정책.
- installer와 운영 문서가 표시해야 하는 cron/web trigger 선택 기준.

적용되지 않는 것:

- long-running worker, Supervisor, systemd, Redis/RQ, Celery 배포.
- 호스팅사별 제어판 화면 캡처나 클릭 순서.
- job runner URL의 최종 라우트, 토큰 생성 UI, 실행 코드 구현.

## 1. 기본 실행 모델

shared hosting의 기본 runner는 **jobs sync runner**다. runner는 한 번 실행될 때
다음 원칙을 따른다.

- 큐에서 실행 가능한 job을 제한된 개수만 claim하고 처리한다.
- 각 실행은 짧게 끝나야 하며, 기본 목표는 30초 이내 종료다.
- 호스팅사의 PHP `max_execution_time`보다 작은 내부 시간 제한을 둔다.
- 다음 cron 또는 웹 트리거 호출이 남은 job을 이어서 처리할 수 있어야 한다.
- long-running daemon이 항상 떠 있다는 가정에 의존하지 않는다.

동시 실행과 claim 방식은
[Jobs Polling Portable Policy](jobs-polling-portable-policy.md)의 조건부
`UPDATE` 기준을 따른다. cron과 웹 트리거는 runner를 깨우는 방식만 다르고,
큐 처리 의미론은 같아야 한다.

## 2. Cron 권장 경로

호스팅사가 cron job 또는 scheduler를 제공하고 PHP CLI 실행을 허용하면 cron을
기본 권장 경로로 사용한다.

권장 조건:

- PHP CLI 경로를 확인할 수 있다.
- document root 밖의 애플리케이션 경로에서 runner를 실행할 수 있다.
- 1분에서 5분 사이의 반복 실행을 설정할 수 있다.
- cron output을 파일이나 호스팅 제어판 로그에서 확인할 수 있다.
- 실행 명령에 DB 비밀번호, installer secret, 토큰을 직접 노출하지 않는다.

운영 기준:

- 기본 주기는 5분이다.
- 빠른 색인 반영이 필요한 배포만 1분 주기를 선택한다.
- 같은 runner가 겹쳐 실행되어도 job claim update가 중복 실행을 막아야 한다.
- cron 실패가 누적되면 운영자는 웹 트리거 대안을 임시로 사용할 수 있다.

예시 명령은 이 문서에 고정하지 않는다. 호스팅사별 PHP 경로와 배포 경로가 달라
후속 runner URL/설정 문서에서 다룬다.

## 3. Web Trigger 대안

cron이나 PHP CLI를 제공하지 않는 shared hosting에서는 **web trigger**를
제한적 대안으로 둔다. web trigger는 HTTP 요청으로 같은 jobs sync runner를
짧게 실행하는 방식이다.

채택 조건:

- HTTPS가 활성화되어 있다.
- 예측 불가능한 runner secret 또는 서명 토큰을 요구한다.
- HTTP `GET` 또는 `POST` 한 번으로 제한된 batch만 처리한다.
- 성공, 처리 개수, 남은 큐 존재 여부를 운영자가 확인할 수 있다.
- 공개 사용자 화면이나 검색 엔진이 URL을 발견하지 못하도록 라우트와 응답을
  분리한다.

금지 조건:

- 토큰 없는 공개 runner endpoint.
- 로그인 세션 쿠키만으로 보호되는 runner endpoint.
- 무제한 loop 또는 요청 시간 끝까지 모든 job을 처리하는 endpoint.
- 웹 요청에 DB 자격증명이나 installer secret을 query string으로 넣는 방식.

web trigger는 cron을 완전히 대체하는 고신뢰 scheduler가 아니다. 방문자가 거의
없는 사이트에서는 외부 모니터링 서비스나 호스팅 제어판의 URL 호출 기능이
필요할 수 있으며, 이 경우에도 secret 보호와 rate limit을 유지한다.

## 4. Installer 표시 기준

installer requirement check는 job 실행 경로를 다음 순서로 표시한다.

1. cron 또는 scheduler 사용 가능 여부를 확인한다.
2. PHP CLI 경로와 document root 밖 runner 실행 가능 여부를 표시한다.
3. cron이 가능하면 "cron 권장" 상태와 기본 5분 주기를 안내한다.
4. cron이 불가능하면 web trigger 대안을 표시하고 HTTPS, secret, rate limit
   요구사항을 확인한다.
5. 두 경로가 모두 불가능하면 job 처리가 지연될 수 있음을 명확히 표시한다.

installer는 job runner를 즉시 구현하거나 예약하지 않는다. 설치 완료 전에
운영자가 선택해야 하는 실행 경로와 확인해야 할 제한만 보여준다.

## 5. 보안과 운영 경계

- runner secret은 document root 밖의 비공개 설정 파일에 저장한다.
- runner endpoint는 cache되지 않아야 하며, 검색 색인 대상에서 제외한다.
- 응답에는 secret, DB 오류 원문, 내부 파일 경로를 노출하지 않는다.
- 동일 secret으로 과도한 호출이 발생하면 rate limit 또는 짧은 cooldown을
  적용한다.
- job 실패 상세는 운영 로그에 남기고, HTTP 응답은 처리 요약만 반환한다.
- cron과 web trigger 모두 shared hosting 로그에서 최근 실행 시각과 실패 사유를
  추적할 수 있어야 한다.

## 이 문서가 하지 않는 것

- PHP job runner endpoint 또는 CLI command를 구현하지 않는다.
- 호스팅사별 cron 설정 예시를 작성하지 않는다.
- 외부 uptime monitor 서비스 연동을 구현하지 않는다.
- Redis/RQ/Celery 같은 상시 worker 배포를 추가하지 않는다.

## 관련 문서

- [Jobs Polling Portable Policy](jobs-polling-portable-policy.md) —
  portable job claim/update 의미론.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) —
  PHP/PDO/MariaDB 공용 웹호스팅 요구사항.
- [Config File Permission Policy](config-file-permission-policy.md) —
  runner secret과 로컬 설정 파일 보호 기준.
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) —
  PHP 런타임 보안 경계.
