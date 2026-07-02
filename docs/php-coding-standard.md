# PHP Coding Standard

이 문서는 `php/` 트리에 새 코드를 추가할 때 지켜야 하는 최소 코딩 표준을
고정한다. Phase B: PHP Runtime Skeleton, 0391-0440
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)의 산출물이며, 지금까지
작성된 `php/src/`, `php/tests/` 아래 파일들이 실제로 따르고 있는 패턴을
사후적으로 문서화한 것이다 — 새 규칙을 발명하지 않는다.

## PSR-4 오토로딩 규칙

`php/composer.json`은 두 개의 오토로드 항목을 함께 쓴다.

```json
"autoload": {
    "psr-4": {
        "MintWiki\\": "src/"
    },
    "classmap": [
        "src/Modules/"
    ]
}
```

- `MintWiki\` 접두사는 `src/` 아래 표준 PSR-4 규칙(namespace 세그먼트 =
  디렉터리 세그먼트)을 따르는 코드에 적용된다. 예: `MintWiki\App\ConfigLoader`는
  `src/App/ConfigLoader.php`, `MintWiki\Http\Response`는
  `src/Http/Response.php`.
- **예외**: `src/Modules/<Module>/` 아래 클래스는 namespace가
  `MintWiki\<Module>`이지만 파일 경로에는 `Modules/` 세그먼트가 추가로
  들어간다(예: `MintWiki\Document\Document` 클래스가
  `src/Modules/Document/Document.php`에 있음 — `src/Document/Document.php`가
  아니다). 이는 PSR-4 규칙을 어기므로, `composer.json`이 `src/Modules/`
  전체를 `classmap`으로 별도 등록해 클래스 이름 → 파일 경로를 직접
  스캔해서 찾는다. 이 예외는 `docs/php-namespace-mapping.md`가 정의한
  "Python `modules.<module>` → PHP `MintWiki\<Module>`" 매핑을 유지하면서,
  `src/Modules/`라는 실제 디렉터리 계층(`docs/modules.md`의 12개 모듈과
  1:1 대응)을 그대로 두기 위한 의도적 선택이다 — namespace를
  `MintWiki\Modules\<Module>`로 바꾸지 않는다.
- 새 클래스를 추가할 때 규칙: 파일이 `src/Modules/` 아래 있으면
  classmap이 적용되므로 PSR-4 규칙과 무관하게 namespace만
  `docs/php-namespace-mapping.md`를 따르면 된다. 그 밖(`src/App/`,
  `src/Http/` 등 애플리케이션 부트스트랩 계층)은 표준 PSR-4 규칙을
  그대로 따른다 — namespace 세그먼트가 곧 디렉터리 세그먼트다.
- `composer install`을 다시 실행하지 않아도 `classmap`은 `composer
  dump-autoload`가 다시 스캔해야 새 클래스를 인식한다는 점에 유의한다
  (표준 PSR-4는 디렉터리 규칙만 맞으면 재스캔이 필요 없다). `docs/php-test-bootstrap.md`가
  설명하는 `composer install` 절차가 이 재생성을 함께 수행한다.

## strict_types 규칙

`php/src/`, `php/tests/` 아래 모든 `.php` 파일은 첫 줄부터 아래 3줄을
정확히 이 순서로 둔다(파일에 클래스가 없는 스크립트도 동일):

```php
<?php

declare(strict_types=1);

