# Shared Hosting Rollback Procedure

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅에 배포한 PHP 릴리스에서 장애가 발생했을 때 이전 릴리스로
되돌리는 최소 절차를 정의한다. 범위는 코드, 의존성, document root, 재생성 가능한
캐시, 데이터베이스 호환성 확인이다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, 설치/업그레이드 안내 작성자.
- **다루는 것**:
  - 롤백 시작 전 중단 기준과 현재 상태 보존.
  - 이전 릴리스 파일과 document root 복원 순서.
  - `composer.lock`과 `vendor/`를 같은 릴리스 기준으로 맞추는 절차.
  - DB backward compatibility 확인과 마이그레이션 후 코드 롤백 주의점.
  - 롤백 후 cache clear, smoke test, 운영 기록.
- **다루지 않는 것**:
  - 패키지 빌드 스크립트 구현.
  - 호스팅사별 제어판 자동화.
  - 데이터 복구 도구 또는 마이그레이션 down 스크립트 구현.

## 1. 롤백 결정 기준

다음 상황에서는 새 릴리스로 일반 트래픽을 열지 말고 롤백을 검토한다.

- [ ] `php/vendor/autoload.php` 누락, `Class not found`, PHP fatal error가 발생한다.
- [ ] 새 릴리스의 `php/public/`이 이전 `php/src/` 또는 이전 `vendor/`와 섞였다.
- [ ] schema version이 새 코드 요구사항보다 낮고 즉시 마이그레이션할 수 없다.
- [ ] 마이그레이션이 일부만 적용되어 installer 또는 diagnostics가 `migration_failed`
      상태를 표시한다.
- [ ] 주요 기능(로그인, 문서 보기, 문서 편집, 검색)이 배포 직후 실패한다.
- [ ] cache clear 후에도 이전 asset 또는 이전 PHP 클래스가 계속 실행된다.

롤백은 "이전 릴리스 전체로 되돌리는 것"을 기본값으로 한다. 특정 파일만 되돌리는
부분 롤백은 DB와 코드 호환성을 이미 확인한 경우에만 사용한다.

## 2. 롤백 전 보존 항목

롤백을 시작하기 전에 현재 실패 상태를 덮어쓰지 말고 최소한의 진단 정보를 남긴다.

- [ ] 현재 document root가 가리키는 경로 또는 실제 배포 디렉터리를 기록한다.
- [ ] 현재 릴리스 식별자, 이전 릴리스 식별자, 배포 시각을 기록한다.
- [ ] `php/config/` 운영 설정 파일을 백업한다.
- [ ] `storage/uploads/`, `storage/exports/`는 삭제하지 않고 그대로 보존한다.
- [ ] DB 변경이 있었으면 현재 schema version과 적용된 마이그레이션 목록을 기록한다.
- [ ] 가능하면 롤백 직전 DB 백업 또는 JSON export를 확보한다.
- [ ] 호스팅 error log에서 최근 PHP fatal error와 migration error를 보존한다.

`storage/cache/`는 재생성 가능한 파일만 담아야 하므로 보존 대상이 아니다.

## 3. DB Backward Compatibility 확인

코드 롤백 전에 이전 코드가 현재 DB schema와 함께 실행 가능한지 확인한다. 이미
적용된 DB 마이그레이션은 자동으로 되돌리지 않는다.

확인 항목:

- [ ] 새 마이그레이션이 **nullable 컬럼 추가**, **기본값이 있는 컬럼 추가**,
      **새 테이블 추가**, **새 인덱스 추가**처럼 이전 코드가 무시할 수 있는 변경인지
      확인한다.
- [ ] 새 마이그레이션이 **컬럼 삭제**, **컬럼 이름 변경**, **타입 축소**,
      **NOT NULL 제약 추가**, **기존 값 의미 변경**을 포함하면 이전 코드가 깨질 수
      있으므로 코드만 롤백하지 않는다.
- [ ] 새 코드가 생성한 데이터가 이전 코드의 enum, 상태값, JSON 구조, 길이 제한을
      벗어나지 않는지 확인한다.
- [ ] 부분 적용된 DDL이 있는 경우, MariaDB에서는 DDL이 암묵적으로 커밋될 수 있으므로
      트랜잭션 rollback으로 원상복구된다고 가정하지 않는다.
- [ ] schema version이 이전 코드의 허용 범위를 넘는 경우, maintenance mode를 유지하고
      `shared-hosting-migration-policy.md` 기준으로 호스팅사 보정 또는 데이터 복구
      절차를 먼저 결정한다.

판단 기준:

