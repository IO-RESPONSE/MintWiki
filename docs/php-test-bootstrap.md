# PHP Test Bootstrap

이 문서는 `php/tests/` 아래 테스트를 어떻게 실행 준비(bootstrap)하고
돌리는지, 그리고 테스트 프레임워크로 composer 의존성(PHPUnit 등)을
언제 도입할지 판단 기준을 고정한다. Phase B: PHP Runtime Skeleton,
0391-0440 의 산출물이다(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).

## 현재 상태: 외부 테스트 프레임워크 없음

`php/tests/` 아래 테스트는 전부 PHPUnit 등 외부 프레임워크 없이 `php`
CLI만으로 실행되는 평범한 PHP 스크립트다(`php/tests/AutoloadSmokeTest.php`가
이 패턴의 첫 사례). 각 파일은:

- 실행에 필요한 클래스를 `vendor/autoload.php`를 통해 로드하고,
- 조건을 직접 `if`/`fwrite(STDERR, ...)`/`exit(1)`로 검사하며,
- 실패가 없으면 `exit(0)`과 함께 통과 메시지를 출력한다.

`php/composer.json`은 `require`에 `php: ^8.1` 엔진 제약만 선언하고
`require-dev`에 PHPUnit 등 패키지를 추가하지 않는다(0392,
"shared hosting 대응을 위해 의존성은 최소화한다"). 그 결과
`composer install`은 네트워크 접근 없이 끝나고, `vendor/autoload.php`는
PSR-4 오토로드 설정만 등록한다.

## Bootstrap 절차

1. `php/` 디렉터리로 이동한다.
2. `composer install`을 실행한다 — `composer.json`에 패키지 의존성이
   없으므로 네트워크 접근 없이 `vendor/`를 생성한다.
3. 개별 테스트 파일을 `php` CLI로 직접 실행한다. 예:
   `php tests/AutoloadSmokeTest.php`, `php tests/Http/ResponseTest.php`.
   각 파일이 정확히 어떤 것을 검증하는지, 실행 명령이 무엇인지는
   `php/tests/README.md`가 파일별로 기록한다.
4. 모든 테스트 파일이 `exit(0)`으로 끝나면 통과, 하나라도 `exit(1)`이면
   실패다 — 셸에서 `$?`로 확인한다.

테스트 파일 전체를 한 번에 순회해 실행하는 통합 스크립트(예:
`php/scripts/test.sh`)는 이 태스크의 범위가 아니다 — PHP 런타임 QA
스크립트 골격을 만드는 0430(Add PHP runtime QA command script)이
담당한다. 그때까지는 위 3단계를 테스트 파일마다 반복하거나, 저장소
루트에서 `find php/tests -name '*Test.php' -exec php {} \;`처럼
임시 셸 명령으로 순회한다.

## composer/phpunit 선택 기준

"테스트를 어떻게 짤 것인가"는 프레임워크 없이 시작해서, 아래 조건 중
하나라도 뚜렷해지면 PHPUnit(또는 동등한 composer 의존 프레임워크)
도입을 재검토하는 순서를 따른다. 조건이 없는 동안은 현재 방식(외부
의존성 없는 스크립트)을 유지한다.

### 프레임워크 없이 유지하는 이유 (현재)

- **shared hosting 제약**: 0392가 못박은 "의존성 최소화"는 배포
  대상이 `composer install --no-dev`조차 못 돌리거나 vendor 용량에
  민감한 shared hosting을 포함하기 때문이다(`docs/php-replacement-strategy.md`).
  PHPUnit은 `require-dev`로 격리할 수 있지만, 도입 자체가 "테스트를
  돌리려면 composer 의존성이 하나 더 필요하다"는 문턱을 만든다.
- **네트워크 없는 설치 보장**: `docs/php-db-ui-micro-job-prompts-0351-0670.md`가
  반복해서 요구하는 "네트워크 의존 없이 실행"은 `composer.json`에
  패키지가 전혀 없을 때 가장 단순하게 성립한다. PHPUnit을 추가하면
  최초 `composer install` 시점의 네트워크 접근(또는 vendor 사전 커밋)
  문제를 다시 풀어야 한다.
- **테스트 수와 복잡도가 아직 작다**: 지금까지의 테스트는 값 객체
  생성자/불변 조건 확인이 대부분이라, data provider나 공유 assertion
  헬퍼 없이도 파일당 몇 줄의 `if`로 충분하다.

### PHPUnit(또는 동등 프레임워크) 도입을 검토할 조건

아래 중 하나라도 실제로 발생하면, 그 시점의 태스크가 도입 여부를
다시 판단한다 — 이 문서는 지금 당장 도입을 지시하지 않는다.

- **data provider가 반복적으로 필요해질 때**: fixture 파일 하나당
  케이스 하나를 만드는 패턴(`php/tests/Modules/Parser/FixtureRunnerTest.php`,
  `php/tests/Modules/Render/FixtureRunnerTest.php`)이 모듈마다
  손으로 반복하는 `foreach` 루프로는 감당이 안 될 만큼 늘어날 때.
  PHPUnit의 `#[DataProvider]`가 이 중복을 줄인다.
- **실패 리포트 집계가 필요해질 때**: 테스트 파일이 많아져 "몇 개 중
  몇 개 통과"를 사람이 셸 출력으로 셀 수 없는 수준이 되면, JUnit XML 등
  CI가 파싱할 수 있는 표준 출력 형식이 필요해진다.
- **assertion 헬퍼 중복이 파일마다 쌓일 때**: `assertSame`/`assertTrue`
  류를 각 테스트 파일이 직접 재구현하는 대신 공유 라이브러리가 필요할
  때.
- **shared hosting 제약이 실제로 완화될 때**: 배포 대상이
  `composer install`(네트워크 포함) 또는 CI에서만 생성한 `vendor/`를
  배포 아티팩트에 포함하는 방식으로 바뀌어, 0392의 "의존성 최소화"
  전제가 더 이상 유효하지 않을 때.

이 네 조건 중 하나라도 성립해 PHPUnit 도입을 결정하면, 그 도입은
`php/composer.json`의 `require-dev`에만 추가하고(런타임 `require`는
그대로 최소 유지), 기존 테스트 파일을 한 번에 옮기지 않고 신규
테스트부터 점진적으로 전환하는 것을 기본값으로 한다 — 전체 재작성
전략의 수립은 이 문서의 범위가 아니다.

## 이 문서가 하지 않는 것

- `php/scripts/test.sh` 등 통합 테스트 실행 스크립트를 만들지
  않는다(0430의 범위).
- PHPUnit 등 실제 composer 의존 프레임워크를 지금 도입하지
  않는다 — 위 조건이 성립할 때 재검토한다.
- `scripts/qa.sh`에 PHP QA를 선택 실행으로 연결하지 않는다(0431의
  범위).
- 개별 테스트 파일의 검증 내용을 바꾸지 않는다 — `php/tests/README.md`가
  파일별 내용의 정본이다.

## 관련 문서

- `docs/php-replacement-strategy.md` — shared hosting 제약과 readiness
  gate의 배경.
- `docs/php-parity-test-plan.md` — fixture 기반 parity 테스트가 이
  bootstrap 절차 위에서 어떻게 실행되는지.
- `php/README.md`, `php/tests/README.md` — `php/` 트리 구조와 테스트
  파일별 상세 설명.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 0392(composer
  manifest), 0430(QA 스크립트), 0431(루트 QA 훅) 등 관련 태스크 목록.
