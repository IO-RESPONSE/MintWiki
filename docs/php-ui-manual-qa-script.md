# PHP UI Manual QA Script

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 수동 QA 스크립트.

이 문서는 PHP UI 계층의 수동 QA를 체계적으로 수행하기 위한 실행 가이드다.
자동 테스트(`scripts/qa.sh`)를 통과한 뒤, 브라우저에서 직접 UI를 검증할 때 사용한다.

특히 **홈/문서/관리자/모바일/오류 상태** 에 대한 수동 확인 항목을 제공한다.
자세한 QA 기준은 `docs/php-ui-phase-qa-checklist.md` 를 참조한다.

## 전제 조건

- `php` CLI 설치 (PHP 8.1+)
- 최근 `composer install` 실행 (php/vendor/ 디렉터리 존재)
- `scripts/test.sh` 및 `scripts/qa.sh` 통과
- 모던 브라우저 (Chrome, Firefox, Safari, Edge)

## 초기 설정

### 1단계: 자동 QA 실행

```bash
cd /root/wiki-engine-blueprint
php/scripts/qa.sh
```

모든 자동 검사가 통과해야 다음 단계로 진행한다. 실패 시 로그를 확인하고 수정.

### 2단계: 로컬 서버 시작

```bash
cd /root/wiki-engine-blueprint
php -S 127.0.0.1:8000 -t php/public &
# 또는 별도 터미널에서
php -S 127.0.0.1:8000 -t php/public
```

### 3단계: 브라우저에서 확인

```
http://127.0.0.1:8000
```

모든 아래 항목을 차례로 확인한다.

## 1. 홈 페이지 (Home)

### 1.1 페이지 로드

- [ ] `http://127.0.0.1:8000/` 접속 성공
- [ ] 200 OK 상태 (브라우저 DevTools Network 탭 확인)
- [ ] HTML 완전히 로드됨 (스타일 적용, 레이아웃 깨지지 않음)

### 1.2 레이아웃 및 네비게이션

- [ ] `<header>`, `<nav>`, `<main>`, `<footer>` 모두 시각적으로 보임
- [ ] 헤더에 사이트 제목 또는 로고 표시
- [ ] 네비게이션 메뉴가 보기 좋게 배치
- [ ] 모바일 기기/작은 화면에서 네비게이션이 축소되거나 드롭다운 형태로 변함

### 1.3 접근성

- [ ] 페이지 소스 확인: `<html lang="ko">` 속성 있음 (DevTools → 우클릭 검사)
- [ ] `<meta name="viewport">` 존재 확인
- [ ] 모든 링크/버튼을 Tab 키로 순회 가능
- [ ] 페이지 제목(`<title>`)이 "MintWiki" 또는 유사한 이름

### 1.4 시각 디자인

- [ ] 글씨 크기 및 색상이 읽기 좋음 (너무 작거나 대비가 약하지 않음)
- [ ] 배경색과 텍스트 색상이 명도 대비 4.5:1 이상 (참고: 큼지막한 텍스트는 3:1)

---

## 2. 문서 페이지 (Documents)

문서 CRUD 관련 페이지들. 실제 문서 데이터가 없으면 placeholder/empty state를 확인.

### 2.1 문서 목록 / 검색 결과

- [ ] `/search` 또는 `/recent` 페이지 로드 성공 (리다이렉트되거나 placeholder 표시)
- [ ] 비어 있거나 예제 결과가 테이블/리스트로 표시
- [ ] 각 항목이 링크 형태 (문서 제목이 클릭 가능)
- [ ] 페이지네이션(있으면) 버튼이 클릭 가능 (또는 비활성화 상태 명확)

### 2.2 문서 보기

- [ ] `/document/example` 또는 placeholder 문서 접속 가능
- [ ] 문서 제목이 `<h1>` 태그로 렌더링
- [ ] 문서 내용이 보이거나, "문서 없음" 등 명확한 empty state 표시
- [ ] "편집", "이력", "토론" 등의 버튼/링크가 보임 (상태에 따라 disabled 가능)
- [ ] 문서 생성자, 최종 수정일 등의 메타데이터가 표시되거나 숨겨짐 (일관성 확인)

