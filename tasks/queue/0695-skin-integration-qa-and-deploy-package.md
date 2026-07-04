# 0695 Skin integration QA and deployment package update

## Goal

Phase H 스킨(0689-0694)을 통합 점검하고, 스킨 자산(CSS)과 갱신된 UI가 배포 패키지/런북에 반영되도록 매니페스트·문서를 갱신하며, 라이브 스모크 시나리오에 스킨 확인 항목을 보강한다.

## Phase

Phase H: NamuWiki-style Skin, 0689+.

## Scope

- php/deployment-package-manifest.json
- php/scripts (smoke)
- docs
- php/tests

## Acceptance Criteria

- 스킨에 필요한 공개 자산(`public/assets/css/**`)과 갱신된 `src/Ui/**`가 배포 패키지 매니페스트에 포함되는지 점검·갱신한다.
- 배포 런북에 스킨 관련 확인 항목(상단바 노출, 브랜드색 `#008485` 적용, 문서 액션 탭, 반응형)을 추가한다.
- 라이브/로컬 스모크 스크립트에 스킨 확인 항목을 보강하되(예: 홈 HTML에 상단바 마크업과 `--color-brand`/`#008485` 참조 존재), 자격 증명이 없으면 안전하게 skip한다.
- 민감정보(FTP/DB 비밀번호)는 저장소에 기록하지 않는다.
- php·py 테스트와 QA가 통과한다.

## Out of Scope

- 실제 라이브 배포 실행(자격 증명 보유 운영자가 수행).
- NamuMark 문법 렌더링(후속 Phase).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `php/deployment-package-manifest.json`, `php/scripts/live-http-smoke-test.sh`/`smoke-ui-*.sh`. 실제 배포(FTP 업로드 + 변경 자산 반영)는 운영자가 수행한다. 이 태스크는 스킨이 배포 산출물에 빠짐없이 포함되고 스모크로 확인되게 하는 것이 목적이다.
