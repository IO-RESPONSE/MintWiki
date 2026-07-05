# 0713 Phase J QA, skin integration, and deploy package

## Goal

Phase J(0704-0712) 산출물을 통합 점검하고, 새 공개 자산(편집 툴바/미리보기/TOC/표/history/discussion CSS·JS)과 갱신된 UI가 배포 패키지·런북·스모크에 빠짐없이 반영되게 한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/deployment-package-manifest.json
- php/scripts (smoke)
- docs
- php/tests, tests

## Acceptance Criteria

- NamuMark 렌더·편집 개선·history·discussion에 필요한 공개 자산(`public/assets/css/**`, `public/assets/js/**`)과 갱신된 `src/**`가 배포 매니페스트에 포함되는지 점검·갱신한다.
- 배포 런북에 Phase J 확인 항목을 추가한다: `/wiki/{title}`가 위키 문법을 HTML로 렌더(굵게/링크/표/제목/TOC), 편집 화면의 요약·미리보기·툴바·문법 도움말, `/wiki/{title}/history` 200, `/wiki/{title}/discussion` 200(스레드/댓글 작성).
- 라이브/로컬 스모크 스크립트에 Phase J 점검을 보강하되 자격 증명이 없으면 안전하게 skip한다(예: 렌더된 문서 HTML에 `<strong>`/`<table>`/TOC 마크업, history·discussion 경로의 200/302/403 응답 형태 확인).
- 민감정보(FTP/DB/관리자 비밀번호)는 저장소에 기록하지 않는다.
- php·py 테스트와 QA가 통과한다. 기존 계층 규칙(0424: 도메인 모듈이 App/Http import 금지)을 Phase J 신규 코드가 위반하지 않는지 확인한다.

## Out of Scope

- 실제 라이브 배포 실행(자격 증명 보유 운영자가 수행 — 중첩 public/ 레이아웃, 형제 디렉터리는 cd 후 직접 mirror).
- 리비전 revert, 댓글 수정/삭제 등 후속 기능.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

Phase H/I의 마감 태스크(0695/0702)와 동일 역할. 스모크 패턴은 `smoke-ui-skin.sh`/`live-e2e-smoke-test.sh` 참고. 이 태스크 완료 후 운영자가 index.php·src·assets 변경분을 iowiki에 재배포한다.
