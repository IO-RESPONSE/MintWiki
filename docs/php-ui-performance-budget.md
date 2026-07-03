# PHP UI Performance Budget

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 서버 렌더링 기본값에서,
HTML 응답과 정적 자산(CSS, JavaScript)의 크기 예산을 정의한다.

## 목적

MintWiki는 shared hosting 환경을 기본값으로 삼는다. 이 환경에서는:

- 저속 네트워크 연결(≤3G)이 일반적이다
- CDN을 기본으로 사용하지 않는다
- 페이지 렌더링 속도가 사용성과 신뢰성에 영향을 준다

이 문서는 다음을 고정한다:

- 기본 HTML 응답 크기 상한
- CSS 번들의 크기 상한
- JavaScript 번들의 크기 상한 및 정책
- 크기 증가 시 검토 프로세스
- 측정 방법과 도구

## 핵심 원칙

### 1. HTML은 렌더링 기본값을 따른다

서버 렌더링 HTML 응답은 각 페이지별로 다르지만, 기본 구조(레이아웃, 네비게이션)는
일정하다.

- **기본 레이아웃 응답**: ≤ 3 KB (gzipped)
  - `<html>`, `<head>` 메타 정보 및 asset 참조
  - `<header>` 네비게이션
  - `<main>` 영역 (페이지별 내용 제외)
  - `<footer>` 기본 정보

- **페이지별 콘텐츠**: 별도 측정
  - 문서 내용(render output): 측정 대상이 아님 (사용자 입력 크기)
  - 메타데이터(제목, 작성자, 시간 등): ≤ 500 B
  - 폼 마크업: ≤ 1 KB

기본 레이아웃 크기가 증가하면 레이아웃 컴포넌트(`0525`) 또는 네비게이션 모델(`0550`)
을 검토해야 한다.

### 2. CSS는 최소한의 스타일만 포함한다

CSS는 shared hosting의 첫 로드부터 다운로드되므로, 불필요한 규칙은 제외해야 한다.

- **CSS 총 크기**: ≤ 15 KB (gzipped)
- **파일별 제한**: 각 파일 ≤ 5 KB (gzipped)
  - `design-tokens.css`: ≤ 4 KB (색상, spacing, typography)
  - `buttons.css`: ≤ 2 KB
  - `responsive-table.css`: ≤ 3 KB
  - `print.css`: ≤ 1 KB
  - `forms.css`: ≤ 2 KB (0530, 0532 폼 추가 시)
  - `components.css`: ≤ 2 KB (추가 컴포넌트용 예약)

CSS는 다음 원칙을 따른다:

- 불필요한 색상/크기 변형을 만들지 않는다 (design token에서만 정의)
- vendor prefix는 자동화된 도구로만 추가한다 (손수 작성 금지)
- CSS framework 또는 utility-first 방식(예: Tailwind)을 사용하지 않는다
  (대신 semantic class와 design token 기반)
- 사용되지 않는 규칙이 누적되지 않도록 주기적으로 정리한다

### 3. JavaScript는 점진적 향상만 구현한다

JavaScript는 선택사항이다. 기본 기능은 HTML과 CSS만으로 작동해야 한다.

- **JS 총 크기**: ≤ 5 KB (gzipped)
  - 초기 목표: 0 (static HTML/CSS만 사용)
  - 추가 시: form validation, toggle, interactive state만 허용

JavaScript는 다음 기준을 만족할 때만 추가한다:

- 기존 form/link 기능을 더 편하게 만든다 (반드시 필요하지 않음)
- 번들러나 build tool을 요구하지 않는다 (plain ES5 또는 모듈 최소화)
- 네트워크 오류 시 기능이 저하되지만 작동 불가는 되지 않는다

## 측정 방법

### 도구

