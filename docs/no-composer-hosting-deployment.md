# No-Composer Hosting Deployment

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 Composer를 실행할 수 없는 공용 웹호스팅에 PHP 배포 패키지를 올릴 때,
`vendor/` 디렉터리를 로컬 또는 CI에서 미리 준비해 업로드하는 절차를 정의한다.
대상 환경은 SSH가 없거나, `composer install` 실행이 금지되어 있거나, 실행 시간과
메모리 제한 때문에 서버에서 의존성을 설치할 수 없는 plain FTP/cPanel/Plesk 계정이다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, 패키징 스크립트 작성자.
- **다루는 것**:
  - Composer 없는 호스팅에서 사용할 배포 패키지 선택 기준.
  - 배포 전에 `php/vendor/`를 생성하고 검증하는 절차.
  - FTP/File Manager 업로드 순서와 배포 후 확인 항목.
- **다루지 않는 것**:
  - 호스팅 서버에서 Composer를 실행하는 절차.
  - 패키징 스크립트 구현 또는 배포 자동화.
  - 데이터베이스 마이그레이션, 파일 권한, installer 화면 구현.

## 1. 기본 원칙

Composer 없는 호스팅에서는 **서버가 의존성을 설치하지 않는다**. 배포자는 개발
환경이나 CI에서 의존성을 설치한 뒤, `php/vendor/`와 `php/composer.lock`을 포함한
패키지를 호스팅 계정에 업로드한다.

패키지 선택은 `php/deployment-package-manifest.json`의 옵션을 따른다.

| 호스팅 조건 | 패키지 옵션 | 설명 |
|---|---|---|
| SSH와 Composer 사용 가능 | `without_vendor` | 서버에서 `composer install --no-dev` 실행 가능. |
| SSH 없음 또는 Composer 금지 | `with_vendor` | 로컬/CI에서 생성한 `php/vendor/`를 함께 업로드. |
| 서버 PHP 버전이 개발 환경과 다름 | `with_vendor` + PHP 버전 일치 빌드 | 로컬/CI PHP 버전을 호스팅 PHP 버전과 맞춘 뒤 패키징. |

`with_vendor` 패키지는 운영 서버에서 Composer 네트워크 접근, 플러그인 실행,
패키지 다운로드가 일어나지 않도록 만든다.

## 2. 사전 준비

배포 전 로컬 또는 CI 환경에서 호스팅 서버와 같은 주 버전의 PHP를 사용한다.
호스팅 서버가 PHP 8.2라면 패키징 환경도 PHP 8.2를 사용한다.

```bash
cd php
php -v
composer install --no-dev --prefer-dist --classmap-authoritative
composer dump-autoload --no-dev --classmap-authoritative
cd ..
```

검증 항목:

- [ ] `php/vendor/autoload.php`가 존재한다.
- [ ] `php/composer.lock`이 현재 `php/composer.json`과 일치한다.
- [ ] `composer install` 결과에 platform requirement 오류가 없다.
- [ ] 개발 전용 패키지가 배포용 `vendor/`에 포함되지 않는다.
- [ ] 호스팅 PHP 버전과 `composer.lock`의 platform 요구사항이 충돌하지 않는다.

## 3. 패키지 구성

Composer 없는 호스팅용 패키지는 기본 배포 입력에 다음 파일을 추가로 포함한다.

```text
php/composer.lock
php/vendor/**
```

반대로 다음 파일과 디렉터리는 업로드하지 않는다.

```text
.git/
docs/
tasks/
tests/
php/tests/
scripts/
ops/
```

`php/vendor/`는 document root 밖에 두는 것을 기본값으로 한다. document root는
`php/public/`이어야 하며, 브라우저가 `vendor/` 내부 파일을 직접 다운로드할 수
있으면 안 된다.

## 4. 업로드 절차

### 4.1 새 배포 디렉터리에 먼저 업로드

가능하면 현재 운영 디렉터리를 직접 덮어쓰지 말고 새 릴리스 디렉터리에 업로드한다.

```text
/home/account/releases/2026-07-04/
  php/
    public/
    src/
    config/
    vendor/
    composer.lock
```

호스팅사가 심볼릭 링크 전환을 허용하지 않으면, 제어판 File Manager 또는 FTP에서
maintenance mode를 켠 뒤 같은 구조로 덮어쓴다.

### 4.2 업로드 순서

1. `php/vendor/`를 먼저 업로드한다.
2. `php/src/`, `php/config/*.sample`, `db/schema/`를 업로드한다.
3. `php/public/`을 마지막에 업로드한다.
4. document root가 새 `php/public/`을 가리키는지 확인한다.
5. installer 또는 health check 페이지를 열어 autoload 오류가 없는지 확인한다.

`php/public/`을 마지막에 올리는 이유는 새 front controller가 아직 업로드되지 않은
`vendor/` 또는 `src/`를 참조해 500 오류를 내는 시간을 줄이기 위해서다.

## 5. 배포 후 확인

업로드 직후 다음 항목을 확인한다.

- [ ] `/installer` 또는 초기 진단 페이지가 PHP fatal error 없이 열린다.
- [ ] 오류 로그에 `Failed opening required vendor/autoload.php`가 없다.
- [ ] 오류 로그에 `Class not found` 또는 `Interface not found`가 없다.
- [ ] `vendor/` URL 직접 접근이 403 또는 404로 차단된다.
- [ ] `php/public/` 아래 정적 asset이 정상 응답한다.
- [ ] DB 설정과 마이그레이션 상태는 별도 정책 문서 절차에 따라 확인한다.

문제가 있으면 먼저 `php/vendor/autoload.php` 누락, FTP 전송 실패, 대소문자 차이,
PHP 버전 불일치를 확인한다.

## 6. 롤백 기준

Composer 없는 호스팅에서는 서버에서 의존성을 다시 계산할 수 없으므로, 롤백도
이전 릴리스의 `vendor/`와 `composer.lock`을 함께 복원해야 한다.

롤백 시:

- [ ] 이전 릴리스의 `php/vendor/`를 현재 코드와 섞지 않는다.
- [ ] 이전 릴리스의 `php/composer.lock`을 함께 복원한다.
- [ ] `php/public/` 전환 후 installer 또는 health check를 다시 확인한다.
- [ ] DB 스키마 변경이 이미 적용된 경우에는 `shared-hosting-migration-policy.md`
      기준으로 코드 롤백 가능 여부를 먼저 판단한다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP/PDO/MariaDB
  공용 웹호스팅 요구사항.
- [PHP UI Deployment Checklist](php-ui-deployment-checklist.md) — shared hosting 업로드
  전후 UI 검증 절차.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — DB 마이그레이션
  적용 방식.
- [Public Docroot Policy](public-docroot-policy.md) — `php/public/` document root 기준.
