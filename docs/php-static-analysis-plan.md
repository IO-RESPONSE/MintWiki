# PHP Static Analysis Plan

이 문서는 `php/` 트리에 정적 분석 도구(PHPStan 또는 Psalm)를 언제,
어떤 기준으로 도입할지 계획만 고정한다. Phase B: PHP Runtime Skeleton,
0391-0440 의 산출물이다(`docs/php-db-ui-micro-job-prompts-0351-0670.md`).
**도구 자체의 도입(composer 의존성 추가, 설정 파일 작성, CI/QA 연결)은
이 문서의 범위가 아니다** — 후속 잡이 이 계획을 근거로 실행한다.

## 현재 상태: 정적 분석 도구 없음

`php/composer.json`의 `require`에는 `php: ^8.1` 엔진 제약만 있고,
`require-dev`는 아직 존재하지 않는다(0392, "shared hosting 대응을 위해
의존성은 최소화한다"). 지금까지의 타입 안전성은 아래 두 관행으로만
확보된다.

- 모든 파일이 `declare(strict_types=1)`을 선언한다
  (`docs/php-coding-standard.md`).
- 값 객체가 생성자 프로퍼티 승격과 `readonly`, 타입 힌트가 있는
  프로퍼티/파라미터/리턴 타입을 기본으로 쓴다.

이 두 관행은 런타임 타입 강제와 가독성은 보장하지만, `composer install`
없이는 실행되지 않는 죽은 코드 경로, null 가능성 누락, 존재하지 않는
메서드 호출 같은 정적 결함은 잡지 못한다. 이 문서는 그 간극을 메울
도구를 "언제" 들일지 판단 기준을 미리 정해 둔다.

## 도구 후보: PHPStan vs Psalm

두 도구 모두 composer `require-dev` 패키지로 배포되고 shared hosting
운영 환경(`php/public/`, 실제 배포 대상)에는 전혀 배치되지 않는다 —
개발자 워크스테이션과 CI에서만 실행되는 도구이므로, 0392가 못박은
"런타임 의존성 최소화" 원칙과 충돌하지 않는다(`require-dev`는 배포
아티팩트에서 제외 가능).

- **PHPStan**: 기본 채택 후보로 둔다. 규칙 레벨(0~9 정수, 레벨이
  높을수록 엄격)을 점진적으로 올릴 수 있어, 프로젝트 초기에는 낮은
  레벨로 시작해 코드베이스가 자라면서 레벨을 올리는 전략과 잘 맞는다.
  `docs/php-coding-standard.md`가 이미 강제하는 `final class`,
  `readonly`, PSR-4/classmap 규칙과 충돌 없이 동작한다.
- **Psalm**: 대안으로만 기록한다. 타입 추론이 더 정교하고 `@psalm-*`
  어노테이션으로 세밀한 타입 표현이 가능하지만, 이 저장소의 코드베이스
  규모(값 객체와 인터페이스 중심, 복잡한 제네릭 타입 없음)에서는
  PHPStan 대비 이점이 크지 않다.
- 실제 도입 시점의 잡이 두 도구 중 하나를 최종 선택한다. 이 문서는
  PHPStan을 기본값으로 권고하되, 그 시점에 PHP 생태계 상황이 바뀌었다면
  재검토를 막지 않는다.

## 도입 트리거 조건

`docs/php-test-bootstrap.md`가 PHPUnit 도입 조건을 미리 정해 둔 것과
같은 방식으로, 아래 조건 중 하나라도 실제로 발생하면 그 시점의 태스크가
도구 도입 여부를 재판단한다. 조건이 없는 동안은 지금처럼 도구 없이
`docs/php-coding-standard.md`의 관행만으로 유지한다.

- **모듈 수가 늘어 수동 리뷰로 타입 불일치를 못 잡을 때**: 현재
  12개 모듈(`docs/modules.md`) 각각의 PHP 이식이 끝나갈 무렵, 모듈 간
  interface 구현체가 늘어나 사람이 코드 리뷰만으로 시그니처 불일치를
  잡기 어려워지는 시점.
- **`docs/php-namespace-mapping.md`/classmap 예외 관련 회귀가 실제로
  발생했을 때**: `src/Modules/` classmap 예외(`docs/php-coding-standard.md`
  PSR-4 오토로딩 규칙 절 참조)로 인한 클래스 미발견 같은 문제가 정적
  분석 없이 런타임에서야 드러난 사례가 한 번이라도 생기면.
- **0424(PHP 도메인 framework 금지 규칙)가 코드 검사 자동화를 요구할
  때**: `scripts/check_boundaries.py`, `scripts/check_no_app_import_in_modules.py`와
  동등한 PHP 쪽 경계 검사를 만드는 시점에, 그 검사를 정적 분석 도구의
  커스텀 규칙으로 구현할지 별도 스크립트로 구현할지 판단이 필요해진다
  — 이때 정적 분석 도구 도입 여부도 함께 재검토한다.
- **CI에서 PHP QA가 실행되기 시작할 때**: 0430(PHP QA 스크립트),
  0431(루트 QA 훅 연결) 이후 `php/` 코드가 실제로 CI 파이프라인에서
  검증되기 시작하면, 그 파이프라인에 정적 분석 단계를 추가할지 결정할
  자연스러운 지점이 생긴다.

## 도입 시 지켜야 할 원칙 (실행할 때 참고)

실제 도입 잡이 진행될 때 아래 원칙을 따른다 — 지금 이 문서가 코드를
바꾸지는 않는다.

- `php/composer.json`의 `require-dev`에만 추가한다. 런타임 `require`는
  `php: ^8.1` 하나로 최소 유지한다(`docs/php-test-bootstrap.md`가 같은
  원칙을 PHPUnit에 대해 이미 적용).
- 설정 파일(`phpstan.neon` 등)은 `php/` 디렉터리 루트에 두고, 분석
  대상은 `src/`로 한정한다 — `vendor/`, `tests/`의 픽스처 데이터는
  제외한다.
- 레벨/엄격도는 낮은 단계에서 시작해 기존 코드가 통과하는 선에서
  점진적으로 올린다. 도입 첫 커밋에서 전체 코드베이스를 한 번에 최고
  레벨로 통과시키려 하지 않는다.
- `scripts/qa.sh`에 자동 연결하는 것은 0431(Add manifest validation to
  QA류 후속 PHP QA 연결 잡)의 판단에 맡긴다 — 이 문서는 연결 여부를
  미리 정하지 않는다.

## 이 문서가 하지 않는 것

- PHPStan/Psalm을 실제로 설치하거나 설정 파일을 작성하지 않는다 — 위
  트리거 조건이 성립할 때 별도 잡이 수행한다.
- `php/composer.json`을 수정하지 않는다.
- `scripts/qa.sh`, `scripts/test.sh`에 PHP 정적 분석 실행 단계를
  추가하지 않는다.
- 0424(PHP 도메인 framework 금지 규칙)가 다루는 도메인 경계 검사
  규칙 자체를 정의하지 않는다 — 그 규칙을 정적 분석 도구로 구현할지
  여부만 위 트리거 조건에서 언급한다.

## 관련 문서

- `docs/php-coding-standard.md` — 현재 타입 안전성을 지탱하는
  `strict_types`, `final class`, `readonly` 관행.
- `docs/php-test-bootstrap.md` — PHPUnit 등 테스트 프레임워크 도입 여부를
  같은 방식(트리거 조건 목록)으로 판단하는 선례.
- `docs/php-replacement-strategy.md` — shared hosting 배포 제약과
  `require-dev` 의존성이 런타임에 영향을 주지 않는 이유.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — 0424(도메인
  framework 금지 규칙), 0430(PHP QA 스크립트), 0431(루트 QA 훅 연결) 등
  관련 후속 태스크 목록.
- `docs/php-no-framework-domain-rule.md` — 0424가 정의하는 도메인 계층
  framework 금지 규칙 정본. 이 규칙을 자동 검사로 구현할지는 위 도입
  트리거 조건에서 판단한다.
