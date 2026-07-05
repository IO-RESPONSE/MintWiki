# 0718 Phase K QA, integration, and deploy package

## Goal

Phase K(0714-0717) 산출물을 통합 점검하고, 새 라우트·자산·UI가 배포 패키지·런북·스모크에 반영되게 한다.

## Phase

Phase K: Delete + audit logging + backup download, 0714+.

## Scope

- php/deployment-package-manifest.json
- php/scripts (smoke)
- docs
- php/tests, tests

## Acceptance Criteria

- 감사 기록·문서 삭제·백업 다운로드·운영 진단(실데이터+export)에 필요한 갱신된 `src/**`와 공개 자산이 배포 매니페스트에 포함되는지 점검·갱신한다.
- 배포 런북에 Phase K 확인 항목을 추가한다: 문서 삭제(로그인 필요·확인·삭제 후 사라짐), `/admin/audit`에 실제 이벤트 표시, `/admin/backup` 다운로드 링크 동작, `/admin/diagnostics`가 실 DB/스키마/캐시/환경 표시 + export 다운로드.
- 라이브/로컬 스모크 스크립트에 Phase K 점검을 보강하되 자격 증명이 없으면 안전하게 skip한다(예: 익명 삭제 POST가 302/403, 백업 다운로드 라우트의 traversal 거부, 진단 export의 민감값 부재).
- 민감정보(FTP/DB/관리자 비밀번호, 백업/진단 export 내 시크릿)는 저장소·로그·응답에 노출되지 않는다.
- php·py 테스트와 QA가 통과한다. 신규 도메인 코드가 계층 규칙(0424: 도메인 모듈이 App/Http import 금지)을 위반하지 않는지 확인한다.

## Out of Scope

- 실제 라이브 배포 실행(자격 증명 보유 운영자 — 평탄 docroot: `php/public/index.php`→`/public_html/index.php`, 새 클래스 추가 시 `php/vendor/composer/` classmap 동반 배포).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

Phase H/I/J 마감 태스크(0695/0702/0713)와 동일 역할. 스모크 패턴은 `smoke-ui-skin.sh`/`live-e2e-smoke-test.sh` 참고. 라이브는 평탄 단일 docroot이며 새 Modules 클래스 추가 시 서버 classmap 갱신이 필수임을 런북에 명시.
