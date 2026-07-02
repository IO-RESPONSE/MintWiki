# UI micro job prompts 0351-0420

이 문서는 0351번 이후 화면 개발 러너 큐에 넣을 마이크로 잡 프롬프트 초안이다.
`tasks/` 디렉터리는 러너가 전담하므로, 실제 큐 파일 생성은 러너 운영자가 수행한다.

## Phase 1: UI Platform Foundation

### 0351 Add UI package skeleton

## Goal

add UI package skeleton.

## Scope

- src/app/ui
- tests/test_ui_routes.py

## Acceptance Criteria

- `src/app/ui` 패키지가 추가된다.
- UI 전용 렌더링 헬퍼의 최소 공개 API가 정의된다.
- 기존 API 라우트 동작은 변경하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 실제 화면 디자인 구현.
- 문서 조회/작성 워크플로우 구현.
- 새로운 프론트엔드 빌드 도구 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

FastAPI 어댑터와 UI 렌더링 헬퍼를 분리한다.

### 0352 Add static asset mount

## Goal

add static asset mount.

## Scope

- src/app/main.py
- src/app/static
- tests/test_ui_routes.py

## Acceptance Criteria

- `/static` 경로가 앱에 등록된다.
- 정적 CSS 파일을 응답할 수 있다.
- 정적 파일 라우트 등록 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- CSS 디자인 토큰 전체 구현.
- JavaScript 번들러 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

의존성을 늘리지 말고 FastAPI/Starlette 기본 정적 파일 기능을 사용한다.

### 0353 Add base HTML shell renderer

## Goal

add base HTML shell renderer.

## Scope

- src/app/ui
- tests/test_ui_shell.py

## Acceptance Criteria

- 공통 `<html>`, `<head>`, `<body>` 셸을 렌더링하는 함수가 추가된다.
- 제목, 주요 콘텐츠, 정적 CSS 링크가 포함된다.
- HTML 특수문자 이스케이프 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 템플릿 엔진 도입.
- 화면별 상세 레이아웃 구현.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기에는 표준 라이브러리 기반 렌더링으로 시작하고, 템플릿 엔진 전환은 별도 잡으로 남긴다.

### 0354 Add public home route

## Goal

add public home route.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_ui_routes.py

## Acceptance Criteria

- `GET /`가 HTML 응답을 반환한다.
- 홈 화면에는 MintWiki 브랜드명과 문서 검색 진입점이 있다.
- 응답 Content-Type이 HTML임을 검증한다.
- Existing tests continue to pass.

## Out of Scope

- 실제 검색 API 연동.
- 문서 생성 폼 구현.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

API 문서 경로와 충돌하지 않게 라우트 순서를 유지한다.

### 0355 Add design token stylesheet

## Goal

add design token stylesheet.

## Scope

- src/app/static
- tests/test_static_assets.py

## Acceptance Criteria

- 색상, 간격, 타이포그래피, 포커스 링 토큰이 CSS 변수로 정의된다.
- 라이트 모드 기본값을 제공한다.
- 토큰 파일이 `/static`에서 조회되는 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 다크 모드.
- 컴포넌트별 상세 CSS.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

엔터프라이즈 운영 화면에 맞게 대비와 스캔성을 우선한다.

### 0356 Add app layout primitives

## Goal

add app layout primitives.

## Scope

- src/app/ui
- src/app/static
- tests/test_ui_shell.py

## Acceptance Criteria

- 상단 바, 본문 컨테이너, 보조 패널 영역을 렌더링할 수 있다.
- 모바일 폭에서 단일 컬럼으로 내려가는 CSS가 포함된다.
- 기본 랜드마크(`header`, `main`, `nav`)가 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 각 업무 화면의 구체 기능 구현.
- 사이드바 상태 저장.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

카드는 반복 항목과 명확한 패널에만 사용한다.

### 0357 Add navigation model

## Goal

add navigation model.

## Scope

- src/app/ui
- tests/test_ui_navigation.py

## Acceptance Criteria

- 홈, 최근 변경, 문서 작성, 관리자 링크를 표현하는 순수 Python 모델이 추가된다.
- 현재 경로에 대한 active 상태 계산이 테스트된다.
- 모델은 FastAPI를 import하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 권한별 메뉴 필터링.
- 관리자 화면 구현.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

권한 기반 메뉴는 ACL UI 단계에서 별도 작업한다.

### 0358 Add UI accessibility baseline tests

## Goal

add UI accessibility baseline tests.

## Scope

- tests/test_ui_accessibility.py
- src/app/ui

## Acceptance Criteria

- 홈 HTML에 `lang`, viewport, skip link, main landmark가 있는지 테스트한다.
- 모든 기본 폼 컨트롤에 label 또는 aria-label이 있다.
- Existing tests continue to pass.

## Out of Scope

- 자동 브라우저 기반 접근성 스캐너 도입.
- 모든 향후 화면의 상세 접근성 검수.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기 기준을 테스트로 고정해 후속 화면이 깨뜨리지 못하게 한다.

