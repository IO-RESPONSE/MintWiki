# PHP UI No-JavaScript Fallback Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
[PHP UI Architecture](php-ui-architecture.md)의 서버 렌더링 기본값을 구현할 때,
JavaScript 비활성화 또는 오류 상황에서도 핵심 기능이 작동하도록 하는 정책을 정의한다.

## 목적

MintWiki는 shared hosting 환경에서 안정적으로 동작해야 한다. 사용자가 JavaScript를
비활성화했거나, 브라우저가 구형이거나, 네트워크 오류로 JavaScript 로딩이 실패했을 때도
문서 읽기와 기본 form 제출이 작동해야 한다.

no-JS fallback은 선택사항이 아니라, **서버 렌더링 기본값의 결과**다.

이 문서는 다음을 고정한다:

- HTML form이 JavaScript 없이도 제출되는 방식
- 서버가 제공하는 form validation과 JavaScript 검증의 경계
- 컴포넌트가 사용할 기본 HTML 요소와 속성
- progressive enhancement 패턴의 범위
- 대체 상태 메시지와 오류 처리

## 핵심 원칙

### 1. HTML Form이 기본 경로다

문서 생성, 편집, 사용자 차단 같은 모든 상태 변경은 **HTML form으로 구현**한다.

```html
<!-- 올바른 예: POST form -->
<form method="post" action="/documents">
  <input type="hidden" name="csrf_token" value="...">
  <label for="title">제목</label>
  <input type="text" id="title" name="title" required>
  <button type="submit">저장</button>
</form>
```

`method="post"` 또는 `method="delete"` 같은 실제 HTTP 메서드를 사용한다. JavaScript는 form의
`submit` 이벤트를 가로채 AJAX로 업그레이드할 수 있지만, form 제출 자체는 브라우저의
기본 동작이어야 한다.

### 2. HTML5 Form Validation을 우선한다

서버의 검증이 우선이지만, **클라이언트가 먼저 확인**하는 것이 사용자 경험을 개선한다.

```html
<!-- 필수 입력 -->
<input type="text" name="title" required>

<!-- 타입 검증 (email, url, number 등) -->
<input type="email" name="email" required>

<!-- 길이 제한 -->
<input type="text" name="title" required minlength="1" maxlength="200">

<!-- 정규식 검증 -->
<input type="text" name="username" pattern="[a-z0-9_-]{3,20}" required>
```

이 속성들은:

- JavaScript 없이도 브라우저가 기본 검증을 한다
- JavaScript가 있으면 서버에 요청 전에 미리 피드백을 준다
- 서버는 여전히 모든 입력을 다시 검증한다 (클라이언트 검증은 선택적)

### 3. CSRF Token은 Hidden Field에

상태 변경 form에는 반드시 CSRF token을 포함한다.

```html
<form method="post" action="/documents">
  <input type="hidden" name="csrf_token" value="...">
  <!-- 나머지 필드 -->
</form>
```

token은 URL query parameter가 아니라 **hidden input field**로 전달해야 한다. 이 방식은:

- referer 없이도 안전하다 (shared hosting의 referer 정책 불일치 대비)
- form 복사/북마크 시 실수로 token이 노출되지 않는다
- JavaScript 폼 보강이 기존 field를 그대로 재사용할 수 있다

## 컴포넌트 설계 패턴

### Form Field

#### 텍스트 입력

```html
<label for="title">제목</label>
<input type="text" id="title" name="title" required>
```

- `label` 요소와 `for` 속성으로 접근성을 확보한다
- `name` 속성은 POST 데이터로 서버에 전달된다
- `id` 속성은 label과 JavaScript 선택을 위해 둔다
- `required` 속성은 브라우저가 비어있으면 폼 제출을 거부한다

#### Textarea

```html
<label for="source">내용</label>
<textarea id="source" name="source" required></textarea>
```

Textarea도 form의 일부로 `name` 속성을 가진다. 서버 렌더링 시 값을 미리 채우면
편집 재개가 가능하다 (draft 기능).

#### 체크박스

위험 작업 확인에는 체크박스를 사용한다.

```html
<label>
  <input type="checkbox" name="confirm_danger" value="1" required>
  네, 이 작업을 수행하겠습니다
</label>
```

이 방식은:

- JavaScript 없이 체크 여부만으로 form 제출 가능/불가능이 결정된다
- `required` 속성은 확인을 강제한다
- 라벨이 체크박스 바로 옆에 있어서 클릭 범위가 크다

#### Select

목록 선택은 `<select>` 요소를 기본으로 한다.

```html
<label for="status">상태</label>
<select id="status" name="status" required>
  <option value="">선택하세요</option>
  <option value="draft">임시</option>
  <option value="published">공개</option>
</select>
```

- 모든 옵션이 단순 텍스트다
- 복잡한 아이콘이나 서식은 progressive enhancement로 업그레이드한다
- 첫 옵션이 비어있으면 사용자가 명시적으로 선택하도록 강제한다

