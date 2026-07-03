# PHP UI Static Asset Integrity Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 정적 asset 정책에서,
캐시 무효화(cache busting)와 무결성 검증을 위한 해시/버전 쿼리 규칙을 정의한다.

## 목적

MintWiki는 shared hosting 환경에서 장시간 정적 asset을 캐시한다.

- 브라우저는 변경되지 않은 파일을 재다운로드하지 않는다
- 프록시/CDN은 다른 사용자의 캐시 복사본을 재사용할 수 있다

이 동작은 성능을 크게 향상시키지만, **파일이 업데이트될 때 기존 캐시를 무효화해야 한다**는 문제가 있다.
이 문서는 다음을 고정한다:

- asset URL에 무결성 식별자를 어떻게 추가할 것인지
- 식별자로 사용할 값 (hash vs version)
- 식별자 계산 및 배포 방법
- 브라우저/프록시 캐시 동작

## 핵심 원칙

### 1. 모든 asset URL에 쿼리 매개변수로 식별자를 추가한다

정적 asset은 항상 쿼리 매개변수로 버전/무결성 식별자를 포함한다:

```html
<!-- 기본 규칙: /assets/[경로]/[파일]?v=[식별자] -->
<link rel="stylesheet" href="/assets/css/design-tokens.css?v=abc123">
<script src="/assets/js/app.js?v=def456"></script>
```

쿼리 매개변수는:

- 표준 HTTP 캐시 메커니즘과 호환된다 (쿼리가 다르면 캐시 키가 다르다)
- 파일 이름을 변경하지 않으므로, 웹 서버가 직접 파일을 제공할 때도 URL rewrite가 필요 없다
- SEO와 asset 경로의 명확성을 유지한다 (URL에 논리적 경로가 보인다)

### 2. 식별자로는 파일 content hash를 기본값으로 한다

파일의 내용이 변경되면 해시가 변경되어, 캐시 무효화가 자동으로 일어난다.

**hash 기본값:**

```
- 알고리즘: SHA-256의 처음 8자 (충돌 가능성 무시할 수 있는 수준)
- 형식: 16진수 소문자
- 예: "abc123de"
```

**hash 계산:**

```
hash = substr(sha256(file_contents), 0, 8)
```

**예시:**

- `design-tokens.css` 내용이 변경 → hash `a1b2c3d4` → `/assets/css/design-tokens.css?v=a1b2c3d4`
- 프록시가 이전 `?v=oldABC` 캐시를 가지고 있어도, 새 query string이 다르므로 새로 다운로드

### 3. 파일별 독립 식별자를 사용한다

각 파일은 자신의 hash를 가진다. 한 파일이 변경되어도 다른 파일의 캐시는 유지된다.

```
/assets/css/design-tokens.css?v=hash1
/assets/css/buttons.css?v=hash2        ← 변경되지 않음, hash2 유지
/assets/css/print.css?v=hash3          ← 변경 가능성 낮음, hash3 유지
```

이는 번들 기반 hash (한 번들의 모든 파일이 같은 hash)보다 캐시 효율성이 높다.

### 4. HTML 응답에서 asset URL 생성 시 현재 hash를 참조한다

asset URL은 **하드코딩되지 않는다**. HTML 렌더링 시점에 현재 파일의 hash를 읽어 URL을 생성한다.

**구현 방식:**

```php
// HTML 템플릿이 asset URL을 생성할 때
$assetUrl = $assetVersioning->url('/assets/css/design-tokens.css');
// 결과: /assets/css/design-tokens.css?v=currentHash
```

이는 배포 시 asset 파일을 먼저 업로드한 후, HTML 렌더링이 현재 파일의 hash를 자동으로 반영하도록 한다.

**런타임 계산 vs 빌드 시 계산:**

- **런타임 (권장)**: 파일 업로드 후 즉시 적용, 별도 빌드 단계 불필요
- **빌드 시**: 배포 패키지를 생성하며 manifest를 만드는 방식도 가능하지만, shared hosting에서는 런타임이 더 간단

task 0607 (Add UI asset version helper)에서 런타임 hash 계산 함수를 구현한다.

## 캐시 헤더와의 조합

### HTTP 캐시 헤더 다시 보기

asset의 캐시 정책은 이미 [PHP UI Cache Header Policy](php-ui-cache-header-policy.md)에서 정의되었다:

```
Cache-Control: public, max-age=31536000, immutable
```

- `max-age=31536000`: 1년 동안 유효한 캐시
- `immutable`: query string이 포함되므로, 같은 URL은 절대 변경되지 않음

### query string 있는 asset의 캐시 키

브라우저와 CDN은 URL 전체를 캐시 키로 사용한다:

```
캐시 키: /assets/css/design-tokens.css?v=abc123
```

파일 내용이 변경되어 hash가 `def456`으로 바뀌면:

```
이전 URL:  /assets/css/design-tokens.css?v=abc123  (1년 캐시됨)
새 URL:    /assets/css/design-tokens.css?v=def456  (새로운 캐시 항목)
```

캐시가 별도 항목이므로, 이전 캐시는 유지되고 새 캐시는 새로 다운로드된다.

## 배포 흐름

### 단계 1: asset 파일 업로드

```
php/public/assets/css/design-tokens.css → 웹 서버에 업로드
php/public/assets/js/app.js → 웹 서버에 업로드
```

기존 query string은 버려진다. 새 파일만 존재한다.

### 단계 2: 런타임 hash 계산

PHP 애플리케이션이 요청을 받으면:

```php
// asset URL이 필요한 시점 (HTML 렌더링 중)
$cssHash = hash('sha256', file_get_contents('php/public/assets/css/design-tokens.css'));
$cssUrl = '/assets/css/design-tokens.css?v=' . substr($cssHash, 0, 8);
// 결과: /assets/css/design-tokens.css?v=a1b2c3d4
```

### 단계 3: HTML에 새 URL을 렌더링

```html
<link rel="stylesheet" href="/assets/css/design-tokens.css?v=a1b2c3d4">
```

다음 번에 asset이 업데이트되면, hash가 바뀌고 URL도 자동으로 새로워진다.

## 성능과 제약

### 런타임 hash 계산의 비용

파일을 매번 읽고 hash를 계산하는 비용:

- **파일 읽기**: small asset (≤15KB gzipped)이므로 무시할 수 있음
- **hash 계산**: PHP의 `hash()` 함수는 매우 빠름 (1KB 파일에 <1ms)

**최적화 권장사항:**

application startup 시 한 번 계산하거나, 애플리케이션 메모리에 캐시할 수 있다.
task 0607에서 구체화한다.

### CDN/프록시의 캐시 동작

query string이 있는 URL은 CDN 설정에 따라 처리가 다를 수 있다:

- **query string을 캐시 키에 포함** (권장): `/assets/css/app.css?v=abc123` ≠ `/assets/css/app.css?v=def456`
  → 각 버전을 별도 캐시 항목으로 취급, 올바른 캐시 무효화
- **query string 무시**: `/assets/css/app.css?v=*` → 같은 캐시 항목
  → 캐시 무효화가 작동하지 않을 가능성 높음

shared hosting의 기본 Apache/Nginx는 query string을 캐시 키에 포함하므로 문제없다.
다른 CDN을 사용하는 경우 설정을 확인해야 한다.

## 대안: version number 사용

hash 대신 명시적 version number를 사용할 수도 있다:

```
/assets/css/design-tokens.css?v=1.0.0
```

**장점:**

- 인간이 읽을 수 있음
- 배포 시 명시적으로 관리

**단점:**

- 개발자가 수동으로 버전을 증가시켜야 함 (실수 가능성)
- 파일이 같으면 버전도 같으므로, 일부 파일만 변경되는 경우 버전 관리가 복잡해짐

MintWiki는 **파일 content hash를 기본값**으로 삼는다. version number는 필요시 task 이후의 배포 자동화 단계에서 추가할 수 있다.

## 후속 구현 태스크

- **0607**: PHP asset version helper 함수 구현 (`$assetVersioning->url()`, 런타임 hash 계산)
- **0608**: UI 배포 체크리스트 (asset 업로드 순서, HTML 렌더링 순서 확인)
- **0609**: UI rollback 체크리스트 (이전 asset 버전 복원, URL의 hash 변경 확인)

## 보안 고려사항

### query string injection 방지

asset URL은 사용자 입력으로 조작되지 않는다. `$assetVersioning->url()` 함수가 정적으로 정의된 파일 경로만 지원한다:

```php
// 허용됨
$assetVersioning->url('/assets/css/app.css')

// 허용 안 됨 (함수 시그니처로 검증)
$assetVersioning->url($userInput)
```

### hash 충돌

SHA-256의 처음 8자 (약 32비트)는 약 4 billion 조합을 가진다. asset이 대량으로 업데이트되지 않는 한, 충돌 가능성은 무시할 수 있다.

더 강한 검증이 필요하면 전체 SHA-256 hash를 사용할 수 있다 (64자).

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md)
- [PHP Static Asset Serving](php-static-asset-serving.md)
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md)
- [PHP UI Performance Budget](php-ui-performance-budget.md)
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)

## 관련 태스크

- 0578: Add PHP static asset cache headers (기본 캐시 정책)
- **0606**: Add UI static asset integrity docs (이 문서)
- 0607: Add UI asset version helper (런타임 구현)
- 0608: Add UI deployment checklist (배포 프로세스)
- 0609: Add UI rollback checklist (롤백 프로세스)