### 0359 Add UI error page renderer

## Goal

add UI error page renderer.

## Scope

- src/app/ui
- tests/test_ui_error_pages.py

## Acceptance Criteria

- 404와 일반 오류 페이지 렌더링 헬퍼가 추가된다.
- 오류 메시지는 HTML 이스케이프된다.
- 사용자가 홈으로 돌아갈 수 있는 링크가 포함된다.
- Existing tests continue to pass.

## Out of Scope

- FastAPI exception handler 연결.
- 운영 장애 추적 연동.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

핸들러 연결은 별도 잡으로 유지한다.

### 0360 Register UI exception handlers

## Goal

register UI exception handlers.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_ui_error_pages.py

## Acceptance Criteria

- 브라우저 HTML 요청의 404가 UI 오류 페이지를 반환한다.
- API JSON 요청은 기존 JSON 오류 응답을 유지한다.
- HTML/API 분기 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 세부 오류 추적 시스템.
- 관리자 장애 대시보드.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`Accept` 헤더를 기준으로 HTML과 API 응답을 구분한다.

## Phase 2: Document Reader and Editor UX

### 0361 Add document view route

## Goal

add document view route.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- `GET /documents/{title}`가 HTML 응답을 반환한다.
- 존재하지 않는 문서 제목은 생성 안내 상태로 표시한다.
- API 라우트와 충돌하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 문서 본문 렌더링.
- 편집 저장.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

제목 정규화는 기존 document service를 경유한다.

### 0362 Add document read model for UI

## Goal

add document read model for UI.

## Scope

- src/modules/document
- tests/modules/document

## Acceptance Criteria

- UI에 필요한 document title, id, current revision id, source를 담는 읽기 모델이 추가된다.
- 서비스 메서드는 기존 저장소 포트에 의존한다.
- 프레임워크 import 경계 규칙을 지킨다.
- Existing tests continue to pass.

## Out of Scope

- HTML 렌더링.
- 리비전 diff.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

이미 유사 모델이 있으면 중복 생성 대신 테스트를 보강한다.

### 0363 Render current document source

## Goal

render current document source.

## Scope

- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- 현재 리비전 source가 문서 보기 화면에 안전하게 표시된다.
- source가 없으면 빈 문서 상태를 표시한다.
- XSS 문자열 이스케이프 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 위키 문법 HTML 렌더링.
- 편집 폼.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기 독자 화면은 source 표시로 시작하고 렌더러 연결은 후속 잡에서 한다.

### 0364 Add document create page

## Goal

add document create page.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- `GET /documents/new`가 새 문서 작성 HTML을 반환한다.
- 제목과 source 입력 필드가 있다.
- CSRF 정책은 별도 잡으로 남기되 위치를 명시한다.
- Existing tests continue to pass.

## Out of Scope

- POST 저장 처리.
- 리치 텍스트 에디터.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

폼은 서버 렌더링 기반으로 시작한다.

### 0365 Add document create form handler

## Goal

add document create form handler.

## Scope

- src/app/main.py
- src/modules/document/router.py
- tests/test_document_ui.py
- tests/modules/document/test_router.py

## Acceptance Criteria

- HTML 폼 POST로 문서를 생성할 수 있다.
- 생성 성공 시 문서 보기 경로로 redirect한다.
- 중복 제목은 작성 화면에 오류 상태로 표시한다.
- API JSON 생성 동작은 유지된다.
- Existing tests continue to pass.

## Out of Scope

- CSRF 보호.
- 임시 저장.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 API가 `source`를 서비스에 전달하지 않는 경우 이 잡에서 좁게 수정한다.

### 0366 Add document edit page

## Goal

add document edit page.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- `GET /documents/{title}/edit`가 편집 HTML을 반환한다.
- 기존 source가 textarea에 채워진다.
- 없는 문서는 새 문서 작성으로 안내한다.
- Existing tests continue to pass.

## Out of Scope

- 편집 저장.
- 충돌 감지.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

편집 권한 검사는 ACL UI 단계에서 연결한다.

### 0367 Add document edit submit handler

## Goal

add document edit submit handler.

## Scope

- src/app/main.py
- src/modules/revision
- tests/test_document_ui.py
- tests/modules/revision

## Acceptance Criteria

- 편집 폼 POST가 새 리비전을 생성한다.
- 저장 후 문서 보기 화면으로 redirect한다.
- 리비전 author/summary 기본값이 명시적으로 처리된다.
- Existing tests continue to pass.

## Out of Scope

- diff 미리보기.
- 동시 편집 충돌 처리.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

도메인 서비스에 필요한 메서드가 없다면 최소 포트 확장으로 처리한다.

### 0368 Add document history page

## Goal

add document history page.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_history_ui.py

## Acceptance Criteria

