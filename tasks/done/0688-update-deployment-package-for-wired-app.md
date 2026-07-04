# 0688 Update deployment package and runbook for wired app

## Goal

wiring 완료된 앱을 공유호스팅에 배포하기 위한 패키지 매니페스트와 배포 런북을 갱신하고, 라이브 smoke 시나리오를 실사용 흐름으로 보강한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/deployment-package-manifest.json
- docs
- php/scripts
- tests

## Acceptance Criteria

- `deployment-package-manifest.json`이 wiring된 런타임에 필요한 것(공개 `public/**`, 비공개 `src/**`·`vendor/**`·`config`·`db/schema/**`)을 포함하는지 점검·갱신한다.
- 배포 런북 문서를 갱신한다: FTP 업로드(공개=docroot, 비공개=형제 디렉터리), 설치 마법사 접속(`/install`) 절차, config 파일 위치/권한, installer lock 확인.
- 라이브 smoke 시나리오(0672 산출물)를 설치 마법사 → 로그인 → 문서 생성/편집/조회 → 권한 확인까지 커버하도록 보강하되, 자격 증명이 없으면 안전하게 skip한다(러너에서 실패하지 않도록).
- 민감정보(FTP/DB 비밀번호)는 저장소에 기록하지 않고 실행 시 환경변수/임시 파일로만 받는다.
- php/py 테스트와 QA가 통과한다.

## Out of Scope

- 실제 라이브 배포 실행(자격 증명이 있는 운영자가 별도로 수행).
- 부하/침투 테스트.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 도구: `php/scripts/ftp-deploy.sh`(FTP 업로드, index.php 자동 백업, `--private-map`으로 비공개 디렉터리 배치). 실제 배포는 자격 증명을 가진 운영자가 `ftp-deploy.sh` + 브라우저 설치 마법사로 수행한다. 서버 DB는 localhost 전용이므로 스키마 적용은 업로드된 설치 마법사가 서버 내부에서 수행한다.
