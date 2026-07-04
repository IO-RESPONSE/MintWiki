# Installer Lock File Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

설치 완료 후 installer 재실행을 차단하기 위한 lock file 기준을 정의한다.

## 목적

installer는 데이터베이스 스키마와 관리자 계정 생성이 끝난 뒤 다시 실행되면 안 된다.
완료 상태를 파일로 남겨 shared hosting 환경에서도 다음을 보장한다:

- 설치 완료 후 `/installer` 계열 route 접근을 차단한다.
- 데이터베이스 연결 오류가 일시적으로 발생해도 완료된 설치본을 신규 설치처럼 열지 않는다.
- lock file은 document root 밖의 비공개 저장소에 둔다.

## Lock File 위치

기본 파일명은 `install.lock`이다. 배포에서는 document root 밖의 `storage/installer/`
아래에 둔다.

```text
/home/user/wiki/
├── php/
│   └── public/              # document root
└── storage/
    └── installer/
        └── install.lock
```

`php/public/` 안에는 lock file을 두지 않는다. URL로 직접 내려받을 수 있는 위치에
lock file이 있으면 설치 시각과 운영 상태가 노출될 수 있다.

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

- [ ] `storage/installer/`는 document root 밖에 있다.
- [ ] PHP 런타임은 `storage/installer/`에 lock file을 생성할 수 있다.
- [ ] `install.lock`이 있으면 `/installer` 계열 route가 HTTP 403으로 차단된다.
- [ ] lock file 삭제는 백업과 재설치 절차 확인 후 수동으로만 수행한다.