- `GET /documents/{title}/history`가 리비전 목록 HTML을 반환한다.
- 리비전 id, 작성자, 요약, 생성 순서가 표시된다.
- 빈 이력 상태가 표시된다.
- Existing tests continue to pass.

## Out of Scope

- diff 화면.
- 되돌리기.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

리비전 날짜 필드가 부족하면 별도 잡으로 추가한다.

### 0369 Add revision diff placeholder page

## Goal

add revision diff placeholder page.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_history_ui.py

## Acceptance Criteria

- `GET /documents/{title}/diff`가 diff 준비 화면을 반환한다.
- from/to revision 파라미터 검증 오류가 표시된다.
- 실제 diff 알고리즘은 호출하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- diff 계산 구현.
- 되돌리기 UX.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

화면 경로와 파라미터 계약만 먼저 고정한다.

### 0370 Add document UI QA checklist

## Goal

add document UI QA checklist.

## Scope

- docs
- tests/test_document_ui.py

## Acceptance Criteria

- 문서 읽기/작성/편집/이력 화면 QA 체크리스트가 문서화된다.
- 접근성, 모바일, 오류 상태, API 회귀 항목이 포함된다.
- Existing tests continue to pass.

## Out of Scope

- 새로운 기능 구현.
- Playwright 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영자가 수동으로 확인할 항목과 자동화된 항목을 구분한다.

## Phase 3: Enterprise Shell, Auth, and ACL UX

### 0371 Add user session banner model

## Goal

add user session banner model.

## Scope

- src/app/ui
- src/modules/user
- tests/test_ui_session.py

## Acceptance Criteria

- 익명/로그인 사용자 표시 모델이 추가된다.
- UI 모델은 세션 도메인 객체를 표시 문자열로 변환한다.
- FastAPI import 없이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 실제 로그인 처리.
- 쿠키 보안 정책 변경.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

사용자 상태는 모든 화면 상단 바에 들어갈 준비만 한다.

### 0372 Add login page shell

## Goal

add login page shell.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_auth_ui.py

## Acceptance Criteria

- `GET /login`이 로그인 HTML을 반환한다.
- 사용자명, 비밀번호, 다음 경로 입력 필드가 있다.
- 접근성 label 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 인증 검증.
- 계정 생성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

인증 실패 메시지 영역을 미리 둔다.

### 0373 Add login submit handler placeholder

## Goal

add login submit handler placeholder.

## Scope

- src/app/main.py
- src/modules/user
- tests/test_auth_ui.py

## Acceptance Criteria

- `POST /login` 경로가 명시적으로 등록된다.
- 아직 실제 인증이 없으면 501 또는 준비 중 상태를 일관되게 반환한다.
- API와 HTML 응답 구분이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 비밀번호 검증.
- 세션 쿠키 발급.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

미완성 보안 기능을 성공처럼 보이게 하지 않는다.

### 0374 Add logout route placeholder

## Goal

add logout route placeholder.

## Scope

- src/app/main.py
- tests/test_auth_ui.py

## Acceptance Criteria

- `POST /logout` 경로가 등록된다.
- 세션이 없어도 홈으로 redirect한다.
- 향후 세션 삭제 위치가 명시된다.
- Existing tests continue to pass.

## Out of Scope

- 실제 세션 저장소 삭제.
- 모든 화면에 로그아웃 버튼 배치.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

HTTP 메서드는 POST만 허용한다.

### 0375 Add permission denied page

## Goal

add permission denied page.

## Scope

- src/app/ui
- tests/test_acl_ui.py

## Acceptance Criteria

- 읽기/편집/관리 권한 거부 상태를 렌더링할 수 있다.
- 권한명과 대상 문서 제목은 이스케이프된다.
- 사용자가 로그인 또는 홈으로 이동할 수 있다.
- Existing tests continue to pass.

## Out of Scope

- 실제 ACL 검사 연결.
- 권한 변경 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

ACL 도메인 결정 객체를 표시 모델로 변환하는 형태를 준비한다.

### 0376 Add ACL guard adapter for UI routes

## Goal

add ACL guard adapter for UI routes.

## Scope

- src/app
- src/modules/acl
- tests/test_acl_ui.py

## Acceptance Criteria

- UI 라우트에서 ACL 결정을 호출할 수 있는 어댑터가 추가된다.
- 허용/거부 분기가 테스트된다.
- 도메인 ACL 계층은 FastAPI를 import하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 모든 UI 라우트에 ACL 적용.
- 관리자 권한 편집 화면.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

HTTP 의존성은 앱 계층에만 둔다.

### 0377 Apply read permission to document view

## Goal

apply read permission to document view.

## Scope

- src/app/main.py
- tests/test_acl_ui.py

## Acceptance Criteria

- 문서 보기 화면은 read 권한 거부 시 403 HTML을 반환한다.
- 허용 시 기존 문서 보기 동작이 유지된다.
- API 문서 조회 동작은 기존 계약을 유지한다.
- Existing tests continue to pass.

## Out of Scope

