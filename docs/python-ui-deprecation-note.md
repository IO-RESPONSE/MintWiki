# Python UI Deprecation Note

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.

Python 런타임에서 직접 UI를 구현하지 않는 이유와 최종 UI 표준이 PHP shared hosting이 되는 과정을 정의한다.

## 배경

Phase 0-8의 Python 구현 초기 단계에서 FastAPI 기반 API 서버가 먼저 완성되었다. 동시에 UI는 React나 Vue 같은 JavaScript 클라이언트에서 JSON API를 호출하는 SPA(Single Page Application) 패턴을 검토했다. 그러나 공용 웹호스팅 배포 제약을 고려하면서, 다음 사실들이 명확해졌다:

1. 공용 웹호스팅(cPanel, Plesk 등)은 Node.js 빌드 파이프라인을 지원하지 않는다.
2. JavaScript 번들링과 SPA 라우팅은 shared hosting 환경에서 구동되기 어렵다.
3. Python 런타임을 웹호스팅에 배포하는 것도 전문 호스팅(VPS, 관리형) 수준에만 가능하다.
4. 결과적으로 최종 패키징 형태(배포 가능한 상태)는 PHP + MariaDB가 되어야 한다.

## 최종 결정: PHP Shared Hosting이 UI 표준

**Phase D부터 UI는 PHP 서버 렌더링을 기본값으로 구현한다.** 이 결정은 다음 세 가지 원칙 위에 선다:

### 원칙 1: 배포 대상 우선

- 최종 배포 환경은 공용 웹호스팅이다.
- 공용 웹호스팅은 PHP와 MariaDB만 지원하는 것을 기본으로 가정한다.
- 어댑터(adapter)나 선택 구현(optional)이 아니라, **기본 경로가 PHP 서버 렌더링**이어야 한다.

### 원칙 2: UI 구현 통일

Python 런타임과 PHP 런타임은 UI를 따로 구현하지 않는다. 대신:
- 각 모듈(document, parser, render, user, acl 등)의 도메인 계층과 저장소 포트는 계약과 fixture로 언어 독립화한다.
- UI는 **PHP만** 구현한다.
- Python 런타임에서 도메인 기능이 필요하면(테스트, 초기 앱 로직) API 엔드포인트로 접근한다.

### 원칙 3: 문서 가능 상태

[PHP UI Architecture](php-ui-architecture.md)가 정의한 구조와 보안 기준을 정확히 따른다:
- 서버 렌더링 HTML (no SPA router)
- 정적 CSS/JavaScript (no Node build)
- 부트스트랩 불필요 (no-build 기본값)
- 접근 가능성과 보안을 템플릿 계층이 보장

## Python UI가 필요하지 않은 이유

### 개발 진행 순서

Phase A-C(0351-0520)에서 Python으로 계약, 도메인 로직, DB 이식성을 모두 구현한다. Phase D 진입 시점에는 다음이 완료된다:

1. **도메인 계층이 이미 존재** — Python에서 document/parser/render/user/acl/search/jobs/audit/admin 모듈이 완성되어 있다.
2. **계약과 fixture가 언어 독립적** — 모든 기능이 JSON fixture로 정의되어, PHP가 같은 테스트를 통과하게 된다.
3. **DB 스키마가 portable** — ANSI SQL + MariaDB 중심이므로 Python/PHP 모두 같은 DB 사용한다.

따라서 **Python에서 다시 UI를 구현할 이유가 없다**. 도메인 기능 검증은 이미 Python 모듈 테스트로 완료되며, UI는 PHP 서버 렌더링만 하면 된다.

### 배포 복잡도

만약 Python UI를 추가로 구현하면:

- **런타임 이중화** — 배포할 때 Python 서버와 PHP 서버 두 개를 모두 운영해야 한다.
- **호스팅 제약** — Python 런타임은 공용 웹호스팅에서 운영할 수 없으므로, PHP 사용자와 Python 사용자 경로가 갈라진다.
- **유지보수 비용** — 같은 기능을 두 언어에서 유지하면 drift 가능성이 높아진다.

### 기존 설계의 이중성 해소

**Phase 0-8 Python 구현의 위치**:
- 도메인 로직 검증 (필수)
- 계약 정의 (필수)
- API 구현 (선택 — PHP로 대체 가능)
- UI 구현 (제외 — 공용호스팅과 맞지 않음)

