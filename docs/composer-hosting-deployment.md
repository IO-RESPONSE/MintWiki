# Composer Hosting Deployment

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 SSH 또는 터미널에서 Composer를 실행할 수 있는 공용 웹호스팅에 PHP
배포 패키지를 올리고, 서버에서 `composer install`과 `composer update`를 구분해
운영하는 절차를 정의한다. 대상 환경은 cPanel, Plesk, DirectAdmin처럼 계정별
SSH를 제공하고 PHP CLI와 Composer 실행을 허용하는 shared hosting이다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, 패키징 스크립트 작성자.
- **다루는 것**:
  - Composer 실행 가능 호스팅에서 사용할 배포 패키지 선택 기준.
  - 최초 설치 시 서버에서 의존성을 설치하는 절차.
  - 기존 설치본을 업데이트할 때 lock 파일과 autoload를 갱신하는 절차.
- **다루지 않는 것**:
  - Composer 없는 호스팅의 `vendor/` 사전 업로드 절차.
  - 패키징 스크립트 구현 또는 배포 자동화.
  - 데이터베이스 마이그레이션, 파일 권한, installer 화면 구현.

## 1. 기본 원칙

Composer 실행 가능 호스팅에서는 배포 패키지에 `php/vendor/`를 포함하지 않는
`without_vendor` 옵션을 기본값으로 사용한다. 서버는 배포된 `php/composer.json`을
기준으로 운영 의존성을 설치하고, 릴리스에 `php/composer.lock`이 포함된 경우에는
그 lock 파일의 고정 버전을 그대로 재현한다.

패키지 선택은 `php/deployment-package-manifest.json`의 옵션을 따른다.

| 호스팅 조건 | 패키지 옵션 | 설명 |
|---|---|---|
| SSH와 Composer 사용 가능 | `without_vendor` | 서버에서 `composer install --no-dev` 실행. |
| SSH 없음 또는 Composer 금지 | `with_vendor` | 로컬/CI에서 생성한 `php/vendor/`를 함께 업로드. |
| Composer 실행은 가능하지만 메모리/시간 제한이 낮음 | `with_vendor` 권장 | 설치 중단 위험을 줄이기 위해 사전 생성한 `vendor/` 사용. |

운영 서버에서는 임의의 의존성 버전을 새로 고르지 않는다. 일반 배포와 업데이트는
항상 `composer install`을 사용한다. `composer update`는 의존성 버전을 변경하는
개발/릴리스 준비 단계에서만 사용한다.

## 2. 사전 확인

배포 전에 호스팅 계정에서 다음 항목을 확인한다.

```bash
php -v
composer --version
php -m | grep -E 'pdo|pdo_mysql|json'
```

확인 항목:

- [ ] PHP 버전이 `docs/shared-hosting-target-baseline.md`의 최소 요구사항을 만족한다.
- [ ] Composer가 SSH 또는 호스팅 패널 터미널에서 실행된다.
- [ ] `composer install --no-dev`를 실행할 수 있는 메모리와 시간 제한이 있다.
- [ ] document root는 `php/public/`을 가리킨다.
- [ ] `php/vendor/`, `php/composer.json`, `php/composer.lock`은 document root 밖에 있다.

Composer가 메모리 제한으로 실패하면 서버에서 설치를 반복하지 말고
`docs/no-composer-hosting-deployment.md`의 `with_vendor` 절차로 전환한다.

## 3. 최초 설치 절차

### 3.1 패키지 업로드

`without_vendor` 패키지는 기본 배포 입력만 업로드한다.

```text
php/composer.json
php/config/*.sample
php/public/**
php/src/**
db/schema/**
```

릴리스 정책상 `php/composer.lock`을 포함하는 경우에는 `php/composer.json`과 같은
릴리스에서 나온 파일을 함께 업로드한다. 현재 매니페스트의 `without_vendor`
모드는 `vendor/` 산출물을 제외하는 것이 핵심이며, `with_vendor` 모드는
`php/vendor/**`와 `php/composer.lock`을 함께 포함한다.

다음 파일과 디렉터리는 업로드하지 않는다.

```text
.git/
docs/
tasks/
tests/
php/tests/
scripts/
ops/
```

가능하면 새 릴리스 디렉터리에 먼저 업로드한다.

```text
/home/account/releases/2026-07-04/
  php/
    public/
    src/
    config/
    composer.json
```

### 3.2 서버에서 의존성 설치

업로드 후 SSH 또는 호스팅 패널 터미널에서 `php/` 디렉터리로 이동해 운영
의존성을 설치한다.

```bash
cd /home/account/releases/2026-07-04/php
composer install --no-dev --prefer-dist --classmap-authoritative
composer dump-autoload --no-dev --classmap-authoritative
```

검증 항목:

