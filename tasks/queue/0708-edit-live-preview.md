# 0708 Edit live preview

## Goal

편집 화면에서 저장 전에 NamuMark 렌더 결과를 미리 볼 수 있는 미리보기를 제공한다. 0706의 `NamuMarkDocumentRenderer`를 재사용한다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/public/index.php (미리보기 엔드포인트)
- php/src/Ui/DocumentEditorPage.php (미리보기 영역)
- php/public/assets (미리보기 JS, 점진적 향상)
- php/tests

## Acceptance Criteria

- 서버측 미리보기 경로 `POST /wiki/{title}/preview`(또는 `/preview`)를 등록한다 — 폼의 source를 받아 `NamuMarkDocumentRenderer`로 렌더한 HTML 조각을 반환한다. CSRF 토큰을 검증한다.
- **점진적 향상**: JS 없이도 "미리보기" 제출로 렌더 결과가 편집 화면에 표시되고(원문 유지), JS가 있으면 비동기로 미리보기 영역을 갱신한다(assets/js). JS 실패 시에도 편집·저장은 정상 동작.
- 미리보기 렌더는 문서 보기(0706)와 **동일한 렌더러**를 써서 결과가 일치한다. XSS 안전.
- 미리보기 요청 처리는 ACL edit 권한을 요구한다(익명 정책은 기존 edit 라우트와 동일하게).
- php 테스트로 (1) 미리보기 엔드포인트가 렌더된 HTML 반환, (2) CSRF 누락/불일치 거부, (3) 편집 화면에 미리보기 영역 존재를 검증한다.

## Out of Scope

- 실시간 타이핑 디바운스 등 고급 UX 최적화.
- 위지윅 편집기.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

0706의 렌더러에 의존. 미리보기와 본문 렌더가 갈라지지 않도록 렌더러 인스턴스/서비스를 공유. assets/js는 인라인 최소 스크립트로도 충분(외부 의존 금지 — 배포는 self-contained).
