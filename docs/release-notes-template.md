# Release Notes Template

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅 배포본의 릴리스 노트를 작성할 때 사용하는 기본 템플릿이다.
범위는 운영자가 업그레이드 가능 여부, 마이그레이션 필요 여부, 호환성, 검증 결과를
빠르게 판단하는 데 필요한 항목이다.

## 사용법

새 릴리스를 만들 때 이 파일의 템플릿을 복사해 릴리스별 노트로 작성한다. 배포 전에
마이그레이션 필요 여부와 cache clear 필요 여부를 반드시 채우고, 실제 적용한 QA
결과는 릴리스별 값으로 남긴다.

릴리스 노트는 배포 산출물과 같은 버전을 가리켜야 한다. `php/src/`, `php/public/`,
`php/vendor/`, `php/composer.lock`, `db/schema/`가 서로 다른 릴리스에서 섞인 상태를
정상 릴리스로 기록하지 않는다.

## 템플릿

```markdown
# Release Notes: <release-id>

## 릴리스 정보

- **릴리스 ID**: `<YYYY.MM.DD-N>` 또는 `<version>`
- **배포일**: `<YYYY-MM-DD>`
- **대상 패키지**: `with_vendor` / `without_vendor`
- **권장 PHP 버전**: `<version>`
- **권장 MariaDB 버전**: `<version>`
- **이전 릴리스에서 직접 업그레이드 가능 여부**: 가능 / 조건부 가능 / 불가

## 요약

- `<운영자가 알아야 할 주요 변경 1>`
- `<운영자가 알아야 할 주요 변경 2>`
- `<운영자가 알아야 할 주요 변경 3>`

## 마이그레이션 필요 여부

- **DB 마이그레이션 필요**: 예 / 아니오
- **현재 schema version**: `<version 또는 해당 없음>`
- **필요 schema version**: `<version 또는 해당 없음>`
- **포함된 마이그레이션**:
  - `<migration-id>` — `<변경 요약>`
- **호환성 판단**: additive / destructive / 데이터 보정 필요 / 해당 없음
- **적용 경로**: installer 자동 적용 / SQL 수동 적용 / 호스팅사 요청 / 해당 없음
- **롤백 주의사항**: `<이미 적용된 DB 변경과 이전 코드의 호환성>`

## 업그레이드 전 확인

- [ ] 현재 코드, `php/config/`, `storage/uploads/`, 데이터베이스 백업을 확보했다.
- [ ] document root가 `php/public/`을 가리킨다.
- [ ] 패키지 유형(`with_vendor` 또는 `without_vendor`)이 호스팅 환경과 맞는다.
- [ ] DB 마이그레이션이 필요하면 적용 권한과 실패 시 보정 절차를 확인했다.
- [ ] maintenance mode 또는 트래픽 차단 방법을 준비했다.

## 배포 절차 메모

- **파일 교체 방식**: symlink 전환 / FTP 덮어쓰기 / 호스팅 File Manager
- **Composer 처리**: 서버에서 실행 / `vendor/` 포함 패키지 사용
- **Cache clear 필요**: 예 / 아니오
- **정리 대상 cache**:
  - `storage/cache/`
  - PHP opcode cache
  - CDN 또는 static asset cache

## 호환성

- **지원 호스팅 유형**: Composer 가능 / Composer 불가 / 둘 다
- **새로 필요한 PHP extension**: `<extension>` / 없음
- **새로 필요한 writable directory**: `<path>` / 없음
- **설정 파일 변경**: `<config key>` / 없음
- **기존 데이터 형식 변경**: 있음 / 없음

## QA 결과

- [ ] `scripts/qa.sh`
- [ ] 설치 smoke test
- [ ] 업그레이드 smoke test
- [ ] `/installer` 또는 `/admin/diagnostics` schema version 확인
- [ ] 로그인, 문서 보기, 문서 편집, 검색 확인
- [ ] 오류 로그에서 PHP fatal error와 migration failure 없음

## 알려진 제한

- `<제한 또는 해당 없음>`

## 롤백 기준

- `<일반 트래픽을 열지 않고 이전 릴리스로 되돌릴 조건>`
- `<DB 마이그레이션 적용 후 코드 롤백 가능 여부>`

## 관련 문서

- `docs/shared-hosting-upgrade-procedure.md`
- `docs/shared-hosting-rollback-procedure.md`
- `docs/shared-hosting-migration-policy.md`
- `docs/shared-hosting-qa-checklist.md`
```

## 작성 기준

- 마이그레이션 필요 여부는 "예/아니오"로 먼저 판단하고, 필요한 경우 schema version과
  적용 경로를 함께 적는다.
- destructive migration 또는 데이터 보정이 포함되면 롤백 주의사항에 "코드만 롤백
  가능"이라고 쓰지 않는다.
- Composer 없는 배포본은 `vendor/`와 `composer.lock`이 같은 릴리스에서 생성되었는지
  명시한다.
- 설정 파일 변경이 있으면 새 기본값과 기존 설치본에서 수동으로 추가할 값을 적는다.
- QA 결과는 실행한 항목만 체크하고, 실행하지 못한 항목은 이유를 남긴다.

## 관련 문서

- [Shared Hosting Upgrade Procedure](shared-hosting-upgrade-procedure.md) — 업그레이드
  전 준비, 파일 교체, cache clear 절차.
- [Shared Hosting Rollback Procedure](shared-hosting-rollback-procedure.md) — DB
  backward compatibility와 롤백 기준.
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 공용
  웹호스팅 마이그레이션 적용 경로.
- [Shared Hosting QA Checklist](shared-hosting-qa-checklist.md) — 설치, 업그레이드,
  rollback QA 항목.