- 편집 권한 적용.
- ACL 관리 화면.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

테스트에서는 결정 서비스를 대체할 수 있어야 한다.

### 0378 Apply edit permission to edit routes

## Goal

apply edit permission to edit routes.

## Scope

- src/app/main.py
- tests/test_acl_ui.py

## Acceptance Criteria

- 편집 화면과 편집 제출은 edit 권한을 확인한다.
- 거부 시 source 내용이 저장되지 않는다.
- 거부 HTML과 성공 redirect가 모두 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 편집 잠금.
- abuse 필터 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

권한 검사는 저장 전 가장 이른 지점에서 수행한다.

### 0379 Add CSRF token service interface

## Goal

add CSRF token service interface.

## Scope

- src/app/security
- tests/test_csrf.py

## Acceptance Criteria

- CSRF 토큰 생성/검증 인터페이스가 추가된다.
- 메모리 또는 서명 기반 최소 구현이 테스트된다.
- 토큰 검증 실패가 명확한 예외를 반환한다.
- Existing tests continue to pass.

## Out of Scope

- 모든 폼 적용.
- 외부 보안 라이브러리 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

보안 구현은 단순하더라도 테스트로 계약을 고정한다.

### 0380 Apply CSRF to document forms

## Goal

apply CSRF to document forms.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_csrf.py
- tests/test_document_ui.py

## Acceptance Criteria

- 문서 생성/편집 폼에 CSRF 토큰이 포함된다.
- 잘못된 토큰 제출은 저장하지 않고 오류를 표시한다.
- 정상 토큰 제출은 기존 성공 흐름을 유지한다.
- Existing tests continue to pass.

## Out of Scope

- 로그인 폼 적용.
- 세션 저장소 교체.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

테스트가 안정적으로 토큰을 추출할 수 있게 HTML 구조를 단순하게 유지한다.

## Phase 4: Search, Activity, Discussion, and Admin UX

### 0381 Add search page shell

## Goal

add search page shell.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_search_ui.py

## Acceptance Criteria

- `GET /search`가 검색 HTML을 반환한다.
- 질의 입력, 빈 결과, 준비 중 상태가 렌더링된다.
- 검색 어댑터가 없어도 화면이 실패하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 검색 인덱스 연동.
- 자동완성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

검색 어댑터 연결 전에도 운영자가 경로를 확인할 수 있어야 한다.

### 0382 Add search results view model

## Goal

add search results view model.

## Scope

- src/modules/search
- src/app/ui
- tests/test_search_ui.py

## Acceptance Criteria

- 검색 결과 제목, 스니펫, 점수, URL을 표현하는 표시 모델이 추가된다.
- 스니펫은 HTML 이스케이프된다.
- 빈 결과 문구가 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 실제 검색 백엔드 호출.
- 하이라이트 HTML 허용.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

하이라이트는 XSS 정책이 정해진 뒤 별도 잡에서 처리한다.

### 0383 Add recent changes page shell

## Goal

add recent changes page shell.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_recent_changes_ui.py

## Acceptance Criteria

- `GET /recent-changes`가 HTML 응답을 반환한다.
- 빈 활동 상태와 필터 영역이 표시된다.
- 모바일에서도 테이블이 깨지지 않는 구조를 사용한다.
- Existing tests continue to pass.

## Out of Scope

- 실제 최근 변경 데이터 조회.
- 무한 스크롤.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영형 화면이므로 조밀하고 스캔 가능한 리스트를 우선한다.

### 0384 Add recent changes view model

## Goal

add recent changes view model.

## Scope

- src/app/ui
- src/modules/revision
- tests/test_recent_changes_ui.py

## Acceptance Criteria

- 변경 항목의 문서명, 사용자, 요약, 시간, 작업 유형 표시 모델이 추가된다.
- 긴 제목과 긴 요약이 안전하게 렌더링된다.
- Existing tests continue to pass.

## Out of Scope

- DB 조회 쿼리 구현.
- 필터 저장.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

시간 포맷은 KST 고정이 아니라 앱 설정 기반으로 확장 가능하게 둔다.

### 0385 Add discussion thread UI route

## Goal

add discussion thread UI route.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_discussion_ui.py

## Acceptance Criteria

- `GET /documents/{title}/discussion`이 토론 HTML을 반환한다.
- 스레드 없음 상태가 표시된다.
- 문서 보기에서 토론 링크를 노출한다.
- Existing tests continue to pass.

## Out of Scope

- 댓글 작성.
- 토론 상태 변경.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

토론 도메인 API가 아직 부족하면 읽기 전용 셸로 제한한다.

### 0386 Add discussion comment form shell

## Goal

add discussion comment form shell.

## Scope

- src/app/ui
- tests/test_discussion_ui.py

## Acceptance Criteria

- 토론 화면에 댓글 작성 폼이 표시된다.
- 로그인 필요/권한 없음 상태를 표시할 수 있다.
- 댓글 본문 textarea label이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 댓글 저장.
- abuse 검사 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

