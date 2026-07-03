# PHP UI Cache Header Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 서버 렌더링 구현에서,
HTML 응답과 정적 자산(static asset)의 캐시 정책을 구분하여 정의한다.

## 목적

MintWiki의 shared hosting 환경에서, 프록시/CDN 캐시와 브라우저 캐시가 올바르게 동작해야 한다.

- **HTML 문서**: 내용이 자주 변경되므로 캐시하지 않거나 항상 검증해야 한다
- **정적 자산**(CSS, JS, 이미지): 변경 빈도가 낮으므로 오래 캐시할 수 있다

이 문서는 다음을 고정한다:

- 서버 렌더링 HTML 응답의 캐시 정책
- HTTP 클라이언트가 이해해야 할 Cache-Control 헤더
- CDN/프록시가 수행할 캐싱 동작
- 정적 자산 캐싱과의 구분

## 핵심 원칙

### 1. HTML은 항상 재검증한다

HTML 응답의 캐시-제어 헤더는:

```
Cache-Control: no-cache, no-store, must-revalidate
```

이는:

- `no-cache`: 캐시된 복사본을 검증 없이 사용할 수 없다
  - 브라우저/프록시가 저장할 수 있지만, 항상 서버에 조건부 요청(If-None-Match, If-Modified-Since)을 한다
- `no-store`: 캐시가 응답을 저장하지 않는다 (프라이빗 데이터 대비)
- `must-revalidate`: 캐시가 만료된 응답을 검증 없이 사용할 수 없다

결과적으로 브라우저는 매번 새로고침 시 최신 버전을 확인한다.

### 2. 정적 자산은 장시간 캐시한다

정적 자산(CSS, JS, 이미지)은 응답 헤더가 아닌 웹 서버 설정이나 CDN 규칙으로
캐시되어야 한다:

```
Cache-Control: public, max-age=31536000, immutable
```

- `public`: 공개 콘텐츠로, 프록시도 캐시할 수 있다
- `max-age=31536000`: 1년 동안 캐시 유효
- `immutable`: 파일이 변경되지 않으므로 재검증할 필요 없다

**주의**: MintWiki는 현재 정적 자산을 웹 서버(Nginx/Apache)에서 직접 제공하며,
PHP 애플리케이션이 정적 자산 응답을 생성하지 않는다.

### 3. 보안 헤더와의 조합

캐시 정책은 보안 헤더(태스크 0554)와 함께 적용된다:

```php
Response::html('<p>content</p>')
// 다음 헤더들이 자동으로 포함됨:
// - Cache-Control: no-cache, no-store, must-revalidate
// - X-Content-Type-Options: nosniff
// - X-Frame-Options: DENY
// - Content-Security-Policy: default-src 'self'
```

## 구현 위치

PHP의 `Response::html()` 메서드가 모든 HTML 응답에 캐시 헤더를 자동으로
추가한다. 호출자는 개별적으로 헤더를 설정할 필요가 없다.

```php
public static function html(string $body, int $status = 200, array $headers = []): self
{
    $defaultHeaders = [
        'Cache-Control' => 'no-cache, no-store, must-revalidate',
        'X-Content-Type-Options' => 'nosniff',
        'X-Frame-Options' => 'DENY',
        'Content-Security-Policy' => "default-src 'self'",
        'Content-Type' => 'text/html; charset=utf-8',
    ];
    return new self($status, $defaultHeaders + $headers, $body);
}
```

## 추가 헤더 병합 규칙

호출자가 추가 헤더를 전달할 경우:

```php
Response::html('<p>test</p>', 200, ['X-Custom' => 'value'])
```

기본 헤더(`$defaultHeaders`) 뒤에 추가 헤더를 더한다:

```php
$defaultHeaders + $headers
```

이 순서에서는 **기본값이 우선**이므로, 호출자가 실수로 Cache-Control을
덮어쓸 수 없다.

## 테스트

HTML 응답이 항상 캐시 정책을 포함하는지 확인하는 테스트를 수행한다:

- 기본 캐시 헤더가 모두 포함되는지
- 기본 헤더를 호출자 헤더로 덮어쓸 수 없는지
- 다른 추가 헤더는 정상 병합되는지
- status/body와 함께 정상 동작하는지
