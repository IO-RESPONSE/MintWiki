# Installer Lock File Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

설치 완료 후 installer 재실행을 차단하기 위한 lock file 기준을 정의한다.

## 목적

installer는 데이터베이스 스키마와 관리자 계정 생성이 끝난 뒤 다시 실행되면 안 된다.
완료 상태를 파일로 남겨 shared hosting 환경에서도 다음을 보장한다:

- 설치 완료 후 `/install` 계열 route 접근을 차단한다.
- 데이터베이스 연결 오류가 일시적으로 발생해도 완료된 설치본을 신규 설치처럼 열지 않는다.
- lock file은 document root 밖의 비공개 저장소에 둔다.

## Lock File 위치

기본 파일명은 `install.lock`이다.

**0688 정정**: 이 절 초안은 `storage/installer/` 아래를 기본 위치로
적었지만, 실제 구현(`MintWiki\Installer\InstallerLock::atDefaultPath()`,
태스크 0682)은 `php/config/`(비공개 `local-config.php`와 같은 디렉터리)
아래에 `install.lock`을 만든다. `docs/config-file-permission-policy.md`,
`docs/iowiki-shared-hosting-porting-log.md` §3이 이미 문서화한 것과 같은
디렉터리다 — 실제 route는 `/install`이며, lock file은 아래처럼 배치된다.

```text
/home/user/wiki/            # (FTP 배포에서는 계정 FTP 루트)
├── php/
│   └── public/              # document root
├── src/
├── vendor/
└── config/
    ├── local-config.php     # DB 접속 정보(설치 마법사가 기록)
    └── install.lock         # 설치 완료 lock file
```

`php/public/`(document root) 안에는 lock file을 두지 않는다. URL로 직접
내려받을 수 있는 위치에 lock file이 있으면 설치 시각과 운영 상태가 노출될
수 있다.

## 생성 시점

installer는 모든 필수 단계가 성공한 뒤 마지막 단계에서 lock file을 만든다.

- 데이터베이스 설정 저장 완료
- 스키마 적용 또는 적용 확인 완료
- 초기 관리자 계정 생성 완료
- 필수 쓰기 디렉터리 검사 완료

중간 단계 실패 시 lock file을 만들지 않는다. 실패한 설치는 운영자가 문제를 고친 뒤
installer를 다시 열어 이어서 처리할 수 있어야 한다.

## 차단 기준

`install.lock`이 존재하면 설치 완료로 판단하고 installer route 접근을 차단한다.
기존 `schema_version` 기반 완료 판단은 fallback으로 유지하지만, lock file이 있으면
데이터베이스 상태보다 lock file을 우선한다.

차단 응답은 HTTP 403과 `installation_already_complete` 오류 코드를 사용한다.

## 삭제 정책

운영 중 lock file을 자동 삭제하지 않는다. 재설치가 필요한 경우에는 운영자가
백업을 확보하고 데이터베이스와 비공개 설정 파일 정리 절차를 별도로 수행한 뒤
수동으로 삭제한다.

업그레이드와 마이그레이션은 installer 재실행이 아니라 관리자 진단 또는 migration
절차로 처리한다.

## 운영 체크리스트

- [ ] `config/`(lock file이 실제로 생성되는 디렉터리)는 document root 밖에 있다.
- [ ] PHP 런타임은 `config/`에 lock file을 생성할 수 있다(쓰기 권한).
- [ ] `install.lock`이 있으면 `/install` 계열 route가 HTTP 403으로 차단된다.
- [ ] lock file 삭제는 백업과 재설치 절차 확인 후 수동으로만 수행한다.

## 알려진 이슈 (0688에서 발견, 미해결)

라이브 환경에서 설치 마법사 전체 흐름을 직접 실행해 검증한 결과, 이
lock file 자체와 무관하게 설치 마법사가 최초 관리자 계정을 만들기 전에
스스로를 잠그는 순서 문제를 발견했다: `InstallerRouteGate`는
`install.lock`이 아직 없어도 `schema_version`에 행이 1개라도 있으면 이미
설치가 끝난 것으로 판단해 `/install/*` 전체를 차단한다. 그런데
`/install/schema`가 성공하는 순간 `schema_version`에 행이 생기므로, 바로
다음 단계인 `/install/admin`이 이미 차단되어 있어 관리자 계정을 만들 수
없다 — lock file은 아예 만들어지지도 못한다. 이 문서가 정의한 "차단
기준"(lock file 우선)은 lock file이 실제로 존재할 때만 유효하고, 지금은
lock file이 생기기도 전에 `schema_version` fallback이 먼저 차단해 버리는
셈이다. 코드 수정(완료 판단 기준 재설계, 예: 관리자 계정 존재 여부까지
함께 확인)은 이 문서의 범위를 벗어나 별도 태스크로 남긴다 — 실제 배포
전에 이 문제가 해결됐는지 먼저 확인한다.