### 2.3 문서 생성 폼

- [ ] `/document/create` 페이지 로드 성공
- [ ] 폼 필드(제목, 내용 등)가 `<label>` 으로 명시적으로 레이블됨 (DevTools 검사)
- [ ] 각 필드에 `<input>` 또는 `<textarea>` 요소 확인
- [ ] 제출 버튼이 `<button type="submit">` 형태
- [ ] 폼에 hidden input으로 CSRF token이 있음 (소스 보기에서 `name="csrf_token"` 확인)

### 2.4 폼 오류 처리

- [ ] 폼을 비운 상태로 제출하면, 오류 메시지가 `<div role="alert">` 로 감싸여 나타남
- [ ] 오류 메시지가 폼 위에 먼저 표시 (스크린 리더 사용자가 먼저 알게 됨)
- [ ] 각 오류 메시지가 해당 필드로의 링크(`#field-id`) 포함
- [ ] 오류 필드가 시각적으로 구분됨 (빨간 테두리, 아이콘, 배경색 등)

### 2.5 문서 수정 폼

- [ ] `/document/edit` 페이지에서 기존 값이 폼 필드에 유지됨 (있으면)
- [ ] "저장" 버튼이 disabled 상태로 시작하거나, 클릭 후 로딩 상태로 변함
- [ ] 중복 클릭 방지: 버튼을 빠르게 여러 번 클릭해도 한 번의 제출로만 처리

---

## 3. 관리자 페이지 (Admin)

관리자 기능. 권한 없음 상태도 확인.

### 3.1 관리자 대시보드

- [ ] `/admin` 페이지 로드 성공 (또는 로그인 필요 상태 표시)
- [ ] 시스템 상태, 통계 등이 표시되거나 placeholder 표시
- [ ] 부분 메뉴(감사 로그, 사용자 관리, 보고서 등)가 보임

### 3.2 감사 로그 뷰어

- [ ] `/admin/audit` 페이지 로드 성공
- [ ] 감사 로그가 테이블로 표시 (또는 비어 있음)
  - 행(row): 이벤트 시간, 사용자명, 액션, 세부 정보
  - `<table>`, `<thead>`, `<tbody>` 마크업 확인
- [ ] 각 열(column) 헤더가 명확
- [ ] 사용자명, 문서 제목 등이 HTML escape되어 출력 (검사: `<`, `>`, `&` 등이 escape 문자로 표시)
  - 예: `<script>alert('xss')</script>` → `&lt;script&gt;...` 형태

### 3.3 사용자 차단 폼

- [ ] `/admin/block-user` 또는 유사 페이지 로드
- [ ] 사용자 선택 필드, 사유 필드 등이 있음
- [ ] CSRF token 확인
- [ ] 제출 후 성공/오류 메시지 표시 (flash message)

### 3.4 권한 없음 상태

- [ ] 로그인하지 않은 상태에서 `/admin` 접속 시:
  - 로그인 페이지로 리다이렉트, 또는
  - "권한이 없습니다" 페이지(403) 표시
- [ ] 인증된 사용자가 일반 사용자인 경우 관리자 페이지 접근 거부

---

## 4. 모바일 및 반응형 (Mobile & Responsive)

다양한 화면 크기에서의 표현.

### 4.1 모바일 뷰포트

브라우저 DevTools에서 Device Emulation 실행 (`Ctrl+Shift+M` 또는 메뉴 → Device Toolbar):

- [ ] iPhone 12 (390×844px) 에서 모든 페이지 정상 표시
- [ ] Galaxy S21 (360×720px) 에서 모든 페이지 정상 표시
- [ ] iPad (768×1024px) 에서 모든 페이지 정상 표시
- [ ] 텍스트가 가독성 있게 자동으로 reflowed (과도하게 줄바꿈되지 않음)
- [ ] 버튼/링크가 터치하기 충분한 크기 (최소 44×44px 권장)

