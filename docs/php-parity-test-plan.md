# PHP Parity Test Plan

이 문서는 Python 구현과 PHP 구현이 같은 fixture 를 입력했을 때 같은
결과를 내는지 검증하는 **parity 테스트**를 어떻게 계획·조직하는지
고정한다. Phase A: PHP Replacement Contract, 0351-0390 의 산출물이다.

`docs/php-replacement-strategy.md` 의 readiness gate 3번째 조건("모듈의
핵심 동작이 언어 독립 JSON fixture 로 커버되어, Python 과 PHP 양쪽
러너가 같은 입력에 같은 출력을 내는지 검증할 수 있다")과 완료 기준
("PHP 구현이 위 fixture 전부에 대해 Python 구현과 동일한 결과를
내고(parity test, 0387) ...")이 이 문서가 계획하는 대상이다. 이 문서는
계획만 고정하며, 실제 PHP 쪽 러너 구현은 이후 태스크(0406, 0407, 0425,
0426-0429)의 범위다 — 이 태스크 시점에는 `php/` 트리 자체가 아직
존재하지 않는다.

## 핵심 원칙: 같은 fixture 파일을 두 런타임이 그대로 공유한다

Python 쪽과 PHP 쪽 parity 테스트는 fixture 파일을 복사하거나 각자
재작성하지 않고, `docs/fixture-directory-convention.md` 가 고정한
같은 경로(`tests/modules/<module>/fixtures/`, `tests/fixtures/`)의
같은 파일을 그대로 읽는다.

- fixture 는 `docs/cross-language-fixture-schema.md` 가 정한
  `schema_version`/`input`/`expected`/`errors` 구조를 따르는 JSON
  이므로, Python `json` 표준 라이브러리와 PHP `json_decode` 양쪽 모두
  추가 변환 없이 읽을 수 있다.
- 새 fixture 를 추가하거나 기존 fixture 를 고칠 때는 한 곳(위 경로)만
  고치면 되고, Python/PHP 러너가 다음 실행에서 자동으로 같은 파일을
  집는다. 언어별로 별도 fixture 사본을 만드는 것은
  `docs/portability-glossary.md` 의 Fixture 정의("언어별로 별도의
  fixture 를 만들지 않는다")를 어기는 것이므로 금지한다.
- fixture 파일의 정본(source of truth)은 저장소이지, 어느 한 언어의
  테스트 디렉터리가 아니다. PHP 러너가 위치할 `php/tests/` 아래에는
  fixture 사본을 두지 않고, 저장소 루트 기준 상대 경로로 Python 쪽과
  동일한 `tests/modules/<module>/fixtures/`, `tests/fixtures/` 를
  참조한다.

## Python 쪽 실행 방식 (이미 존재)

Python 쪽 fixture 러너는 이미 이 저장소에 있으며, 이후 PHP 러너가
따라야 할 기준 패턴이다. 예: `tests/modules/document/test_title_fixtures.py`,
`tests/modules/acl/test_decision_code_fixtures.py`.

각 모듈의 fixture 러너 테스트는 다음 순서를 따른다.

1. `src/modules/<module>/manifest.json` 의 `fixtures.path`/`fixtures.format`
   이 실제 fixture 디렉터리와 일치하는지 확인한다.
2. 해당 디렉터리의 `*.json` 파일을 모두 모아 `pytest.mark.parametrize`
   로 파일 하나당 테스트 케이스 하나를 만든다 — 파일 이름(`.stem`)을
   테스트 id 로 써서 실패 시 어느 fixture 가 깨졌는지 바로 알 수 있게
   한다.
3. fixture 하나마다 먼저 `tests/fixtures/schema/cross_language_fixture.schema.json`
   으로 구조를 검증한 뒤, `input` 을 manifest 의 `service.public_methods`
   에 나열된 실제 공개 메서드에 그대로 전달한다.
4. `errors` 가 빈 배열이면 반환값을 `expected` 와 비교하고, `errors`
   가 비어 있지 않으면 실행이 예외를 던지는지, 그 예외의 `code` 속성이
   `errors` 목록과 일치하는지 확인한다(`docs/portable-exception-code-policy.md`
   의 code 비교 원칙 — 메시지 문자열이 아니라 code 로만 비교).

## PHP 쪽 실행 방식 (계획, 0406/0407/0425 이후 구현)

PHP 쪽 러너는 Python 쪽과 같은 4단계를 PHP 관용구로 반복한다. 이
문서는 그 구조만 계획하며, 실제 코드는 아래에 표시한 태스크가 만든다.

1. **공유 fixture 로더** (0425, Add PHP shared fixture loader) — 저장소
   루트 기준 `tests/modules/<module>/fixtures/`, `tests/fixtures/` 를
   읽어 JSON 을 PHP 배열/객체로 디코드하는 공용 헬퍼를 `php/tests/`
   아래 둔다. Python 쪽 4개 테스트 파일이 각자 `_load_json` 을 반복
   정의하는 것과 달리, PHP 쪽은 이 로더 하나를 모든 모듈 러너가
   재사용한다.
2. **모듈별 parity 테스트** (0426 document, 0427 acl, 0428 parser
   placeholder, 0429 render placeholder 등) — 모듈마다 fixture
   디렉터리의 파일 수만큼 테스트 케이스를 만들고, 파일 이름을 테스트
   설명에 넣어 실패 위치를 바로 알 수 있게 한다. Python 쪽 parametrize
   패턴과 동등한 것을 PHP 테스트 프레임워크의 data provider 기능으로
   구현한다.
3. **입력 실행과 비교** — `input` 을 PHP 로 포팅된 서비스의 같은 이름
   공개 메서드(`docs/php-namespace-mapping.md` 가 고정한
   `MintWiki\<Module>\Service` 아래)에 전달한다. `errors` 가 빈
   배열이면 반환값을 `expected` 와 비교하고, 비어 있지 않으면 예외의
   `CODE` 상수(또는 동등한 접근자)가 `errors` 목록과 일치하는지
   확인한다. Python 쪽과 마찬가지로 예외 메시지 문자열은 비교하지
   않는다.
4. **아직 포팅되지 않은 모듈의 처리** — 해당 모듈 manifest 의
   `port.status` 가 `ready` 가 아니면, parity 테스트는 실패로
   기록하지 않고 명시적으로 skip 하거나 "PHP 구현 없음" 을 이유로 든
   expected-failure 로 표시한다(0428/0429 가 이 placeholder 정책을
   문서화한다). 이 문서는 그 표시 방식 자체(skip vs expected-failure
   문법)를 확정하지 않으며, 0428/0429 가 채택한 PHP 테스트
   프레임워크의 관용구를 따른다 — 다만 "포팅 전 모듈은 parity 실패로
   집계하지 않는다"는 원칙만 여기서 고정한다.

## Parity 판정 기준

한 모듈이 parity 를 만족한다고 판단하려면 다음이 모두 성립해야 한다.

- 그 모듈의 fixture 디렉터리에 있는 **모든** `*.json` 파일에 대해
  Python 러너와 PHP 러너가 각각 통과한다. 일부만 통과하는 상태는
  parity 로 보지 않는다.
- 두 러너가 같은 fixture 파일(사본이 아니라 동일 경로의 동일 파일)을
  읽었다는 것이 보장된다 — 위 "핵심 원칙" 절이 이를 구조적으로
  강제한다.
- 실패 케이스(`errors` 가 비어 있지 않은 fixture)에서 두 언어가 반환한
  error code 문자열이 정확히 일치한다. code 형식은
  `docs/portable-exception-code-policy.md` 가 고정한
  `<module>.<reason>` 이다.
- `docs/php-replacement-strategy.md` readiness gate 의 나머지
  4개 조건(manifest 검증 통과, 경계 검사 통과, error code 상수화,
  PostgreSQL 전용 기능 미의존)도 함께 성립한다 — parity fixture 통과는
  readiness 의 필요조건 중 하나일 뿐, 그것만으로 전환 완료를 뜻하지
  않는다.

이 판정 결과는 이후 태스크가 만들 "PHP 전환 준비 체크리스트"(0388,
Add PHP replacement readiness checklist)의 모듈별 ready/not-ready
판단과, "PHP 모듈 교체 matrix"(0433, Add PHP module replacement matrix)
의 parity 상태 컬럼이 참조하는 근거 자료가 된다. 두 문서의 실제 파일
이름은 이 문서가 고정하지 않는다.

## 실행 방법 (계획)

- Python 쪽은 이미 `scripts/test.sh`(`pytest`)로 전체 fixture 러너를
  포함해 실행된다. 이 태스크는 그 스크립트를 바꾸지 않는다.
- PHP 쪽 러너가 생기면(0406 이후), PHP 전용 테스트 실행 스크립트(예:
  `php/scripts/test.sh` 또는 동등한 위치, 실제 이름은 PHP 골격을
  만드는 태스크가 정한다)로 별도 실행한다. 이 문서는 Python 쪽
  `scripts/test.sh`/`scripts/qa.sh` 에 PHP 실행을 강제로 끼워 넣지
  않는다 — Phase A/B 동안 두 런타임은 같은 CI 파이프라인 안에서도
  독립된 단계로 실행된다고 가정한다(`docs/php-replacement-strategy.md`
  의 "PHP 런타임이 Python 프로세스를 호출하거나 Python 런타임에
  의존하지 않는다" 원칙과 같은 이유).
- 두 런타임을 하나의 명령으로 함께 실행하는 통합 스크립트를 만들지
  여부와 그 형태는 이 문서의 범위가 아니다 — 필요해지면 별도 태스크가
  정한다.

## 이 문서가 하지 않는 것

- PHP fixture 로더나 모듈별 parity 테스트의 실제 코드를 작성하지
  않는다(0406, 0407, 0425-0429 의 범위).
- `php/` 디렉터리나 PHP 테스트 프레임워크(선택지, 설정 파일)를 만들지
  않는다.
- readiness checklist(0388)와 module replacement matrix(0433) 문서
  자체를 작성하지 않는다 — 이 문서는 그 두 문서가 참조할 parity 판정
  기준만 고정한다.
- 개별 모듈의 실제 fixture 내용을 추가하거나 바꾸지 않는다.

## 관련 문서

- `docs/php-replacement-strategy.md` — readiness gate 와 전환 완료
  기준(parity test 요구사항의 배경).
- `docs/portability-glossary.md` — Fixture/Port/Contract 용어 정의.
- `docs/fixture-directory-convention.md` — fixture 파일 위치 규칙.
- `docs/cross-language-fixture-schema.md` — fixture JSON 구조.
- `docs/portable-exception-code-policy.md` — error code 형식과 비교
  방식.
- `docs/php-namespace-mapping.md` — PHP 쪽에서 parity 테스트가 호출할
  서비스 클래스의 namespace 규칙.
- `docs/module-contract-manifest-schema.md` — `fixtures.path`/`format`,
  `service.public_methods`, `port.status` 필드.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — PHP 러너를 실제로
  구현하는 이후 태스크(0406, 0407, 0425-0429, 0433) 목록.
