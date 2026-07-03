# Shared Hosting Upgrade Procedure

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅에 이미 설치된 PHP 배포본을 새 릴리스로 업그레이드할 때
운영자가 따라야 할 최소 절차를 정의한다. 범위는 파일 교체, 데이터베이스
마이그레이션 확인, 캐시 정리, 업그레이드 후 검증이다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, 설치/업그레이드 안내 작성자.
- **다루는 것**:
  - 새 릴리스 파일을 기존 설치본과 섞지 않고 교체하는 순서.
  - 업그레이드 전후 마이그레이션 상태 확인.
  - 재생성 가능한 cache 디렉터리와 opcode/static cache 정리.
  - 실패 시 이전 릴리스로 되돌릴 수 있는 중단 기준.
- **다루지 않는 것**:
  - 패키지 빌드 스크립트 구현.
  - cache clear CLI 또는 웹 UI 구현.
  - 호스팅사별 제어판 자동화.

## 1. 업그레이드 전 준비

업그레이드는 현재 운영 디렉터리를 직접 수정하기 전에 새 릴리스와 백업을 준비한
상태에서 시작한다.

확인 항목:

- [ ] 현재 코드, `php/config/`, `storage/uploads/`, 데이터베이스 백업을 확보한다.
- [ ] 새 패키지가 호스팅 조건에 맞는 `with_vendor` 또는 `without_vendor` 산출물이다.
- [ ] `php/composer.lock`과 `php/vendor/`는 같은 릴리스에서 나온 파일이다.
- [ ] document root는 `php/public/`을 가리킨다.
- [ ] `storage/cache/`, `storage/uploads/`, `storage/logs/` 경로가 분리되어 있다.
- [ ] 마이그레이션이 포함된 릴리스라면 적용 경로와 롤백 가능 여부를 먼저 확인한다.

## 2. 파일 교체 절차

가능하면 새 릴리스 디렉터리에 업로드한 뒤 document root를 전환한다.

```text
/home/account/releases/2026-07-04/
  php/
    public/
    src/
    config/
    vendor/
    composer.lock
  db/
    schema/
```

심볼릭 링크 전환이 불가능한 FTP/File Manager 환경에서는 maintenance mode를 켠 뒤
기존 설치본을 덮어쓴다. 이때 사용자 데이터와 런타임 파일은 교체 대상에서 제외한다.

덮어쓰기 순서:

1. `php/src/`, `php/config/*.sample`, `db/schema/`를 먼저 업로드한다.
2. Composer 없는 배포라면 `php/vendor/`와 `php/composer.lock`을 같은 릴리스 기준으로
   교체한다.
3. Composer 실행 가능 배포라면 서버의 `php/` 디렉터리에서
   `composer install --no-dev --prefer-dist --classmap-authoritative`를 실행한다.
4. `php/public/`을 마지막에 교체하거나 document root를 새 릴리스의 `php/public/`으로
   전환한다.
5. `php/config/`의 운영 설정 파일과 `storage/uploads/`는 새 패키지 파일로 덮어쓰지
   않는다.

새 front controller가 아직 교체되지 않은 의존성이나 소스 파일을 참조하지 않도록
`php/public/`을 마지막에 처리한다.

## 3. 마이그레이션 확인

DB 변경이 포함된 릴리스는 파일 전환 직후 일반 트래픽을 받기 전에 마이그레이션
상태를 확인한다.

권장 순서:

1. `/installer` 또는 `/admin/diagnostics`에서 현재 schema version과 필요한 schema
   version을 확인한다.
2. 대기 중인 마이그레이션 SQL이 있으면
   `shared-hosting-migration-policy.md`의 경로 A/B/C 중 현재 호스팅 권한에 맞는
   방법으로 적용한다.
3. 마이그레이션 적용 후 schema version을 다시 확인한다.
4. 실패한 마이그레이션이 있으면 새 코드로 트래픽을 열지 말고 maintenance mode를
   유지한 채 이전 릴리스 복구 여부를 판단한다.

마이그레이션이 필요한 릴리스에서는 코드만 먼저 교체하고 DB를 나중에 맞추는 상태를
장시간 유지하지 않는다. 새 코드가 새 컬럼이나 새 테이블을 전제로 동작할 수 있기
때문이다.

## 4. Cache Clear

업그레이드 후에는 재생성 가능한 캐시만 정리한다. 사용자 업로드, 로그, 백업, export
파일은 캐시 정리 대상이 아니다.

정리 대상:

- [ ] `storage/cache/`
- [ ] 호스팅 제어판에서 제공하는 PHP opcode cache clear 기능
- [ ] CDN 또는 reverse proxy를 사용하는 경우 static asset cache purge
- [ ] 브라우저가 오래된 asset을 참조하지 않도록 asset version이 새 릴리스와 맞는지 확인

공용 웹호스팅에서 CLI가 없으면 File Manager 또는 FTP로 `storage/cache/` 내부 파일만
삭제한다. 디렉터리 자체를 삭제했다면 같은 권한으로 다시 만든다.

```bash
mkdir -p storage/cache
chmod 750 storage/cache
```

`storage/uploads/`, `storage/logs/`, `storage/exports/`는 삭제하지 않는다.

## 5. 업그레이드 후 검증

maintenance mode를 끄기 전에 다음 항목을 확인한다.

- [ ] `/installer` 또는 `/admin/diagnostics`가 PHP fatal error 없이 열린다.
- [ ] schema version이 릴리스 요구사항과 일치한다.
- [ ] 오류 로그에 `Class not found`, `Failed opening required vendor/autoload.php`,
      migration failure가 없다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색 같은 기본 화면이 정상 응답한다.
- [ ] 정적 asset이 새 버전으로 응답하고 HTML은 `no-cache` 정책을 유지한다.
- [ ] `storage/cache/`는 비어 있거나 새 요청으로 재생성된 파일만 포함한다.

검증이 끝나면 업그레이드 시각, 릴리스 식별자, 적용한 마이그레이션, 수행한 cache
clear 방식을 운영 기록에 남긴다.

## 6. 중단과 롤백 기준

다음 상황에서는 일반 트래픽을 열지 않는다.

- [ ] 파일 업로드가 중간에 실패했다.
- [ ] `php/vendor/autoload.php`를 읽을 수 없다.
- [ ] schema version이 새 코드 요구사항보다 낮다.
- [ ] 마이그레이션 일부만 적용되었고 재시도 또는 수동 보정이 필요하다.
- [ ] cache clear 후에도 이전 asset이나 이전 PHP 클래스가 계속 실행된다.

롤백은 코드, `composer.lock`, `vendor/`, document root를 같은 이전 릴리스 기준으로
되돌린다. 이미 적용된 DB 마이그레이션은 자동으로 되돌리지 않으며, 먼저
`shared-hosting-migration-policy.md`의 롤백 판단 기준을 따른다.

## 관련 문서

- [Composer Hosting Deployment](composer-hosting-deployment.md) — Composer 실행 가능
  호스팅의 의존성 설치 절차.
- [No-Composer Hosting Deployment](no-composer-hosting-deployment.md) — `vendor/`
  사전 업로드 절차.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 공용
  웹호스팅 마이그레이션 적용 경로.
- [Writable Directories Policy](writable-directories-policy.md) — `storage/cache`,
  `storage/uploads`, `storage/logs` 분리 정책.
- [PHP UI Deployment Checklist](php-ui-deployment-checklist.md) — 배포 전후 UI 검증
  항목.
- [PHP UI Rollback Checklist](php-ui-rollback-checklist.md) — UI 배포 롤백 기준.
