# UI Route Parity Matrix

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.

이 문서는 MintWiki 사용자 인터페이스가 노출하는 HTTP 라우트의 Python 구현과 PHP 구현 상태를 비교하는 살아있는 matrix다. 최종적으로 **PHP 라우트가 canonical(정본)이 되며**, Python 라우트는 이에 대응되거나 freeze 상태로 관리된다.

## 배경

Phase D 진입 시점에서 Python 런타임은 JSON API 라우트만 제공하고 있다:
- 문서 조회/생성/검색 API (`/api/documents/*`)
- 리비전 조회 API (`/api/documents/{id}/revisions`)
- 헬스체크 (`/health`)

이와 동시에 PHP 런타임이 서버 렌더링 UI 라우트를 먼저 구현하기 시작했다:
- 홈 페이지 (`GET /`)
- 헬스체크 (`GET /health`)
- 문서 API placeholder 라우트들 (`/api/documents/*` — 아직 501)

이 표는 **두 구현 간 경로 대응**과 **현재 구현 상태**를 한눈에 보여주는 것을 목표로 한다.

## 정본(Source of Truth)

이 표의 정본은 다음과 같다:

**Python 쪽:**
- `src/app/main.py` — FastAPI 앱 설정과 라우터 등록
- `src/modules/*/router.py` — 각 모듈별 라우터

**PHP 쪽:**
- `php/public/index.php` — 프론트 컨트롤러와 경로 등록 현황
- `php/src/Http/` — 라우터, DocumentApiRoutes 등
- `php/tests/Http/*Test.php` — 라우트 등록 및 동작 검증 테스트

## 라우트 상태 정의 (5단계)

- **not-started** — 어느 쪽도 구현되지 않음. 후속 태스크에서 구현할 계획만 있음.
- **placeholder** — PHP 쪽에만 501 Not Implemented 응답을 반환하는 placeholder 라우트가 있음. 서비스/저장소 연결이 없음.
- **python-only** — Python에만 구현되어 있고 PHP 구현은 없음. Phase D/E 동안 API 라우트로 사용 가능.
- **parity** — Python과 PHP 모두에 대응하는 라우트가 있고, 같은 기능을 제공함.
- **canonical-php** — PHP 구현이 canonical(정본)으로 결정되었으며, 이를 최종 배포 경로로 삼는 상태.

단계의 의미:
- `not-started` < `placeholder` < `python-only` < `parity` < `canonical-php`

## UI와 API 라우트의 구분

**UI 라우트 (서버 렌더링 HTML):**
- `GET /` — 홈 페이지
- `GET /documents` — 문서 목록 페이지
- `GET /documents/{id}` — 문서 읽기 페이지
- `GET /documents/{id}/edit` — 문서 편집 페이지
- `GET /documents/{id}/history` — 문서 이력 페이지
- 기타 UI: admin, auth, search 등

**API 라우트 (JSON 응답):**
- `GET /api/documents` — 문서 목록 조회
- `POST /api/documents` — 문서 생성
- `GET /api/documents/by-title` — 제목으로 문서 조회
- `GET /api/documents/{id}` — ID로 문서 조회
- `GET /api/documents/{id}/revisions` — 리비전 목록
- 기타 API: admin, auth, search 등

**인프라 라우트 (모니터링/진단):**
- `GET /health` — 헬스체크

## 라우트 parity matrix

### 인프라 라우트

| 라우트 | Python | PHP | 상태 | 근거/계획 |
|---|---|---|---|---|
| GET /health | ✓ (JSON) | ✓ (JSON) | parity | 앱 이름과 상태를 반환. 두 구현 모두 동일한 계약 |

### UI 라우트 (서버 렌더링)

| 라우트 | 용도 | Python | PHP | 상태 | 근거/계획 |
|---|---|---|---|---|---|
| GET / | 홈/검색 진입점 | ✗ | ✓ | placeholder | PHP 0526에서 구현. Python은 SPA 기반 설계라 UI 미구현 |
| GET /documents | 문서 목록 | ✗ | ✗ | not-started | 0563 이후 PHP에서 구현 예정 |
| GET /documents/{id} | 문서 읽기 | ✗ | ✗ | not-started | 0563 이후 PHP에서 구현 예정 (view flow) |
| GET /documents/{id}/edit | 문서 편집 폼 | ✗ | ✗ | not-started | 0563 이후 PHP에서 구현 예정 (edit flow) |
| GET /documents/{id}/history | 문서 이력 | ✗ | ✗ | not-started | 0563 이후 PHP에서 구현 예정 (history flow) |
| POST /documents | 문서 저장 | ✗ | ✗ | not-started | 0563 이후 PHP에서 구현 예정 (create/update submission) |
| GET /admin | 관리자 대시보드 | ✗ | ✗ | not-started | 0564에서 PHP route 등록 테스트만 추가 |
| GET /auth/login | 로그인 폼 | ✗ | ✗ | not-started | 0565에서 PHP placeholder route 예정 |
| POST /auth/login | 로그인 제출 | ✗ | ✗ | not-started | 0565에서 PHP placeholder route 예정 |
| GET /auth/logout | 로그아웃 | ✗ | ✗ | not-started | 0565에서 PHP placeholder route 예정 |
| GET /search | 검색 결과 | ✗ | ✗ | not-started | 후속 태스크에서 구현 |
| GET /sitemap | 사이트맵 | ✗ | ✗ | not-started | 0596에서 PHP placeholder route 예정 |