폼 제출 경로는 후속 잡에서 연결한다.

### 0387 Add admin dashboard shell

## Goal

add admin dashboard shell.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_admin_ui.py

## Acceptance Criteria

- `GET /admin`이 관리자 대시보드 HTML을 반환한다.
- 시스템 상태, 신고, 보호, 차단 진입점이 표시된다.
- 관리자 권한 거부 상태가 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 실제 관리자 작업 실행.
- 차트 라이브러리 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

관리 화면은 장식보다 조밀한 정보 구조를 우선한다.

### 0388 Add admin report list page

## Goal

add admin report list page.

## Scope

- src/app/main.py
- src/app/ui
- src/modules/admin
- tests/test_admin_ui.py

## Acceptance Criteria

- `GET /admin/reports`가 신고 목록 HTML을 반환한다.
- 빈 상태, 우선순위, 상태 배지가 표시된다.
- 관리자 권한 없이는 403 HTML을 반환한다.
- Existing tests continue to pass.

## Out of Scope

- 신고 처리 액션.
- 알림 발송.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 admin report 모델이 있으면 표시 모델로 변환한다.

### 0389 Add admin block user page shell

## Goal

add admin block user page shell.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_admin_ui.py

## Acceptance Criteria

- `GET /admin/blocks/new`가 차단 작성 HTML을 반환한다.
- 대상, 기간, 사유 필드가 있다.
- 위험 작업임을 나타내는 확인 영역이 있다.
- Existing tests continue to pass.

## Out of Scope

- 차단 저장.
- 감사 이벤트 기록.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

위험 액션은 버튼 문구와 오류 상태를 명확히 둔다.

### 0390 Add audit log viewer shell

## Goal

add audit log viewer shell.

## Scope

- src/app/main.py
- src/app/ui
- src/modules/audit
- tests/test_audit_ui.py

## Acceptance Criteria

- `GET /admin/audit`가 감사 로그 HTML을 반환한다.
- 이벤트 타입, 행위자, 대상, 시간 필터 영역이 있다.
- 감사 로그가 없을 때 빈 상태를 표시한다.
- Existing tests continue to pass.

## Out of Scope

- 로그 내보내기.
- 실시간 스트리밍.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

감사 화면은 운영 증적이므로 행 단위 스캔성을 우선한다.

## Phase 5: Enterprise Hardening

### 0391 Add UI security headers middleware

## Goal

add UI security headers middleware.

## Scope

- src/app/main.py
- src/app/security
- tests/test_security_headers.py

## Acceptance Criteria

- HTML 응답에 기본 보안 헤더가 추가된다.
- API JSON 응답의 기존 계약을 깨지 않는다.
- CSP는 현재 정적 자산 구조와 맞게 최소 허용으로 시작한다.
- Existing tests continue to pass.

## Out of Scope

- nonce 기반 CSP.
- 외부 CDN 허용.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기 CSP는 인라인 스크립트를 피하는 방향으로 후속 잡을 만든다.

### 0392 Extract inline UI scripts to static files

## Goal

extract inline UI scripts to static files.

## Scope

- src/app/static
- src/app/ui
- tests/test_static_assets.py

## Acceptance Criteria

- UI JavaScript가 정적 파일로 분리된다.
- HTML 셸은 script src만 포함한다.
- CSP에서 inline script가 필요 없도록 테스트한다.
- Existing tests continue to pass.

## Out of Scope

- 번들러 도입.
- 프레임워크 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기 UI는 서버 렌더링과 작은 정적 스크립트 조합으로 유지한다.

### 0393 Add form validation error summary

## Goal

add form validation error summary.

## Scope

- src/app/ui
- tests/test_ui_forms.py

## Acceptance Criteria

- 폼 오류 요약 컴포넌트가 추가된다.
- 필드별 오류와 전체 오류를 표시할 수 있다.
- 오류 요약은 접근 가능한 role/aria 속성을 포함한다.
- Existing tests continue to pass.

## Out of Scope

- 모든 폼 적용.
- 클라이언트 검증 라이브러리 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

서버 검증 오류를 일관된 화면으로 보여주기 위한 기반이다.

### 0394 Apply validation summary to document forms

## Goal

apply validation summary to document forms.

## Scope

- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- 문서 생성/편집 폼 오류가 공통 오류 요약으로 표시된다.
- 제목 누락, 중복 제목, CSRF 실패가 구분된다.
- 정상 저장 흐름은 유지된다.
- Existing tests continue to pass.

## Out of Scope

- 로그인/관리자 폼 적용.
- 클라이언트 실시간 검증.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

오류 메시지는 운영자가 원인을 바로 알 수 있게 구체적으로 둔다.

### 0395 Add UI pagination component

## Goal

add UI pagination component.

## Scope

- src/app/ui
- tests/test_ui_pagination.py

## Acceptance Criteria

