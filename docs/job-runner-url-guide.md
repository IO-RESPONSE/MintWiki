# Job Runner URL Guide

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅(shared hosting)에서 jobs sync runner를 예약할 때
운영자에게 보여줄 runner URL 형식과 cron 설정 예시를 고정한다. 실행 정책은
[Shared Hosting Cron Policy](shared-hosting-cron-policy.md)를 따른다.

## 목적과 범위

- **대상**: shared hosting 운영자, installer 안내 문구, 배포 문서 작성자.
- **다루는 것**:
  - cron 또는 호스팅 scheduler에 넣을 runner 호출 형식.
  - web trigger URL 형식과 secret 취급 기준.
  - cPanel, Plesk, DirectAdmin, URL 호출형 scheduler 예시.
- **다루지 않는 것**:
  - PHP runner endpoint 또는 CLI command 구현.
  - runner secret 생성 UI.
  - 호스팅사별 화면 캡처나 클릭 순서.

## 1. 기본 URL 형식

web trigger runner URL은 다음 형식을 기준으로 안내한다.

```text
https://example.com/_jobs/run?token=RUNNER_SECRET
```

경로 의미:

| 항목 | 기준 |
|---|---|
| `https://example.com` | 설치 도메인의 HTTPS origin. HTTP URL은 사용하지 않는다. |
| `/_jobs/run` | 공개 사용자 화면과 분리된 job runner 전용 경로. |
| `token` | document root 밖 비공개 설정에 저장된 runner secret. |

`RUNNER_SECRET`은 예측 불가능한 긴 값이어야 하며, installer secret이나 DB
비밀번호를 재사용하지 않는다. 운영자가 외부 URL 호출 서비스에 등록할 때는 해당
서비스의 로그와 알림 화면에 token이 노출될 수 있음을 안내한다.

## 2. Cron 권장 명령

PHP CLI를 사용할 수 있으면 URL 호출보다 CLI runner가 우선이다. 실제 command
이름은 runner 구현 태스크에서 고정하되, 운영 문서는 다음 구조를 사용한다.

```bash
*/5 * * * * /usr/bin/php /home/account/app/php/scripts/jobs-runner.php --quiet >> /home/account/app/storage/logs/jobs-cron.log 2>&1
```

운영자가 바꿔야 하는 값:

| 자리표시자 | 설명 |
|---|---|
| `/usr/bin/php` | 호스팅 제어판 또는 `which php`로 확인한 PHP CLI 경로. |
| `/home/account/app` | document root 밖 애플리케이션 설치 경로. |
| `storage/logs/jobs-cron.log` | 공개 URL로 접근할 수 없는 cron 로그 파일. |

기본 주기는 5분이다. 빠른 색인 반영이 필요한 운영 환경만 1분 주기를 선택한다.
명령줄에는 DB 비밀번호, installer secret, runner token을 직접 넣지 않는다.

## 3. URL 호출형 Scheduler 예시

PHP CLI가 없고 호스팅사가 URL 호출형 scheduler만 제공하면 다음 중 하나를
사용한다.

```text
GET https://example.com/_jobs/run?token=RUNNER_SECRET
```

또는 header를 설정할 수 있는 scheduler라면 query string 대신 header를 권장한다.

```text
POST https://example.com/_jobs/run
X-Job-Runner-Token: RUNNER_SECRET
```

URL 호출형 scheduler 설정 기준:

- HTTPS URL만 등록한다.
- 호출 주기는 기본 5분으로 둔다.
- redirect follow를 끄거나, 최종 응답이 같은 origin인지 확인한다.
- 응답 본문은 저장하지 않거나 짧은 요약만 저장한다.
- 연속 실패 시 운영자에게 알림을 보내도록 설정한다.

## 4. 제어판별 예시

### 4.1 cPanel Cron Jobs

PHP CLI가 가능한 경우:

```bash
*/5 * * * * /usr/local/bin/php /home/account/wiki/php/scripts/jobs-runner.php --quiet >> /home/account/wiki/storage/logs/jobs-cron.log 2>&1
```

URL 호출만 가능한 경우:

```bash
*/5 * * * * /usr/bin/curl -fsS --max-time 25 'https://example.com/_jobs/run?token=RUNNER_SECRET' >> /home/account/wiki/storage/logs/jobs-cron.log 2>&1
```

### 4.2 Plesk Scheduled Tasks

PHP script 유형을 제공하면 script path에 다음 값을 넣는다.

```text
/home/account/wiki/php/scripts/jobs-runner.php
```

arguments에는 비밀값을 넣지 않는다.

URL fetch 유형만 제공하면 다음 URL을 등록한다.

```text
https://example.com/_jobs/run?token=RUNNER_SECRET
```

### 4.3 DirectAdmin Cron Jobs

DirectAdmin의 cron command 칸에는 전체 명령을 넣는다.

```bash
/usr/bin/php /home/account/wiki/php/scripts/jobs-runner.php --quiet >> /home/account/wiki/storage/logs/jobs-cron.log 2>&1
```

분(minute) 필드는 `*/5`를 기본값으로 둔다.

### 4.4 외부 모니터링 서비스

호스팅 제어판에 cron과 URL scheduler가 모두 없으면 외부 모니터링 서비스의
periodic HTTP check를 제한적 대안으로 사용할 수 있다.

```text
https://example.com/_jobs/run?token=RUNNER_SECRET
```

외부 서비스에는 runner token이 저장되므로, 최소 권한 계정으로 관리하고 token
교체 절차를 운영 문서에 남긴다. 외부 서비스가 응답 본문이나 전체 URL을 공개
status page에 노출하는 설정은 사용하지 않는다.

## 5. 응답 확인 기준

runner 응답은 운영자가 성공 여부만 판별할 수 있을 만큼 짧아야 한다.

```json
{
  "ok": true,
  "processed": 3,
  "remaining": false
}
```

오류 응답은 secret, DB 오류 원문, 내부 파일 경로를 포함하지 않는다. 자세한 실패
사유는 `storage/logs/` 아래의 비공개 로그나 호스팅 error log에서 확인한다.

## 6. 운영 체크리스트

- [ ] runner URL은 HTTPS를 사용한다.
- [ ] runner token은 installer secret, DB 비밀번호와 다르다.
- [ ] cron 또는 scheduler 주기는 기본 5분이다.
- [ ] cron 로그는 document root 밖에 저장된다.
- [ ] 실패 알림이나 최근 실행 시각을 확인할 수 있다.
- [ ] runner endpoint는 검색 색인과 공개 navigation에 노출되지 않는다.

## 관련 문서

- [Shared Hosting Cron Policy](shared-hosting-cron-policy.md) — jobs sync runner
  실행 정책과 web trigger 보안 기준.
- [Config File Permission Policy](config-file-permission-policy.md) — runner secret
  저장 위치와 설정 파일 권한 기준.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP CLI,
  HTTPS, rewrite 등 shared hosting 요구사항.
