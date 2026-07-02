# PHP UI Architecture

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
PHP 런타임과 MariaDB portable DB 계층 이후에 붙는 기본 UI 아키텍처를
정의한다.

## 목적

MintWiki의 최종 패키징 대상은 PHP + MariaDB shared hosting이다. UI는 이
배포 조건을 기본값으로 삼아야 하므로, 별도 Node 빌드 파이프라인이나 상시
프론트엔드 서버를 요구하지 않는다.

- 기본 UI는 PHP 서버 렌더링으로 제공한다.
- HTML 템플릿은 `php/` 런타임 안에 두고 라우터/서비스 계층과 같은 배포
  단위로 패키징한다.
- CSS와 JavaScript는 정적 asset으로 제공한다.
- 기본 배포 경로는 no-build이다.

## 서버 렌더링 기본값

문서 보기, 생성, 편집, 이력, 검색, 로그인 같은 핵심 화면은 PHP request
안에서 HTML을 렌더링한다. JSON API는 내부 통합과 점진적 향상을 위해 남길 수
있지만, 첫 화면을 API 호출 이후 JavaScript가 조립하는 구조를 기본값으로 두지
않는다.

이 원칙은 shared hosting에서 다음 장점을 준다.

- PHP 파일과 정적 asset만 업로드해도 첫 화면이 동작한다.
- MariaDB 연결, installer diagnostics, 권한 오류 같은 서버 상태를 같은
  request 안에서 바로 HTML로 표현할 수 있다.
- JavaScript가 비활성화되어도 문서 읽기와 기본 form 제출 흐름을 유지할 수
  있다.

## 템플릿 경계

템플릿은 도메인 객체를 직접 변경하지 않는다. 라우터나 application service가
화면에 필요한 값을 view model 형태로 만든 뒤 템플릿에 전달한다.

템플릿 계층의 책임:

- HTML 구조와 화면별 partial 조합
- 사용자에게 노출되는 문자열 escaping
- form field 이름과 오류 메시지 배치
- layout, navigation, flash message 렌더링

템플릿 계층의 책임이 아닌 것:

- PDO query 실행
- 권한 판정
- CSRF token 생성/검증
- 문서 제목 정규화나 revision 생성 같은 도메인 규칙

## 정적 Asset 정책

CSS와 JavaScript는 `php/public/` 아래의 정적 asset으로 제공한다. 기본
패키지는 브라우저가 그대로 읽을 수 있는 파일을 포함해야 하며, Sass,
TypeScript, bundler를 설치해야만 동작하는 구조를 만들지 않는다.

허용되는 JavaScript 사용:

- form submit 전의 가벼운 확인/보조 UI
- 토글, 탭, 검색 입력 보조 같은 progressive enhancement
- 서버 렌더링 HTML이 이미 제공하는 기능을 더 편하게 만드는 동작

기본값에서 제외되는 항목:

- Node 기반 mandatory build
- SPA router를 전제로 한 첫 화면
- CDN에 반드시 의존하는 UI runtime
- CSS-in-JS나 bundler output만 존재하는 스타일 시스템

## 보안 기준

HTML 출력은 기본적으로 escaping된 문자열만 사용한다. raw HTML 삽입은 renderer
모듈이 이미 검증한 문서 HTML처럼 신뢰 경계가 분명한 값에만 허용한다.

모든 state-changing form은 후속 CSRF 서비스 태스크가 제공하는 token을 포함해야
한다. Phase D 초반의 skeleton 화면은 token 검증을 구현하지 않더라도, form
구조가 CSRF token field를 넣을 수 있는 위치를 막지 않아야 한다.

## 후속 태스크 연결

- 0522: PHP UI template skeleton은 이 문서의 템플릿 경계를 따른다.
- 0523: HTML escaping tests는 이 문서의 보안 기준을 검증한다.
- 0524: static asset serving docs는 이 문서의 정적 asset 정책을 구체화한다.
- 0525 이후 page/handler 태스크는 서버 렌더링 기본값을 따른다.

## 관련 문서

- [PHP Runtime Phase QA Checklist](php-runtime-phase-qa-checklist.md)
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md)
- [PHP Replacement Strategy](php-replacement-strategy.md)
- [DB Web Hosting Constraints](db-web-hosting-constraints.md)
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md)
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