| 현재 DB 상태 | 코드 롤백 가능 여부 | 조치 |
|---|---|---|
| DB 변경 없음 | 가능 | 이전 릴리스 파일로 복원한다. |
| 이전 코드가 무시 가능한 additive 변경만 있음 | 대체로 가능 | 롤백 후 주요 읽기/쓰기 기능을 확인한다. |
| destructive 변경 또는 데이터 형식 변경 있음 | 위험 | 코드 롤백 전에 DB 보정 계획을 세운다. |
| 마이그레이션 일부만 적용됨 | 위험 | 일반 트래픽을 열지 말고 수동 보정한다. |

DB가 이미 새 schema로 올라갔더라도, 호환성이 확인되기 전에는 이전 코드를 배포하지
않는다. 구 코드가 새 컬럼을 무시하더라도, 쓰기 경로에서 기본값이나 제약을 만족하지
못하면 장애가 반복될 수 있다.

## 4. 파일 롤백 절차

가능하면 document root 또는 release symlink를 이전 릴리스의 `php/public/`으로
전환한다.

```text
/home/account/releases/previous-release/
  php/
    public/
    src/
    config/
    vendor/
    composer.lock
```

전환 순서:

1. maintenance mode를 켠다.
2. 현재 운영 설정 파일(`php/config/`)과 사용자 데이터(`storage/uploads/`)가 이전
   릴리스 파일로 덮이지 않도록 확인한다.
3. 이전 릴리스의 `php/src/`, `php/public/`, `php/config/*.sample`, `db/schema/`를
   복원한다.
4. Composer 없는 호스팅은 이전 릴리스의 `php/vendor/`와 `php/composer.lock`을 함께
   복원한다.
5. Composer 실행 가능 호스팅은 이전 릴리스의 `php/`에서
   `composer install --no-dev --prefer-dist --classmap-authoritative`를 실행한다.
6. document root를 이전 릴리스의 `php/public/`으로 전환한다.
7. `storage/cache/`와 opcode cache를 정리한다.

FTP/File Manager로 덮어쓰는 환경에서는 `php/public/`을 마지막에 복원한다. 이전
front controller가 아직 새 `src/` 또는 새 `vendor/`를 참조하는 중간 상태를 줄이기
위해서다.

## 5. Cache Clear

롤백 후에는 새 릴리스에서 생성된 재생성 가능한 캐시를 제거한다.

- [ ] `storage/cache/` 내부 파일을 삭제한다.
- [ ] 호스팅 제어판의 PHP opcode cache clear 기능을 실행한다.
- [ ] CDN 또는 reverse proxy를 사용한다면 HTML과 static asset cache를 purge한다.
- [ ] 이전 릴리스의 asset version이 HTML에 반영되는지 확인한다.

삭제하지 않는 항목:

- `storage/uploads/`
- `storage/logs/`
- `storage/exports/`
- DB 백업 파일

## 6. 롤백 후 검증

maintenance mode를 끄기 전에 다음 항목을 확인한다.

- [ ] `/installer` 또는 `/admin/diagnostics`가 PHP fatal error 없이 열린다.
- [ ] schema version 상태가 이전 코드에서 허용 가능한 상태로 표시된다.
- [ ] 오류 로그에 `Class not found`, `Failed opening required vendor/autoload.php`,
      migration failure가 새로 쌓이지 않는다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색이 정상 응답한다.
- [ ] 정적 asset이 이전 릴리스 버전으로 응답한다.
- [ ] 새 릴리스에서 추가한 데이터가 구 코드의 주요 화면에서 깨지지 않는다.

검증 후 maintenance mode를 끄고, 첫 30분 동안 error log와 diagnostics 상태를
확인한다.

## 7. 운영 기록

롤백 완료 후 다음 내용을 운영 기록에 남긴다.

- 롤백 시작/완료 시각.
- 실패한 릴리스와 복원한 릴리스 식별자.
- DB schema version과 적용된 마이그레이션 목록.
- DB backward compatibility 판단 결과.
- 복원한 파일 범위(`php/public/`, `php/src/`, `vendor/`, `composer.lock` 등).
- 수행한 cache clear 방식.
- 롤백 후 smoke test 결과와 남은 후속 조치.

## 관련 문서

- [Shared Hosting Upgrade Procedure](shared-hosting-upgrade-procedure.md) — 업그레이드
  절차와 롤백 시작 기준.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 공용
  웹호스팅 마이그레이션 적용과 실패 보정 기준.
- [Portable Restore Plan](portable-restore-plan.md) — 운영 백업 복원과 스키마 버전
  호환성 검사.
- [Composer Hosting Deployment](composer-hosting-deployment.md) — Composer 실행 가능
  호스팅의 의존성 설치와 롤백 기준.
- [No-Composer Hosting Deployment](no-composer-hosting-deployment.md) — `vendor/`
  포함 배포본의 업로드와 롤백 기준.
