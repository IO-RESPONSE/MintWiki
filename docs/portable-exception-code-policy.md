# Portable Exception Code Policy

이 문서는 `docs/php-replacement-strategy.md` 의 금지할 결합 항목 —
"예외 메시지 문자열 비교로 에러 종류를 식별하는 것" — 을 지키기 위한 안정적인
error code 정책을 고정한다. Phase A: PHP Replacement Contract, 0351-0390 의
산출물이다.

`docs/cross-language-fixture-schema.md` 의 `errors` 필드는 이미 fixture 가
error code 목록(예: `document.empty_title`)을 담는다고 정했다. 이 문서는 그
code 가 어떤 형식을 따르고, 어디에 선언되며, Python 예외 클래스가 그 code 를
어떻게 실어 나르는지를 고정한다. 개별 모듈의 실제 code 목록은 이후 태스크
(0374 Add document error codes 등)가 채운다.

## 왜 메시지 대신 code 인가

- 예외 메시지 문자열(`Exception.args[0]` 등)은 사람이 읽기 위한 설명이며,
  로케일이나 표현을 바꿔도 되는 대상이다. 메시지를 바꾸는 리팩터링이 에러
  식별 로직까지 깨뜨리면 메시지와 로직이 부당하게 결합된 것이다.
- Python 예외 클래스 이름(`DocumentNotFoundError` 등)과 PHP 예외 클래스
  이름은 언어별 네이밍 관용이 달라 1:1로 맞추기 어렵다. 반면 문자열 code 는
  두 언어가 동일한 값을 그대로 공유할 수 있다.
- fixture(`errors` 필드)와 parity 테스트(0387)는 Python/PHP 양쪽 결과를
  code 값으로만 비교한다. 클래스 이름이나 메시지로 비교하지 않는다.

## Code 형식

Error code 는 `<module>.<reason>` 형식의 소문자 snake_case 문자열이다.

- `<module>` 은 `src/modules/<module>` 디렉터리 이름과 정확히 일치한다
  (`document`, `revision`, `parser`, `render`, `user`, `acl`, `discussion`,
  `cache`, `jobs`, `audit`, `admin`, `search` 등 `docs/modules.md` 가 정의한
  모듈 이름).
- `<reason>` 은 실패 조건을 설명하는 snake_case 단어(들)이며, 예외가
  발생한 내부 구현(어느 함수, 어느 줄)이 아니라 **호출자가 구분해야 하는
  실패 의미**를 가리킨다. 예: `not_found`, `empty_title`,
  `duplicate_title`.
- 구분자는 모듈과 reason 사이의 점(`.`) 하나뿐이다. reason 내부에서 여러
  단어를 이을 때는 밑줄(`_`)을 쓴다. 하이픈, 카멜케이스, 추가 점은 쓰지
  않는다.
- 예시: `document.empty_title`, `document.duplicate_title`,
  `document.not_found`.

## Code 는 어디에 선언하는가

- Python: 각 모듈의 예외 클래스(`repository.py`, `title.py` 등에 정의된
  `Exception` 서브클래스)는 클래스 속성 `code` 로 안정 문자열을 노출한다.
  `code` 값은 클래스 정의부에서 리터럴로 고정하며, 메시지 문자열이나
  다른 런타임 값으로부터 조립하지 않는다.

  ```python
  class DocumentNotFoundError(Exception):
      """문서를 찾을 수 없을 때 발생하는 예외."""

      code = "document.not_found"
  ```

- PHP: 대응하는 예외 클래스는 같은 문자열을 반환하는 상수 또는 메서드
  (예: `const CODE = 'document.not_found';`)로 동일한 code 를 노출한다.
  실제 PHP 예외 클래스 골격은 `docs/php-namespace-mapping.md` 가 정한
  namespace 규칙을 따르며, 도입은 0416(PHP error code registry)이 맡는다.
  Python 클래스 이름과 PHP 클래스 이름이 문자 그대로 같을 필요는 없다 —
  두 언어가 반드시 같아야 하는 값은 `code` 문자열 하나뿐이다.
- 예외 클래스 이름 자체(`DocumentNotFoundError` 같은 PascalCase 이름)는
  code 와 별개로 자유롭게 짓는다. 다만 code 의 `<reason>` 부분과 의미가
  어긋나지 않게 한다(클래스 이름에서 code 를 유추할 수 있어야 리뷰가
  쉽다).

## Code 소유권과 유일성

- 하나의 실패 조건에는 정확히 하나의 code 를 부여한다. 같은 조건을 두
  code 로 나누거나, 서로 다른 조건이 같은 code 를 공유하지 않는다.
- code 의 `<module>` 접두사는 그 예외가 속한 모듈이 소유한다. 다른 모듈이
  같은 접두사로 code 를 추가하지 않는다 — 이는
  `docs/php-replacement-strategy.md` 의 모듈 경계 원칙과 같은 이유다.
- 모듈 하나가 같은 `<reason>` 을 여러 예외 클래스에서 재사용하지 않는다.
  클래스와 code 는 1:1로 대응한다.

## 안정성(하위 호환)

- 한 번 fixture(`errors` 필드)나 parity 테스트에 쓰인 code 문자열은 이후
  임의로 이름을 바꾸지 않는다. code 는 `docs/module-contract-manifest-schema.md`
  가 정의한 모듈 계약의 일부이며, 계약 변경은
  `docs/portability-glossary.md` 의 Contract 정의대로 관련된 모든 언어
  구현과 fixture 를 함께 갱신해야 한다.
- 실패 조건 자체가 없어져 예외 클래스를 제거하는 경우가 아니라면, code
  문자열을 재활용하거나 다른 조건에 재배정하지 않는다.
- 더 구체적인 실패 조건으로 나누고 싶을 때는 기존 code 를 바꾸는 대신
  새 code 를 추가하고, 기존 code 를 계속 쓰는 fixture 는 그대로 둔다.

## fixture 와의 연결

- `docs/cross-language-fixture-schema.md` 의 `errors` 배열에는 이 문서가
  정의한 형식의 code 문자열만 담는다. 예외 메시지, 클래스 이름, HTTP 상태
  코드 등 다른 표현은 담지 않는다.
- 실패 fixture 를 추가할 때는 대응하는 Python 예외 클래스에 `code` 속성이
  이미 선언되어 있어야 한다. `code` 없이 fixture 에 문자열만 새로 지어
  넣지 않는다 — 소스가 fixture 가 아니라 예외 클래스 정의여야 한다.

## 이 문서가 하지 않는 것

- 개별 모듈의 실제 code 목록을 정하지 않는다. `document` 모듈의 code 는
  0374(Add document error codes), 다른 모듈은 이후 순번의 태스크가
  담당한다.
- 기존 예외 클래스에 `code` 속성을 소급 추가하지 않는다. 이 문서는 정책만
  고정하며, 코드 변경은 이후 태스크의 범위다.
- PHP 쪽 실제 예외 클래스나 레지스트리를 구현하지 않는다(0416 Add PHP
  error code registry 의 범위).

## 관련 문서

- `docs/php-replacement-strategy.md` — 이 정책이 지키는 금지할 결합 원칙과
  readiness gate 조건 4번.
- `docs/cross-language-fixture-schema.md` — code 문자열을 담는 `errors`
  필드의 fixture 스키마.
- `docs/module-contract-manifest-schema.md` — code 가 속하는 모듈 계약의
  범위.
- `docs/portability-glossary.md` — Contract 용어 정의와 계약 변경 시
  동기화 원칙.
- `docs/php-namespace-mapping.md` — PHP 쪽 예외 클래스가 따라야 할
  namespace 규칙.