namespace MintWiki\...;
```

- `declare(strict_types=1)`은 파일마다 반드시 선언한다 — 타입 강제
  변환(coercion)에 기대는 코드를 허용하지 않기 위해서다. PHP는 이
  선언을 파일 단위로만 적용하므로 예외 없이 모든 파일에 넣는다.
- `<?php` 여는 태그와 `declare` 사이, `declare`와 `namespace`(또는
  namespace가 없는 최상위 스크립트라면 본문) 사이에 빈 줄을 하나씩
  둔다. `php/tests/AutoloadSmokeTest.php`처럼 namespace가 없는 실행
  스크립트도 `declare(strict_types=1);` 은 그대로 유지한다.
- 닫는 태그 `?>`는 쓰지 않는다 — 파일 끝에 의도치 않은 출력(공백/개행)이
  섞여 HTTP 응답이나 헤더 전송에 영향을 주는 것을 피하기 위한 PHP
  커뮤니티 표준 관행이며, 현재 모든 파일이 이를 따른다.

## Namespace 규칙

세부 매핑 규칙(모듈 이름 → namespace, 예시 표)은
`docs/php-namespace-mapping.md`가 정본이다. 이 문서는 그 규칙을 코드
작성 시 지켜야 할 절차로 요약만 한다.

- 최상위 접두사는 항상 `MintWiki`다 — 모듈마다 다른 접두사를 쓰지
  않는다.
- `src/Modules/<module>/` 아래 코드는 `MintWiki\<Module>`(module 디렉터리
  이름을 PascalCase로 바꾼 것)을 쓴다.
- `src/App/`, `src/Http/`처럼 모듈이 아닌 애플리케이션 부트스트랩
  계층은 디렉터리 이름을 그대로 PascalCase 세그먼트로 쓴다
  (`MintWiki\App`, `MintWiki\Http`) — `docs/php-namespace-mapping.md`의
  모듈 매핑 대상이 아니다.
- 파일 하나에 최상위 클래스/interface 하나만 선언한다. 파일 이름은
  그 클래스/interface 이름과 정확히 같다(대소문자 포함) — PSR-4와
  classmap 양쪽 오토로드 방식 모두 이 관례에 의존한다.
- `use` 구문으로 다른 namespace의 클래스를 가져올 때도 항상 전체
  `MintWiki\...` 경로를 쓴다(예: `App/ErrorCodeRegistry.php`의
  `use MintWiki\Document\DuplicateNormalizedTitleError;`). 상대
  namespace 참조나 `use`를 생략한 완전정규화 이름(`\MintWiki\...`)
  반복 사용은 쓰지 않는다 — PHP 내장 클래스(`\Exception` 등)를 가리킬
  때만 선행 `\`를 쓴다.

## 클래스 선언 규칙

- 값 객체, 서비스, 예외 등 상속을 의도하지 않는 클래스는 기본적으로
  `final class`로 선언한다. 지금까지 작성된 클래스는 예외 없이
  `final`이다.
- 모듈 경계(저장소 포트, 캐시 백엔드, 잡 러너 등)처럼 여러 구현이
  필요한 지점만 `interface`로 선언한다(예: `Modules/Document/Repository.php`,
  `Modules/Cache/Backend.php`, `Modules/Jobs/Runner.php`). `abstract
  class`는 지금까지 쓰지 않는다 — 공유 구현이 필요해지기 전까지는
  interface로 충분하다.
- 도메인 예외는 `final class ... extends \Exception`으로 선언하고,
  클래스 이름 자체가 실패 사유를 설명하게 한다(예:
  `EmptyTitleError`, `DuplicateNormalizedTitleError`, `NotFoundError`).
  범용 `\InvalidArgumentException`을 그대로 던지지 않는다.
- 생성자 프로퍼티 승격(constructor property promotion)과 `readonly`를
  값 객체에 기본으로 쓴다(예: `Http/Response.php`의
  `private readonly int $status`). 값 객체는 생성 후 상태가 바뀌지
  않아야 하므로, setter를 추가하지 않는다.
- 클래스 바로 위에 한글 docblock으로 클래스의 책임과 이를 도입한
  태스크 번호를 한 줄로 남긴다(예: `/** 문서를 표현하는 불변 value
  object (태스크 0400). */`). 이 관례는 코드 자체가 어떤 태스크
  산출물인지 추적하기 위한 것이며, 이 문서가 강제하는 필수 규칙이라기
  보다는 지금까지 일관되게 지켜진 관행이다 — 새 파일도 이어서 남긴다.

## 이 문서가 하지 않는 것

- PHPStan/Psalm 등 정적 분석 도구 도입 여부와 규칙은 다루지 않는다
  — 0423(Add PHP static analysis plan)의 범위다.
- 도메인 계층의 framework 사용 금지 규칙(Python
  `scripts/check_boundaries.py`가 강제하는 것과 동등한 PHP 쪽 경계)은
  다루지 않는다 — 0424(Add PHP no-framework-domain rule)의 범위다.
- 코드 포매터(phpcs/php-cs-fixer 등) 자동 적용 도구를 도입하거나
  설정하지 않는다 — 이 문서는 사람이 읽고 따르는 규칙만 고정하며,
  자동화 도구 도입은 별도 태스크의 판단에 맡긴다.
- `src/Modules/` classmap 예외를 없애기 위해 디렉터리 구조나 namespace
  를 바꾸지 않는다 — 현재 상태를 있는 그대로 문서화할 뿐이다.

## 관련 문서

- `docs/php-namespace-mapping.md` — 모듈별 namespace 매핑 표(이 문서가
  요약만 하는 정본).
- `docs/php-replacement-strategy.md` — `php/` 트리가 따르는 모듈 단위
  1:1 교체 원칙.
- `docs/php-no-framework-domain-rule.md` — 0424가 정의하는 도메인 계층
  framework 금지/어댑터 역참조 금지 규칙 정본.
- `docs/php-test-bootstrap.md` — 파일을 작성한 뒤 `composer install`과
  `php` CLI로 어떻게 실행/검증하는지.
- `php/README.md`, `php/tests/README.md` — `php/` 트리 구조와 파일별
  설명.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 0423(정적 분석
  계획), 0424(도메인 framework 금지 규칙) 등 관련 후속 태스크 목록.