### API 라우트 (문서)

| 라우트 | Python | PHP | 상태 | 근거/계획 |
|---|---|---|---|---|
| GET /api/documents | ✓ (목록 미구현) | ✓ | placeholder | Python은 TODO 상태. PHP는 0420에서 501 placeholder 등록 |
| POST /api/documents | ✓ | ✓ | placeholder | Python은 구현됨. PHP는 0420에서 501 placeholder 등록 |
| GET /api/documents/by-title | ✓ | ✓ | placeholder | Python은 구현됨. PHP는 0420에서 501 placeholder 등록 |
| GET /api/documents/{id} | ✓ | ✗ | python-only | Python은 구현됨. PHP는 동적 세그먼트 미지원(0397) |
| GET /api/documents/{id}/revisions | ✓ | ✗ | python-only | Python은 구현됨. PHP는 동적 세그먼트 미지원(0397) |

### API 라우트 (관리/감시)

| 라우트 | 용도 | Python | PHP | 상태 | 근거/계획 |
|---|---|---|---|---|---|
| GET /api/admin/* | 관리자 API | ✗ | ✗ | not-started | 아직 설계되지 않음 |
| GET /api/audit/* | 감시 API | ✗ | ✗ | not-started | 아직 설계되지 않음 |

## 라우트 대응 관계

### Python → PHP 매핑

현재 Python 라우트는 대부분 JSON API를 기반으로 하고 있다. PHP는 이들을 다음과 같이 처리한다:

1. **Python API를 그대로 대응** — `/api/documents`, `/api/documents/by-title` 등
   - PHP는 동일 경로를 placeholder(501)로 예약
   - 이후 구현할 때 Python 계약을 따름

2. **UI 라우트는 PHP에서만 구현** — `GET /`, `GET /documents/{id}` 등
   - Python은 UI 미구현 (SPA 기반 설계가 아님)
   - PHP는 서버 렌더링 HTML 제공

3. **동적 세그먼트는 미지원 → 지원 순서**
   - Python의 `GET /api/documents/{id}`, `GET /api/documents/{id}/revisions` 는
     PHP Router(0397)가 동적 세그먼트를 지원하지 않아 아직 미등록
   - Router 업그레이드 후 등록 예정

## Phase D 진행에 따른 갱신 계획

이 표는 다음 태스크들과 함께 갱신된다:

| 태스크 | 내용 | 영향받는 라우트 |
|---|---|---|
| 0526 (완료) | PHP home page route (`GET /`) | `GET /` → placeholder |
| 0562 (현재) | UI route parity matrix (이 문서) | — (matrix 작성만) |
| 0563 | PHP document route integration tests | `GET /documents/{id}`, `POST /documents`, etc. → not-started → parity |
| 0564 | PHP admin route registration tests | `GET /admin/*` → placeholder |
| 0565 | PHP auth route registration tests | `GET /auth/login`, `POST /auth/login`, etc. → placeholder |
| 0596 | PHP UI sitemap placeholder | `GET /sitemap` → placeholder |
| 0602 | UI route smoke command | (라우트 추가 아님, test only) |
| 0618 | installer route gate | (라우트 추가 아님, access control only) |

## 이 표를 최신으로 유지하는 방법

1. **새로운 라우트 추가**
   - PHP에서 새로운 경로/메서드가 라우터에 등록되면, 이 표에 행을 추가한다.
   - 같은 경로가 Python에 있으면 `python-only` → `parity` 로 갱신하거나, PHP 구현이 canonical이면 `canonical-php` 로 표시한다.

2. **placeholder → 구현**
   - 어떤 라우트가 501 placeholder에서 실제 구현으로 변경되면, 상태를 갱신한다.
   - PHP 구현이 canonical이 되면 `canonical-php` 로 표시한다.

3. **동적 세그먼트 지원**
   - Router가 동적 세그먼트(`{id}` 등)를 지원하게 되면, 관련 라우트들의 상태를 갱신한다.

4. **갱신 타이밍**
   - 코드/테스트 변경이 먼저 진행되고, 이 표는 그 뒤를 따라가는 **후행 기록**이다.
   - 표를 먼저 갱신하고 구현이 뒤따르게 하지 않는다.

## 이 문서가 하지 않는 것

- Route 핸들러 구현 자체를 작성하지 않는다.
- Router나 Http 계층의 아키텍처를 정의하지 않는다 — [PHP UI Architecture](php-ui-architecture.md) 를 참조.
- 각 라우트의 상세 명세를 정의하지 않는다 — 개별 태스크가 그 몫을 맡는다.
- Python API 라우트를 새로 추가하지 않는다 — Python은 Phase D에서 freeze.

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — 서버 렌더링 구조와 라우터 설계
- [PHP DB UI Micro Job Prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) — 라우트 태스크 큐
- [Python UI Deprecation Note](python-ui-deprecation-note.md) — Python UI 미구현 사유
- [PHP Replacement Strategy](php-replacement-strategy.md) — 전환 원칙
- [Python Modules](modules.md) — 모듈과 API 계약