- 이전/다음/현재 페이지 정보를 렌더링하는 컴포넌트가 추가된다.
- 잘못된 페이지 값은 안전하게 정규화된다.
- 링크 URL 생성이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 각 목록 화면 적용.
- 무한 스크롤.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

검색, 최근 변경, 감사 로그에서 재사용한다.

### 0396 Apply pagination to audit log viewer

## Goal

apply pagination to audit log viewer.

## Scope

- src/app/ui
- tests/test_audit_ui.py

## Acceptance Criteria

- 감사 로그 화면에 공통 pagination이 표시된다.
- page/per_page 파라미터가 보존된다.
- 빈 페이지 상태가 명확하게 표시된다.
- Existing tests continue to pass.

## Out of Scope

- DB 쿼리 최적화.
- CSV 내보내기.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

데이터 조회가 아직 없으면 표시 계약만 테스트한다.

### 0397 Add UI empty state component

## Goal

add UI empty state component.

## Scope

- src/app/ui
- tests/test_ui_empty_state.py

## Acceptance Criteria

- 제목, 설명, 선택 액션을 가진 빈 상태 컴포넌트가 추가된다.
- 액션 없는 빈 상태도 렌더링된다.
- HTML 이스케이프 테스트가 추가된다.
- Existing tests continue to pass.

## Out of Scope

- 모든 화면 적용.
- 아이콘 시스템 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영 화면의 빈 상태 문구를 일관되게 유지한다.

### 0398 Apply empty states across primary UI pages

## Goal

apply empty states across primary UI pages.

## Scope

- src/app/ui
- tests/test_document_ui.py
- tests/test_search_ui.py
- tests/test_recent_changes_ui.py

## Acceptance Criteria

- 문서 없음, 검색 결과 없음, 최근 변경 없음 상태가 공통 컴포넌트를 사용한다.
- 각 화면의 주요 액션이 적절히 표시된다.
- Existing tests continue to pass.

## Out of Scope

- 관리자 화면 적용.
- 문구 전체 재작성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

화면별 행동 유도는 짧고 구체적으로 유지한다.

### 0399 Add UI route registration audit test

## Goal

add UI route registration audit test.

## Scope

- tests/test_ui_routes.py

## Acceptance Criteria

- 주요 UI 경로가 앱에 등록되어 있는지 한 테스트에서 점검한다.
- API 경로와 UI 경로 충돌을 감지한다.
- Existing tests continue to pass.

## Out of Scope

- 기능별 상세 응답 테스트.
- 새 라우트 추가.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

라우트 누락 회귀를 빠르게 잡는 안전망이다.

### 0400 Add UI phase QA checklist

## Goal

add UI phase QA checklist.

## Scope

- docs

## Acceptance Criteria

- UI 플랫폼, 문서 UX, 인증/ACL, 관리자 UX, 보안 헤더 체크리스트가 문서화된다.
- 모바일, 접근성, XSS, CSRF, 권한 거부, 오류 상태 검수 항목이 포함된다.
- Existing tests continue to pass.

## Out of Scope

- 새 기능 구현.
- 외부 테스트 도구 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영 배포 전 수동 검수와 자동 검수를 분리해서 적는다.

## Phase 6: Operational Readiness

### 0401 Add UI health diagnostics page

## Goal

add UI health diagnostics page.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_admin_ui.py

## Acceptance Criteria

- `GET /admin/diagnostics`가 운영 진단 HTML을 반환한다.
- 앱 이름, 환경, DB 연결 상태 placeholder가 표시된다.
- 관리자 권한 없이는 접근할 수 없다.
- Existing tests continue to pass.

## Out of Scope

- 실제 외부 서비스 헬스체크.
- 자동 복구 액션.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

민감 정보는 화면에 노출하지 않는다.

### 0402 Add UI request id display

## Goal

add UI request id display.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_ui_observability.py

## Acceptance Criteria

- HTML 응답에 요청 id가 표시 또는 meta로 포함된다.
- 요청 id가 없으면 생성되는 경로가 테스트된다.
- API 응답 헤더와 충돌하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 분산 추적 연동.
- 로그 포맷 변경.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영 문의 시 화면의 요청 id를 로그와 맞출 수 있게 한다.

### 0403 Add UI flash message support

## Goal

add UI flash message support.

## Scope

- src/app/ui
- src/app
- tests/test_ui_flash.py

## Acceptance Criteria

- redirect 후 성공/오류 메시지를 표시할 수 있는 flash 모델이 추가된다.
- 메시지는 HTML 이스케이프된다.
- 세션 저장소가 없으면 쿼리 기반 최소 구현으로 시작한다.
- Existing tests continue to pass.

## Out of Scope

- 영구 알림 센터.
- 실시간 토스트.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

보안상 민감한 내용을 flash에 담지 않는다.

### 0404 Apply flash messages to document create and edit

## Goal

apply flash messages to document create and edit.

## Scope

