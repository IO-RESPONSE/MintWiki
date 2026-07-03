# PHP Runtime Security Baseline

이 문서는 PHP 런타임이 지켜야 할 보안 기준을 escaping, session, upload,
path traversal 네 영역으로 나눠 고정한다. Phase B: PHP Runtime Skeleton,
0391-0440 의 산출물이다(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).
**이 네 영역의 실제 구현(코드, 클래스, 스크립트, `php/composer.json`
변경)은 이 문서의 범위가 아니다** — 아래 각 절이 가리키는 후속 태스크가
구현한다. 이 문서는 그 태스크들이 따라야 할 기준선만 미리 정해 둔다.

## 배경: 이 문서 이후 실제 구현을 맡는 후속 태스크

`docs/php-db-ui-micro-job-prompts-0351-0670.md` 에 이미 예정된 태스크
목록이다 — 이 문서는 이 태스크들의 구현 범위를 대신하지 않고, 그
태스크들이 공유해야 할 원칙만 미리 고정한다.

- **escaping**: 0567(UI XSS regression fixture), 0571(search result
  component snippet escape).
- **session**: 0632(shared hosting session 정책), 0633(PHP session
  adapter skeleton).
- **upload**: 0626(writable directories 정책), 0629(upload directory
  check).
- **path traversal**: 0635(path traversal guard), 0638(backup download
  guard).
- 위 네 영역을 아우르는 상위 체크리스트: 0554(UI 보안 헤더),
  0540/0541(CSRF), 0634(cookie 보안 정책), 0658(shared hosting 보안
  체크리스트).

## 1. Escaping 기준

- 모든 사용자 입력 유래 문자열을 HTML로 출력하기 전에 반드시
  이스케이프한다. 기준 함수는 Python 쪽 `src/modules/render/escape.py`
  의 `escape_html`과 동등해야 한다 — `&`, `<`, `>`, `"`, `'` 다섯 문자를
  모두 치환한다. PHP 네이티브로는
  `htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5, 'UTF-8')`
  가 이 기준을 만족하는 기본 선택지다(`ENT_QUOTES`가 작은따옴표까지
  이스케이프해야 `escape_html`의 `&#x27;` 치환과 동등해진다).
- `php/src/Http/Response.php`의 `Response::html()`(태스크 0418)은
  "서버 렌더링 기반만 두는 단계이므로 이스케이프나 템플릿 처리는 하지
  않고, 이미 완성된 HTML 문자열을 그대로 감싼다"고 스스로 범위를
  제한한다. 이 기준은 그 빈틈을 명시한다 — `Response::html()`은
  이스케이프 책임을 지지 않으므로, `Response::html()`을 호출하는 UI
  계층(`php/src/Ui/`, 아직 없음) 쪽이 body 문자열을 조립하는 시점에
  사용자 입력을 직접 이스케이프해야 한다. `Response`나 `Http` 계층에
  이스케이프 로직을 넣지 않는다 — 어댑터 계층은 이미 안전하게 만들어진
  문자열만 다뤄야 한다.
- URL 출력은 Python 쪽 `src/modules/render/url_sanitizer.py`가 쓰는
  스킴 allowlist(`http`, `https`, `ftp`, `ftps`, `mailto`, `tel`, `sms`,
  `geo`) 원칙을 그대로 따른다 — `javascript:`, `data:`, `vbscript:` 등
  임의 스킴을 denylist로 걸러내지 않고, 허용 스킴만 통과시킨다.
- `Response::json()`(태스크 0417)은 `json_encode(..., JSON_THROW_ON_ERROR)`
  를 쓰므로 JSON 컨텍스트 출력 자체는 이미 안전하다. 다만 그 JSON을
  `<script>` 태그 안에 직접 삽입하는 용도로 재사용한다면
  `JSON_HEX_TAG`, `JSON_HEX_AMP` 같은 추가 플래그가 필요하다 — 지금은
  그런 삽입 지점이 없으므로 이 문서는 그 플래그를 미리 강제하지 않고,
  실제로 그런 지점이 생기는 태스크가 판단한다.

## 2. Session 기준

- `docs/php-no-framework-domain-rule.md`가 고정한 경계에 따라, 세션
  처리(`session_start()`, `$_SESSION` superglobal 접근)는
  `php/src/Modules/` 도메인 코드에 직접 넣지 않는다 — `php/src/Security/`
  (아직 없음, 0540/0633이 만들 예정) 같은 어댑터 계층의 책임이다.
- Python 쪽 `src/modules/user/session.py`의 `Session` 도메인 모델(고유
  `id`, `user_id`, `created_at`, `expires_at`, 빈 값 거부)이 이식
  기준이다 — PHP session adapter(0633)는 같은 필드와 유효성 검사를
  갖춰야 한다.
- 세션 ID는 로그인 성공 시점에 재발급한다(session fixation 방지).
  PHP 내장 세션 ID 생성기(CSPRNG 기반)를 그대로 쓰고, 예측 가능한
  커스텀 ID 생성 로직으로 대체하지 않는다.
- 세션 수명은 `Session.expires_at`과 일치시키고, 로그아웃 시 서버 쪽
  세션 데이터를 즉시 무효화한다 — 클라이언트 쿠키 삭제만으로 끝내지
  않는다.