### 4.2 모바일 네비게이션

- [ ] 작은 화면에서 네비게이션 메뉴가 숨겨지거나 축소됨
- [ ] 모바일 메뉴 토글 버튼(≡ 또는 유사)이 보이고 클릭 가능
- [ ] 메뉴 토글 후 전체 네비게이션이 표시 (modal, 사이드바, dropdown 등 형식 무관)

### 4.3 폼 입력

- [ ] 폼 필드(`<input>`, `<textarea>`)에 터치/탭 시 확대되거나 키보드가 뜸 (정상)
- [ ] 텍스트 입력 후 제출이 가능
- [ ] 테이블이 있으면 수평 스크롤이 가능하거나 반응형으로 재구성됨

### 4.4 이미지 및 자산

- [ ] 로고, 아이콘 등이 모바일에서도 선명하게 표시
- [ ] 이미지가 텍스트를 가리지 않음

---

## 5. 오류 상태 (Error States)

예상치 못한 상황 또는 유효하지 않은 입력 처리.

### 5.1 404 Not Found

- [ ] `/document/nonexistent` 또는 존재하지 않는 페이지 접속
- [ ] 404 상태 코드 반환 (DevTools Network)
- [ ] "문서를 찾을 수 없습니다" 또는 유사 메시지 표시
- [ ] 홈으로 돌아가기, 검색하기 등의 복구 링크 제공

### 5.2 403 Forbidden / Permission Denied

- [ ] 권한이 없는 문서/페이지에 접속 시 명확한 오류 페이지 표시
- [ ] "이 문서에 접근할 권한이 없습니다" 메시지
- [ ] 홈 또는 로그인으로 이동하는 링크

### 5.3 폼 유효성 오류

- [ ] 필수 필드를 비우고 제출 시:
  - 오류 요약이 `<div role="alert">` 로 페이지 상단에 표시
  - 각 오류가 해당 필드와 연결됨 (anchor link)
  - 필드 옆에 시각적 표시 (빨간색 테두리, 아이콘 등)
- [ ] 오류 메시지가 명확하고 구체적 ("필수 필드입니다", "유효한 이메일이 아닙니다" 등)

### 5.4 XSS 시도 차단

**주의:** 실제로 공격을 시도하지 않고, 코드 리뷰 및 자동 테스트로 확인.

- [ ] 문서 제목에 `<script>alert('xss')</script>` 같은 payload를 입력하려 해도, 자동 테스트에서 escape 확인
- [ ] `php/tests/Ui/HtmlEscapingTest.php` 또는 `php/tests/Ui/UiFieldXssRegressionTest.php` 실행
- [ ] 모든 테스트 통과 확인

### 5.5 CSRF 공격 차단

- [ ] 폼에 CSRF token이 hidden input으로 포함됨 (소스 보기)
- [ ] Token이 제출 시 검증됨 (자동 테스트: `php/tests/UI/FormCsrfTest.php`)

### 5.6 서버 오류 (5xx)

- [ ] 의도적으로 서버 오류를 유발하거나, PHP 에러가 있으면:
  - 사용자에게 노출되는 메시지는 "오류가 발생했습니다" 정도로 일반적
  - 상세 오류(stack trace, SQL query 등)는 노출되지 않음
  - 로그에만 기록됨 (php error log 확인)

---

## 6. 보안 헤더 및 성능 검증

### 6.1 HTTP 보안 헤더

DevTools → Network → 임의 요청 선택 → Response Headers 확인:

- [ ] `X-Content-Type-Options: nosniff` 있음
- [ ] `X-Frame-Options: DENY` 또는 `SAMEORIGIN` 있음
- [ ] `X-XSS-Protection: 1; mode=block` 있음 (구식 브라우저 대응)

### 6.2 Cache 헤더