- [ ] `vendor/autoload.php`가 생성되었다.
- [ ] `composer install`이 실패 없이 끝났고, lock 파일이 있으면 그 기준으로 설치되었다.
- [ ] 개발 전용 패키지가 설치되지 않았다.
- [ ] platform requirement 오류가 없다.
- [ ] `vendor/`가 웹에서 직접 접근되지 않는다.

현재 `php/composer.json`은 PHP 엔진 제약만 선언하므로 네트워크 다운로드가 없어야
한다. 이후 런타임 패키지가 추가되더라도 운영 설치는 위 명령 형식을 유지한다.

### 3.3 공개 경로 전환

의존성 설치가 끝난 뒤 document root가 새 릴리스의 `php/public/`을 가리키게 한다.
심볼릭 링크 전환이 가능하면 새 릴리스 검증 후 링크를 바꾸고, 불가능하면
maintenance mode를 켠 상태에서 `php/public/`을 마지막에 덮어쓴다.

배포 직후 확인:

- [ ] `/installer` 또는 초기 진단 페이지가 PHP fatal error 없이 열린다.
- [ ] 오류 로그에 `Failed opening required vendor/autoload.php`가 없다.
- [ ] 오류 로그에 `Class not found` 또는 `Interface not found`가 없다.
- [ ] `composer.json`, `composer.lock`, `vendor/` URL 직접 접근이 403 또는 404로 차단된다.

## 4. 업데이트 절차

운영 업데이트는 새 코드를 배포한 뒤 서버에서 `composer install`을 다시 실행하는
방식으로 처리한다. 릴리스가 `composer.lock`을 포함한다면 새 코드와 새 lock 파일을
같이 배포한다.

```bash
cd /home/account/releases/2026-07-04/php
composer install --no-dev --prefer-dist --classmap-authoritative
composer dump-autoload --no-dev --classmap-authoritative
```

업데이트 원칙:

- [ ] 운영 서버에서 일반 배포 목적으로 `composer update`를 실행하지 않는다.
- [ ] 릴리스에 `composer.lock`이 포함된다면 코드와 같은 릴리스에서 온 파일을 배포한다.
- [ ] `vendor/`만 이전 릴리스에서 재사용하지 않는다.
- [ ] 의존성 설치 후 installer 또는 health check를 열어 autoload 오류를 확인한다.
- [ ] DB 변경이 포함된 릴리스는 `shared-hosting-migration-policy.md` 기준으로
      마이그레이션 순서를 먼저 따른다.

서버의 `composer.lock`이 배포본과 다르거나 수동 수정된 흔적이 있으면 운영
디렉터리에서 의존성을 고치지 말고, 릴리스 패키지를 다시 업로드한 뒤
`composer install`을 재실행한다.

## 5. `composer update` 사용 기준

`composer update`는 운영 서버의 일상 업데이트 명령이 아니다. 다음 조건을 모두
만족할 때만 릴리스 준비 환경에서 실행한다.

- [ ] 의존성 버전 변경이 이번 릴리스의 명시적 작업 범위에 포함된다.
- [ ] 로컬 또는 CI에서 테스트와 QA를 통과할 수 있다.
- [ ] 변경된 `php/composer.lock`이 코드 변경과 함께 리뷰된다.
- [ ] shared hosting PHP 버전과 확장 요구사항이 계속 충족된다.

릴리스 준비 예시:

```bash
cd php
composer update --no-dev --prefer-dist
composer dump-autoload --no-dev --classmap-authoritative
cd ..
scripts/qa.sh
```

위 절차로 갱신한 `php/composer.lock`을 릴리스에 포함한 뒤, 운영 서버에서는 다시
`composer install --no-dev`만 실행한다.

## 6. 롤백 기준

Composer 실행 가능 호스팅에서도 롤백은 코드, `composer.lock`, `vendor/` 상태를
같은 릴리스 기준으로 맞추어야 한다.

롤백 시:

- [ ] 이전 릴리스 디렉터리의 `php/public/`으로 document root를 되돌린다.
- [ ] 이전 릴리스 디렉터리에서 `composer install --no-dev --classmap-authoritative`를 실행한다.
- [ ] 현재 릴리스의 `vendor/`를 이전 코드와 섞지 않는다.
- [ ] installer 또는 health check를 다시 확인한다.
- [ ] DB 스키마 변경이 이미 적용된 경우에는 `shared-hosting-migration-policy.md`
      기준으로 코드 롤백 가능 여부를 먼저 판단한다.

## 관련 문서

- [No-Composer Hosting Deployment](no-composer-hosting-deployment.md) — Composer를
  실행할 수 없는 호스팅의 `vendor/` 사전 업로드 절차.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP/PDO/MariaDB
  공용 웹호스팅 요구사항.
- [PHP UI Deployment Checklist](php-ui-deployment-checklist.md) — shared hosting 업로드
  전후 UI 검증 절차.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — DB 마이그레이션
  적용 방식.
- [Public Docroot Policy](public-docroot-policy.md) — `php/public/` document root 기준.