### 버튼과 상태

#### 기본 버튼

```html
<button type="submit">저장</button>
```

form 제출의 기본 버튼은 단순한 `<button type="submit">`이다.

#### 비활성화 상태

폼을 제출한 후 중복 클릭을 방지하려면 **서버가 응답할 때까지** 버튼을 비활성화하는 것이 가장 안전하다.
그러나 JavaScript는 제출 전에 미리 버튼을 비활성화할 수 있다.

```html
<!-- HTML만으로는 불가능 (JavaScript 필요) -->
<button type="submit" id="save-button">저장</button>

<script>
  document.getElementById('save-button').addEventListener('click', function() {
    this.disabled = true; // 중복 클릭 방지
  });
</script>
```

CSS는 `:disabled` 의사-클래스로 disabled 상태를 표시한다.

```css
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
```

- **JavaScript 없을 때**: 버튼을 여러 번 클릭하면 여러 form이 제출될 수 있다.
  서버는 idempotency key나 중복 검사로 이를 방지해야 한다.
- **JavaScript 있을 때**: JavaScript가 첫 클릭에 `disabled = true`를 설정해 중복 제출을 즉시 방지한다.

이 구분은 중요하다:
- HTML/CSS만으로 구현 불가능한 기능(클릭 이벤트 가로채기)이므로, 서버는 중복 방지를 구현해야 한다.
- JavaScript가 로딩되지 않았을 때도 기능이 정상 작동하도록 한다.

## 오류 메시지

### 서버 Validation 오류

폼 제출 후 서버에서 유효성 검사를 다시 한다. 오류가 있으면 같은 폼을 다시 렌더링하되,
사용자가 입력한 값과 오류 메시지를 포함한다.

```html
<label for="title">제목</label>
<input type="text" id="title" name="title" value="사용자가 입력한 값" required>
<span class="error" aria-describedby="title-error" id="title-error">
  제목은 200자 이하여야 합니다
</span>
```

이 방식은:

- `value` 속성으로 사용자 입력이 유지된다 (재작성 부담 감소)
- `aria-describedby`로 접근성을 확보한다
- 서버가 같은 HTML 구조로 오류와 함께 재렌더링한다 (JavaScript 필요 없음)
- 오류 메시지는 항상 escaping된 문자열이다 (XSS 방지)

### 브라우저 Validation 오류

HTML5 검증 속성(`required`, `minlength` 등)을 만족하지 않으면 **브라우저가 form 제출을 거부**한다.
이 경우 JavaScript 없이 폼이 제출되지 않으며, 브라우저의 기본 오류 메시지가 표시된다.

- 기본 메시지가 부족하면 `title` 속성이나 `aria-invalid` 같은 보조 정보로 보강할 수 있다
- JavaScript는 더 좋은 오류 표시(예: 아래 정렬된 에러 박스)로 업그레이드할 수 있다

## Progressive Enhancement

### 목표

1. 기본 기능은 HTML form + 서버 렌더링으로 완전히 작동한다.
2. JavaScript가 있으면 더 좋은 UX를 제공한다.
3. JavaScript 오류가 나도 기본 기능은 계속 작동한다.

### 허용되는 JavaScript 사용

- **AJAX 업그레이드**: form을 JavaScript로 가로채 AJAX 요청으로 바꿀 수 있다.
  - 페이지 리로드 없이 응답을 처리한다
  - 서버는 같은 handler에서 `Accept` header를 보고 JSON이나 HTML을 선택할 수 있다
  
  ```javascript
  document.getElementById('edit-form').addEventListener('submit', function(e) {
    e.preventDefault();
    fetch(this.action, {
      method: this.method,
      body: new FormData(this)
    })
    .then(r => r.json())
    .then(data => {
      // 오류 또는 성공 처리
      location.href = data.redirect_url; // 또는 페이지 업데이트
    });
  });
  ```

- **UI 향상**: 버튼 비활성화, 로딩 스피너, 실시간 검증 등
  - 기본 form 제출 경로를 막지 않는다
  - 더 빠른 피드백만 제공한다

- **접근성 개선**: aria-* 속성, keyboard 내비게이션 등
  - 기본 HTML 의미를 유지한다
  - 스크린 리더와 브라우저의 기본 동작을 활용한다

### 금지되는 패턴

- **SPA 라우터**: form을 API로만 제공하고, HTML은 JavaScript가 조립
- **Mandatory build**: 정적 asset이 bundler 없이 읽을 수 없는 형태
- **raw HTML injection**: JavaScript에서 서버 데이터를 `innerHTML`에 삽입
- **form replacement**: 기존 form을 없애고 AJAX form으로만 대체

## 링크 (Navigation)

### GET 요청 링크

문서 읽기, 목록 조회 같은 안전한 작업은 `<a>` 태그로 링크한다.