## Python 모듈이 유지되는 이유

Python 도메인 계층과 테스트가 완전히 제거되지 않는 이유:

1. **개발 검증 — 로컬 테스트에서 Python이 유일한 전체 구현이다.** Phase D-E 진행 중 PHP 기능이 대치되면서, Python은 쉽게 버려질 수 없다. 만약 Python 코드가 없으면 테스트 픽스처를 누가 처음 작성하는가?

2. **공존 기간 — Phase D-E 동안 Python API 서버와 PHP UI 서버가 공존할 수 있다.** 기술적으로는 운영 경로가 PHP 하나지만, 개발/테스트 시에는 양쪽을 모두 활용할 수 있다.

3. **계약 유지 — PHP가 완전히 준비되기 전까지, Python 구현이 계약의 정답 구현 역할을 한다.** 일단 PHP가 준비되면, Python 도메인 계층은 freeze되고 PHP로의 완전 전환을 진행한다.

## 의사결정 기준 (Decision Criteria)

### Phase D 초반의 신호 — Python UI가 필요 없음을 확인하는 조건

| 조건 | 상태 | 의미 |
|---|---|---|
| 1. 도메인 모듈 계약 완료 | Phase A 완료 (0351-0390) | Python과 PHP가 같은 fixture로 테스트할 준비 |
| 2. 웹호스팅 제약 문서화 | Phase B 완료 (0391-0440) | PHP 서버 렌더링이 유일한 배포 경로임을 확인 |
| 3. DB 이식성 확보 | Phase C 완료 (0441-0520) | Python/PHP 모두 ANSI SQL + MariaDB를 사용 가능 |
| 4. PHP 골격 완성 | Phase D 진행 (0521-0560) | PHP 템플릿, 라우터, 기본 보안이 준비됨 |

### 만약 위 조건이 깨지면

만약 다음 중 하나가 참이면 재검토 필요:

- **공용 웹호스팅이 아닌 다른 배포 경로로 전환** (예: 모든 사용자가 VPS 기준 + 높은 기술 수준) → Python SPA UI 검토 가능
- **PHP 서버 렌더링 표준이 실용적이지 않음** (예: 모바일 앱 전용 UI 필요) → API-first 검토 가능
- **Python 런타임의 webhosting 지원이 대중화** (예: 공용 호스팅이 WSGI 기본 제공) → Python UI 재검토 가능

현재로서는 이 조건들이 모두 False이므로, Python UI 직접 구현은 보류한다.

## 명확한 경계: Python 도메인 ↔ PHP UI

```
Python 런타임 (계속 유지)
├── src/modules/
│   ├── document/     (service, model, value objects)
│   ├── parser/       (정규식, AST)
│   ├── render/       (HTML 생성 로직)
│   ├── user/         (identity, session)
│   ├── acl/          (permission decision)
│   ├── discussion/
│   ├── search/
│   ├── audit/
│   └── admin/
└── tests/
    └── fixtures/     (JSON, 공용)

PHP 런타임 (UI 구현 대상)
├── php/src/Ui/       (새로 추가 — 템플릿, 폼)
├── php/src/Http/     (라우터, 요청 처리)
├── php/public/       (정적 CSS, JS)
└── php/tests/
    └── fixtures/     (공용 — JSON 읽음)

공용 스키마 (양쪽 공유)
├── db/schema/        (ANSI SQL + MariaDB)
└── tests/fixtures/   (JSON — 정답 fixture)
```

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — UI 서버 렌더링 구조와 보안 기준
- [PHP Replacement Strategy](php-replacement-strategy.md) — 모듈별 PHP 전환 원칙
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 웹호스팅 배포 제약
- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — 호스팅 DB 권한 제약
- [PHP-DB-UI Micro Job Prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) — Phase A-E 큐 정책

## 다음 단계

- **0522**: PHP UI template skeleton — Python을 참고하되, PHP 서버 렌더링 한정
- **0525-0570**: PHP 페이지/핸들러 구현 — 도메인은 Python fixture로 검증된 것 재사용
- **0561 이후**: Python 모듈은 수정/확장하지 않고, freeze 및 문서화만 진행