- [ ] HTML 페이지: `Cache-Control: no-store, no-cache` 또는 `no-cache`
- [ ] CSS/JS (버전/해시 포함): `Cache-Control: public, max-age=31536000`
- [ ] 이미지: `Cache-Control: public, max-age=31536000` 또는 `public, max-age=3600`

### 6.3 성능 지표

DevTools → Lighthouse 또는 Performance 탭:

- [ ] First Contentful Paint (FCP) < 1.5초 (목표)
- [ ] Largest Contentful Paint (LCP) < 2.5초 (목표)
- [ ] Cumulative Layout Shift (CLS) < 0.1 (목표)
- [ ] 정적 자산(CSS, JS) 총 크기 < 150KB (docs/php-ui-phase-summary.md)

---

## 테스트 시나리오 요약

### 시나리오 1: 신규 방문자 (로그인 전)
```
1. 홈 페이지 접속 → 홈 페이지 섹션 1.1-1.4 확인
2. /document/... 접속 → 문서 페이지 섹션 2.1-2.2 확인
3. 폼 접속 시도 → 권한 없음/로그인 필요 메시지 확인
4. 모바일 뷰에서 반복 → 모바일 섹션 4.1-4.4 확인
```

### 시나리오 2: 인증된 사용자
```
1. 홈/문서 페이지 접속 → 섹션 1, 2 확인
2. 문서 생성 폼 접속 → 섹션 2.3 확인
3. 빈 폼 제출 → 섹션 5.3 오류 확인
4. 유효한 데이터 입력 → 제출 성공 또는 예상된 동작
5. 모바일에서 반복
```

### 시나리오 3: 관리자
```
1. /admin 접속 → 섹션 3.1 확인
2. /admin/audit 접속 → 섹션 3.2 테이블 확인
3. 사용자 차단 폼 접속 → 섹션 3.3 확인
4. XSS escape 검증 → 감사 로그에서 섹션 3.2 escape 확인
```

### 시나리오 4: 오류 상태
```
1. 존재하지 않는 페이지 → 섹션 5.1 404 확인
2. 권한 없는 리소스 → 섹션 5.2 403 확인
3. 폼 제출 오류 → 섹션 5.3 확인
4. 보안 헤더 → 섹션 6.1 확인
```

---

## 진행 추적

수동 QA를 수행할 때 아래 체크리스트를 인쇄하거나 복사하여 항목마다 `[x]` 로 체크.

모든 항목을 완료하면:

```bash
# 최종 검증
scripts/test.sh    # 모든 단위 테스트 통과
scripts/qa.sh      # 모든 QA 검사 통과
```

두 명령이 모두 통과하면 수동 QA 완료.

---

## 참고 문서

- `docs/php-ui-phase-qa-checklist.md` — 자세한 QA 기준 및 자동화 범위
- `docs/php-ui-phase-summary.md` — UI 계층 아키텍처 및 제약 조건
- `docs/php-runtime-security-baseline.md` — 보안 정책
- `php/tests/Ui/` — 각 페이지의 자동 테스트 (참고용)

---

## 트러블슈팅

### 서버 시작 실패 (`Address already in use`)

```bash
# 기존 php 프로세스 종료
lsof -i :8000 | grep php | awk '{print $2}' | xargs kill -9
# 또는 다른 포트 사용
php -S 127.0.0.1:9000 -t php/public
```

### 404 Not Found 모든 페이지

```bash
# php/public/index.php 존재 확인
ls -la php/public/index.php

# .htaccess 설정 확인 (Apache의 경우)
# 또는 PHP 기본 라우팅 활성화 확인
```

### 스타일이 적용되지 않음

```bash
# 정적 자산 경로 확인
ls -la php/public/assets/css/

# 캐시 무시 (DevTools → Network → Disable cache 체크)
# 또는 Ctrl+Shift+R (하드 새로 고침)
```

### 데이터베이스 연결 오류

이는 Phase C (DB) 검증 후 문제. 현재 Phase D 초반이므로 placeholder만 표시되는 것이 정상.

---

**마지막 업데이트: 2026-07-03** (Phase D 진행 중)