```html
<a href="/documents/123">문서 보기</a>
<a href="/audit?page=2">감사 로그</a>
```

이 링크들은 JavaScript가 없어도 작동한다.

### 상태 변경 링크

사용자 차단, 문서 삭제 같은 상태 변경은 **form 제출**로만 처리한다. `<a>` 태그로 DELETE
요청을 만들지 않는다.

```html
<!-- 잘못된 예: 링크만으로 상태 변경 -->
<a href="/users/123/block">사용자 차단</a>

<!-- 올바른 예: form으로 처리 -->
<form method="post" action="/users/123/block">
  <input type="hidden" name="csrf_token" value="...">
  <button type="submit">사용자 차단</button>
</form>
```

이 구분은 보안과 의도의 명확성을 위해 필요하다.

## 테스트 전략

### 수동 테스트: JavaScript 비활성화

1. 브라우저 개발자 도구에서 JavaScript를 비활성화한다.
   - Chrome: DevTools → Settings → Disable JavaScript
   - Firefox: about:config → javascript.enabled = false

2. 다음 흐름을 확인한다:
   - 페이지 로딩 (스타일 적용됨, 기본 HTML 콘텐츠 표시)
   - 폼 필드 클릭 및 입력
   - 필수 필드 비우기 (브라우저 validation이 작동하는가?)
   - form 제출
   - 서버 응답 (리다이렉트 또는 오류 페이지)

3. 예상 동작:
   - 모든 문서 내용이 보인다 (JavaScript가 없어도)
   - 폼이 제출된다 (JavaScript가 없어도)
   - 오류 메시지가 표시된다 (JavaScript가 없어도)

### 자동화 테스트

PHP 테스트에서는:

```php
// form 제출을 시뮬레이션한다
$response = $this->postJson('/documents', [
    'csrf_token' => $token,
    'title' => 'Test Document',
    'source' => 'Test source'
]);

// 리다이렉트 또는 성공 응답을 확인한다
$this->assertRedirect($response);
```

HTML 스냅샷 테스트:

```php
// form 필드가 올바른 속성을 가지는지 확인한다
$html = (new DocumentCreatePage())->render();
$this->assertStringContainsString('type="hidden"', $html); // CSRF field
$this->assertStringContainsString('required', $html);      // HTML5 validation
$this->assertStringContainsString('method="post"', $html); // POST form
```

## 제약과 트레이드오프

### JavaScript 로딩 실패의 경우

네트워크 오류로 JavaScript가 로딩되지 않았을 때:

- 기본 기능(form 제출, 문서 읽기)은 **정상 작동한다**
- 향상된 UX(로딩 스피너, 실시간 검증)는 **제공되지 않는다**
- 사용자 경험이 저하되지만, **작업을 완료할 수 있다**

이는 의도적인 설계다. Progressive enhancement의 정의상, 기본 기능이 최우선이다.

### 성능 vs 기능성

JavaScript 최소화는 다음을 의미한다:

- 페이지 로딩 시간이 짧다 (JavaScript 파싱/실행 없음)
- 반응성이 좋다 (form 제출 지연 없음, 서버가 바로 응답)
- 서버 렌더링이 모든 상태를 다룬다 (상태 동기화 필요 없음)

대신:

- AJAX 업그레이드가 없으면 매 form 제출마다 페이지 리로드가 필요하다
- 복잡한 UI는 CSS만으로 구현이 어렵다

후속 태스크에서 필요한 JavaScript를 추가하되, 이 기본값을 유지한다.

### 구형 브라우저

HTML5 검증 속성(`required`, `minlength` 등)을 지원하지 않는 브라우저:

- 폼이 여전히 제출되지만, **브라우저 검증이 작동하지 않는다**
- **서버 검증은 여전히 작동한다** (필수)
- 사용자가 유효하지 않은 데이터를 제출할 가능성이 높다
- 서버가 같은 폼을 오류 메시지와 함께 재렌더링해야 한다

MintWiki는 IE6 같은 매우 구형 브라우저를 지원하지 않으므로, HTML5 지원을 기본값으로 둔다.

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — 서버 렌더링 기본값
- [PHP Static Asset Serving](php-static-asset-serving.md) — JavaScript asset 경로와 progressive enhancement
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — CSRF, escaping, input validation
- [PHP UI Phase QA Checklist](php-ui-phase-qa-checklist.md) — no-JS 테스트 체크리스트
- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — shared hosting 배포 환경

## 후속 태스크 연결

- 0540: PHP CSRF token service는 이 정책의 token field를 생성한다.
- 0541: PHP form error summary는 서버 validation 오류를 표시한다.
- 0543: PHP flash message는 form 제출 후 리다이렉트 메시지를 표시한다.
- 0555 이후: JavaScript asset 태스크는 progressive enhancement 범위 내에서 기능을 추가한다.