- 세션 저장소를 파일 기반으로 할지 DB 기반으로 할지는 0632(shared
  hosting session 정책)가 결정한다 — 이 문서는 어느 쪽을 선택하더라도
  위 세 가지(도메인 계층 분리, 재발급, 수명 일치)는 공통으로 지켜야
  한다는 것만 못박는다.
- 세션 쿠키의 `Secure`/`HttpOnly`/`SameSite` 속성 값은 0634(cookie
  보안 정책)가 구체적으로 정한다 — 이 문서는 그 값을 미리 정하지
  않는다.

## 3. Upload 기준

- 지금 이 저장소에는 Python 쪽과 PHP 쪽 모두 파일 업로드 기능이 없다.
  이 절은 0629(upload directory check)가 실제로 업로드 디렉터리 검사를
  구현할 때 지켜야 할 기준을 미리 고정해 두는 것이다.
- 업로드된 파일은 `php/public/`(웹에서 직접 실행 가능한 문서 루트,
  태스크 0393/0394) 밖에 저장한다 — 웹 루트 안에 저장하면 업로드된
  파일이 `.php`로 직접 실행될 수 있다.
- 업로드 디렉터리는 0626(writable directories 정책)이 분리하는
  `cache`/`uploads`/`logs` 중 `uploads` 전용 디렉터리를 쓰고, 웹 서버가
  그 디렉터리 안의 스크립트를 실행하지 못하게 한다(예: 실행 권한 제거,
  `.htaccess`의 `php_flag engine off` 또는 동등한 shared hosting 설정 —
  구체적인 적용 방법은 0629가 정한다).
- 원본 업로드 파일명을 그대로 파일시스템 경로로 쓰지 않는다 — 파일명은
  메타데이터로만 보존하고, 실제 저장 경로는 서버가 생성한 식별자
  (`docs/portable-id-policy.md` 가 있다면 그 규칙, 없다면 무작위/해시
  기반 이름)를 쓴다.
- 허용 확장자/MIME 타입은 denylist가 아니라 allowlist로 검사한다 —
  위 escaping 절의 URL 스킴 allowlist 원칙과 같은 방향이다.

## 4. Path Traversal 기준

- 사용자 입력(문서 제목, 파일명, 쿼리 파라미터 등)으로부터 파일시스템
  경로를 만드는 모든 코드는, 최종 경로를 실제로 열기 전에 그 경로가
  의도한 기준 디렉터리(base directory) 밖으로 벗어나지 않는지 검증해야
  한다 — `realpath()`로 정규화한 뒤 기준 디렉터리 접두사와 비교하는
  방식을 기본으로 삼는다. `../` 문자열 치환만으로 막는 방식은 인코딩
  우회나 심볼릭 링크에 취약하므로 채택하지 않는다.
- 이 검증 로직은 `docs/php-no-framework-domain-rule.md`의 경계에 따라
  `php/src/Modules/` 도메인 코드가 아니라 어댑터 계층
  (`php/src/Security/`, 0635가 만들 예정)에 둔다.
- 0635(path traversal guard)가 실제 가드를 구현하고, 0638(backup
  download guard)처럼 관리자 권한이 필요한 파일 다운로드 경로에도 이
  가드를 함께 적용한다 — 권한 검사와 경로 검사는 서로 대체할 수 없는
  별개 방어선이다.
- config 파일(`php/src/App/ConfigLoader.php`가 읽는 대상)과 업로드
  디렉터리(3절) 모두 이 기준의 적용 대상이다.

## 이 문서가 하지 않는 것

- escaping 헬퍼 함수, session adapter, upload 디렉터리 검사, path
  traversal guard 클래스를 실제로 작성하지 않는다 — 각 절이 가리키는
  후속 태스크(0540/0554/0567/0571/0626/0629/0632/0633/0634/0635/0638/0658)
  가 구현한다.
- `php/composer.json`, `php/src/Http/Response.php`, `php/src/App/`를
  수정하지 않는다.
- 쿠키 속성 값, 세션 저장소 종류, 업로드 허용 확장자 목록처럼 각
  후속 태스크가 구체적으로 정해야 할 세부 값을 미리 확정하지 않는다.

## 관련 문서

- `docs/php-no-framework-domain-rule.md` — session/upload/path
  traversal 처리가 도메인이 아닌 어댑터 계층 책임이라는 경계 근거.
- `docs/php-coding-standard.md` — PHP 코딩 표준 정본.
- `docs/php-replacement-strategy.md` — shared hosting 배포 제약(웹 루트
  밖 저장, 실행 권한 제한 등 upload/path 기준의 배경).
- `docs/shared-hosting-session-policy.md` — PHP 기본 세션, 파일 기반 세션,
  DB 기반 세션 선택 기준.
- `docs/cookie-security-policy.md` — 세션 쿠키의 `Secure`/`HttpOnly`/
  `SameSite` 속성 기준.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 이 문서가 가리키는
  0540/0541/0554/0567/0571/0626/0629/0632/0633/0634/0635/0638/0658 등
  후속 태스크 정의.
- `src/modules/render/escape.py`, `src/modules/render/url_sanitizer.py`
  — escaping 기준의 이식 원본(Python).
- `src/modules/user/session.py` — session 기준의 이식 원본(Python).