- src/app/main.py
- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- 문서 생성/편집 성공 후 보기 화면에 성공 메시지가 표시된다.
- 오류 메시지는 폼 화면에 남는다.
- Existing tests continue to pass.

## Out of Scope

- 관리자 액션 flash 적용.
- 클라이언트 토스트 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

redirect 대상 URL에 불필요한 민감 정보를 넣지 않는다.

### 0405 Add responsive table component

## Goal

add responsive table component.

## Scope

- src/app/ui
- src/app/static
- tests/test_ui_table.py

## Acceptance Criteria

- 좁은 화면에서도 깨지지 않는 테이블 컴포넌트가 추가된다.
- 컬럼 헤더와 행 데이터가 이스케이프된다.
- 빈 행 상태가 표시된다.
- Existing tests continue to pass.

## Out of Scope

- 클라이언트 정렬.
- 가상 스크롤.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

감사 로그, 최근 변경, 관리자 목록에서 재사용한다.

### 0406 Apply responsive tables to operational pages

## Goal

apply responsive tables to operational pages.

## Scope

- src/app/ui
- tests/test_recent_changes_ui.py
- tests/test_audit_ui.py
- tests/test_admin_ui.py

## Acceptance Criteria

- 최근 변경, 감사 로그, 신고 목록이 공통 테이블 컴포넌트를 사용한다.
- 각 화면의 주요 컬럼이 유지된다.
- Existing tests continue to pass.

## Out of Scope

- 테이블 정렬/필터 동작 구현.
- 데이터 저장소 변경.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

반복 마크업을 줄이되 화면별 의미는 잃지 않는다.

### 0407 Add UI performance budget documentation

## Goal

add UI performance budget documentation.

## Scope

- docs

## Acceptance Criteria

- 초기 HTML, CSS, JS 크기 예산을 문서화한다.
- 서버 렌더링 응답 시간 목표와 정적 자산 캐싱 원칙이 포함된다.
- Existing tests continue to pass.

## Out of Scope

- 성능 측정 도구 도입.
- 캐시 헤더 구현.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

엔터프라이즈 화면은 무거운 프론트엔드 번들 도입 전에 예산을 먼저 고정한다.

### 0408 Add static asset cache headers

## Goal

add static asset cache headers.

## Scope

- src/app/main.py
- src/app/static
- tests/test_static_assets.py

## Acceptance Criteria

- 정적 자산 응답에 명시적 cache-control 정책이 적용된다.
- HTML 응답은 과도하게 캐시되지 않는다.
- Existing tests continue to pass.

## Out of Scope

- 파일명 해시 빌드.
- CDN 설정.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

해시 없는 자산은 짧은 캐시로 시작한다.

### 0409 Add print stylesheet for document pages

## Goal

add print stylesheet for document pages.

## Scope

- src/app/static
- src/app/ui
- tests/test_static_assets.py

## Acceptance Criteria

- 문서 보기 화면에 인쇄용 CSS가 연결된다.
- 내비게이션과 편집 액션은 인쇄에서 숨겨진다.
- 문서 제목과 본문은 인쇄에 남는다.
- Existing tests continue to pass.

## Out of Scope

- PDF 생성.
- 관리자 화면 인쇄 지원.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영 문서 출력 요구를 위한 최소 기반이다.

### 0410 Add UI internationalization placeholders

## Goal

add UI internationalization placeholders.

## Scope

- src/app/ui
- tests/test_ui_i18n.py

## Acceptance Criteria

- UI 문자열을 키 기반으로 조회할 수 있는 최소 헬퍼가 추가된다.
- 기본 locale은 ko로 동작한다.
- 누락 키 처리 정책이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 다국어 번역 파일 전체 작성.
- 사용자별 locale 저장.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

초기에는 한국어 운영 화면을 기준으로 하되 확장 지점을 둔다.

### 0411 Add UI component snapshot fixtures

## Goal

add UI component snapshot fixtures.

## Scope

- tests/ui_fixtures
- tests/test_ui_snapshots.py

## Acceptance Criteria

- 주요 UI 컴포넌트의 HTML fixture가 추가된다.
- 렌더링 결과가 fixture와 일치하는 테스트가 추가된다.
- 동적 값은 안정적으로 정규화된다.
- Existing tests continue to pass.

## Out of Scope

- 브라우저 스크린샷 테스트.
- 모든 화면 snapshot화.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

시각 회귀 이전 단계로 서버 렌더링 HTML 계약을 고정한다.

### 0412 Add Playwright evaluation plan

## Goal

add Playwright evaluation plan.

## Scope

- docs

## Acceptance Criteria

- Playwright 도입 기준, 테스트 대상, CI 비용, 대체안을 문서화한다.
- 현재 단계에서는 의존성을 추가하지 않는다.
- Existing tests continue to pass.

## Out of Scope

- Playwright 설치.
- 브라우저 테스트 작성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

브라우저 테스트 도입은 의사결정 문서 이후 별도 잡으로 처리한다.