```bash
# CSS 크기 확인 (gzipped, 포함)
gzip -c php/public/assets/css/design-tokens.css | wc -c

# 모든 CSS 파일 합산
cat php/public/assets/css/*.css | gzip | wc -c

# HTML 응답 크기 (렌더링 후 측정)
php -S 127.0.0.1:8000 -t php/public &
curl -s 'http://127.0.0.1:8000/' | gzip | wc -c
```

### CI 또는 테스트

태스크 0580(Add PHP UI performance budget test)이 자동 크기 검사를 제공한다.

```bash
# `scripts/test.sh` 일부
php/scripts/qa.sh --performance-budget
```

## 크기 증가 시 대응

크기 상한을 초과할 경우 다음을 검토한다:

### CSS 증가

1. **현재 파일 내용 정리**: 사용되지 않는 규칙, 중복 정의가 없는지 확인
2. **설계 재검토**: 새 변형이 필요한 경우 design token으로 기존 값을 재조합할 수 있는지 확인
3. **필요시 태스크 등재**: 크기 증가가 정당하면 `docs/php-db-ui-micro-job-prompts-0351-0670.md`에 추가 항목 제안

예: 문서 렌더링 HTML이 특별한 스타일을 요구하면, 그 스타일을 새 `.css` 파일로 분리하되 여전히 예산 범위 내에서 운영한다.

### JavaScript 증가

1. **복잡도 검토**: 번들 도구 도입을 요구하지는 않는가?
2. **필수성 재평가**: 서버 렌더링 또는 HTML form만으로 구현할 수 없는가?
3. **파일 분리**: 필요하면 module pattern이나 named IIFE로 파일을 분리하되, 매번 `<script>` 태그를 추가해야 한다

예: form validation 스크립트가 커지면 `php/public/assets/js/validation.js`로 분리하고 필요한 페이지에서만 `<script src="/assets/js/validation.js"></script>`로 로드한다.

## 성능 최적화 체크리스트

개발자가 크기 증가 시 자문할 항목:

### CSS

- [ ] 색상/크기가 design token으로 정의되어 있는가? (하드코딩된 값 없음)
- [ ] 같은 선택자가 여러 파일에 반복되지는 않는가?
- [ ] 불필요한 media query 또는 폴백 규칙이 없는가?
- [ ] 선택자 특이도(specificity)가 타당한가? (`.class#id` 같은 과도한 조합 금지)

### JavaScript

- [ ] 번들러(webpack, vite 등) 또는 transpiler(TypeScript, Babel)가 필요한가? (기본값: 필요 없어야 함)
- [ ] 같은 기능을 HTML + CSS로 구현할 수 없는가?
- [ ] 로드 실패 시 fallback이 있는가? (기본값: 없어도 작동해야 함)
- [ ] 외부 라이브러리에 의존하지는 않는가? (CDN 불가능)

### HTML

- [ ] 레이아웃 컴포넌트에 불필요한 마크업이 추가되지 않았는가?
- [ ] 반복되는 HTML 구조가 template/component로 재사용되는가?

## 예외 처리

예산 초과가 정당한 경우:

1. **문서 렌더링 출력**: render module이 생성하는 HTML은 크기 제한 대상이 아니다 (사용자 입력 크기)
2. **임시 마이그레이션**: 구형 브라우저 호환성 필요 시 (예: IE 폴백), 임시로 크기 증가를 인정할 수 있으나 반드시 문서화한다
3. **성능 최적화**: 명확한 이유로 성능 개선이 필요하면 (예: 네트워크 요청 감소), 코드 리뷰를 통해 검토한다

## 관련 문서 및 태스크

- [PHP UI Architecture](php-ui-architecture.md)
- [PHP Static Asset Serving](php-static-asset-serving.md)
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md)
- 0525: Add PHP base layout renderer (레이아웃 크기의 시작점)
- 0527: Add UI design token CSS (CSS 정책)
- 0580: Add PHP UI performance budget test (자동 검사)
- 0606: Add PHP UI asset integrity policy (hash/버전 정책, 크기와 무관)
