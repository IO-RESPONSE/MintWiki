# PHP Static Asset Serving

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 "정적 Asset 정책"을 shared
hosting `php/public/` 문서 루트 구조 위에서 구체화한다.

## 목적

MintWiki의 CSS와 JavaScript는 브라우저가 그대로 읽을 수 있는 정적 asset으로
제공한다. shared hosting에 파일만 업로드해도 첫 화면이 스타일과 함께 동작해야
하며, 별도 Node 빌드 파이프라인이나 상시 프론트엔드 서버를 요구하지 않는다.

이 문서는 다음을 고정한다.

- 정적 asset이 어느 디렉터리에 놓이는지 (public 구조)
- 웹 서버가 asset을 어떻게 제공하는지 (front controller 우회)
- no-build 기본값에서 허용/제외되는 항목
- 정적 asset의 보안 기준

## 디렉터리 구조

정적 asset은 웹 문서 루트인 `php/public/` 아래에 둔다. `php/src`,
`php/tests`, `db/` 는 문서 루트 밖에 남으며 웹에서 직접 접근되지 않는다.

```text
php/public/           웹 서버 문서 루트 (DocumentRoot)
├── index.php         front controller (0394, 0419)
└── assets/           정적 asset 루트
    ├── css/          스타일 시트
    └── js/           progressive enhancement 스크립트
```

- 브라우저가 참조하는 asset URL은 문서 루트 기준 절대 경로로 쓴다
  (예: `/assets/css/app.css`). 배포 서브디렉터리에 대한 base path 처리는
  후속 UI 태스크가 view model/layout 계층에서 정한다.
- asset 파일명과 하위 디렉터리 이름은 소문자와 하이픈만 쓰고, 공백이나
  대문자를 쓰지 않는다 — 대소문자 구분 파일시스템 사이의 이식성을 위해서다.
- `assets/` 아래에는 브라우저가 직접 읽는 결과물만 둔다. Sass, TypeScript
  같은 소스는 저장소의 다른 위치에 두더라도 배포 패키지의 동작 조건이 되지
  않아야 한다.

## 웹 서버 직접 제공

정적 asset은 **웹 서버가 문서 루트에서 직접 제공**하며, PHP front
controller(`public/index.php`)를 거치지 않는다. shared hosting의 Apache
기준 동작은 다음과 같다.

- 요청 경로에 해당하는 실제 파일이 `php/public/` 아래에 존재하면 웹 서버가
  그 파일을 그대로 응답한다 (`/assets/css/app.css` → 파일 전송).
- 실제 파일이 없는 경로만 rewrite 규칙으로 `index.php`에 전달한다. 따라서
  라우터는 asset 요청을 route로 등록하거나 PHP에서 파일을 읽어 내보내지
  않는다.
- 이 분리 덕분에 front controller는 HTML 렌더링과 애플리케이션 로직에만
  집중하고, asset 전송의 성능·캐시는 웹 서버가 담당한다.

정적 asset 전송을 PHP로 프록시하는 것은 기본값이 아니다. 접근 제어가 필요한
파일은 애초에 문서 루트 밖에 두고 별도 handler로 내보내며, 그 경우는 정적
asset이 아니라 보호된 다운로드로 다룬다.

## no-build 기본값

기본 배포 경로는 no-build이다. 정적 asset은 설치 도구 없이 업로드만으로
동작해야 한다.

허용되는 사용:

- form submit 전의 가벼운 확인/보조 UI
- 토글, 탭, 검색 입력 보조 같은 progressive enhancement
- 서버 렌더링 HTML이 이미 제공하는 기능을 더 편하게 만드는 동작

기본값에서 제외되는 항목:

- Node 기반 mandatory build
- bundler output만 존재해서 소스로는 브라우저가 읽을 수 없는 asset
- CDN에 반드시 의존하는 UI runtime
- CSS-in-JS나 bundler 없이는 스타일이 적용되지 않는 구조

## 캐시와 버전

정적 asset의 cache header와 버전/무결성 정책은 이 문서에서 값을 확정하지
않는다. 후속 태스크가 정한다.

- HTML과 static asset의 cache header 구분: 0577
- hash 없는 파일의 짧은 캐시 등 static asset cache header: 0578
- 해시/버전 쿼리 기반 static asset integrity 정책: 0606

이 문서는 그 정책들이 붙는 위치가 `php/public/assets/` 아래의 웹 서버 직접
제공 경로임을 고정한다.

## 보안 기준

- 문서 루트에는 브라우저에 직접 노출해도 안전한 asset만 둔다. 비밀 값,
  설정 파일, 서버 사이드 소스는 `php/public/` 밖에 둔다
  (`docs/php-runtime-security-baseline.md`).
- 사용자 업로드는 정적 asset 디렉터리에 저장하지 않는다 — 업로드 정책은
  security baseline과 후속 upload 태스크가 문서 루트 밖 저장을 규정한다.
- JavaScript는 서버가 이미 검증한 데이터만 다루고, 신뢰 경계를 넘는 값을
  DOM에 raw로 삽입하지 않는다. 서버 렌더링 HTML의 escaping 기준
  (`docs/php-ui-architecture.md`의 보안 기준)이 우선한다.

## 후속 태스크 연결

- 0525 이후 page/handler 태스크는 이 문서의 asset 경로 규칙을 참조한다.
- 0577: PHP UI cache header 정책은 HTML과 static asset을 구분한다.
- 0578: PHP static asset cache headers는 hash 없는 파일에 짧은 캐시를 준다.
- 0580: UI performance budget test는 `assets/` 크기 budget을 검증한다.
- 0606: static asset integrity 정책은 해시/버전 쿼리 규칙을 정한다.

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md)
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md)
- [DB Web Hosting Constraints](db-web-hosting-constraints.md)
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md)
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