### 0413 Add UI build/no-build decision record

## Goal

add UI build no-build decision record.

## Scope

- docs

## Acceptance Criteria

- 서버 렌더링 + 정적 CSS/JS로 시작하는 결정 이유가 문서화된다.
- SPA/React/Vue 도입 시점 기준이 포함된다.
- Existing tests continue to pass.

## Out of Scope

- 프론트엔드 프레임워크 도입.
- 빌드 파이프라인 작성.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

엔터프라이즈급은 무거운 도구보다 운영 기준과 경계가 먼저다.

### 0414 Add UI dependency boundary check

## Goal

add UI dependency boundary check.

## Scope

- scripts/check_boundaries.py
- tests

## Acceptance Criteria

- UI 렌더링 계층과 도메인 계층의 import 경계가 검사된다.
- 도메인 모듈이 app UI 계층을 import하면 실패한다.
- 기존 경계 검사와 함께 실행된다.
- Existing tests continue to pass.

## Out of Scope

- 전체 아키텍처 재작성.
- 외부 린터 도입.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

PHP 전환 가능성을 해치지 않게 UI 의존성을 위쪽 계층에만 둔다.

### 0415 Add UI API contract smoke tests

## Goal

add UI API contract smoke tests.

## Scope

- tests/test_ui_api_contract.py

## Acceptance Criteria

- UI가 의존하는 문서 생성/조회/리비전 목록 API 계약을 smoke test로 묶는다.
- UI 변경이 API 응답 필드를 깨뜨리면 실패한다.
- Existing tests continue to pass.

## Out of Scope

- 모든 API 테스트 중복.
- 브라우저 테스트.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

화면과 API 사이의 최소 계약을 문서화하는 테스트다.

### 0416 Add admin dangerous action confirmation component

## Goal

add admin dangerous action confirmation component.

## Scope

- src/app/ui
- tests/test_admin_ui.py

## Acceptance Criteria

- 차단, 보호, 신고 처리 같은 위험 작업용 확인 컴포넌트가 추가된다.
- 대상 이름과 작업명을 명확히 표시한다.
- 확인 문구 입력 여부를 표현할 수 있다.
- Existing tests continue to pass.

## Out of Scope

- 실제 작업 실행.
- JavaScript 확인 모달.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

관리자 실수를 줄이기 위한 서버 렌더링 기반 확인 UI다.

### 0417 Add UI audit event hooks for form actions

## Goal

add UI audit event hooks for form actions.

## Scope

- src/app
- src/modules/audit
- tests/test_audit_ui.py

## Acceptance Criteria

- 문서 생성/편집과 관리자 폼 제출 시 감사 이벤트 기록 hook 위치가 생긴다.
- 실제 저장소가 없으면 no-op 구현으로 계약을 고정한다.
- 실패 시 사용자 작업 자체를 깨뜨리지 않는 정책이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 완전한 감사 저장소 구현.
- 모든 이벤트 타입 정의.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

감사 실패가 사용자 요청 실패로 번지는지 정책을 명확히 한다.

### 0418 Add UI loading and disabled button states

## Goal

add UI loading and disabled button states.

## Scope

- src/app/static
- src/app/ui
- tests/test_ui_forms.py

## Acceptance Criteria

- 폼 제출 버튼의 disabled/loading 상태 스타일이 정의된다.
- 서버 렌더링 fallback 상태도 표현할 수 있다.
- 접근성 속성이 테스트된다.
- Existing tests continue to pass.

## Out of Scope

- 복잡한 클라이언트 상태 관리.
- 낙관적 업데이트.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

중복 제출 방지는 서버 검증과 함께 후속 잡에서 강화한다.

### 0419 Add duplicate submit protection for document forms

## Goal

add duplicate submit protection for document forms.

## Scope

- src/app
- src/app/ui
- tests/test_document_ui.py

## Acceptance Criteria

- 문서 생성/편집 폼의 중복 제출 방지 토큰 또는 idempotency 키가 추가된다.
- 같은 키 재제출 정책이 테스트된다.
- 정상 첫 제출은 기존 동작을 유지한다.
- Existing tests continue to pass.

## Out of Scope

- 모든 관리자 폼 적용.
- 분산 저장소 기반 idempotency.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

운영 화면에서 새로고침/뒤로가기 재제출 피해를 줄인다.

### 0420 Add enterprise UI readiness summary

## Goal

add enterprise UI readiness summary.

## Scope

- docs

## Acceptance Criteria

- 0351-0419 UI 작업 결과와 남은 위험을 요약한다.
- 보안, 접근성, 운영성, 성능, 모바일, 테스트 커버리지 관점이 포함된다.
- 다음 UI 단계 후보가 정리된다.
- Existing tests continue to pass.

## Out of Scope

- 새 기능 구현.
- 큐 재정렬.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

다음 대규모 UI 단계로 넘어가기 전 의사결정 문서 역할을 한다.
