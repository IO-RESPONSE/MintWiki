# PHP Runtime Phase (Phase B) QA Checklist

이 문서는 로드맵 **Phase B: PHP Runtime Skeleton, 0391-0440**
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`) 의 산출물이 회귀 없이
유지되고 있는지 확인하기 위한 체크리스트다. `docs/portability-phase-qa-checklist.md`
가 109-111행에서 "`php/` 트리가 생긴 뒤 이 문서를 확장하거나 별도 Phase B
QA 체크리스트를 추가하는 것은 이후 태스크의 범위다"라고 예고한 바로 그
후속 문서다. Phase B에 속한 `php/` 코드/스크립트/문서를 새로 추가·수정한
뒤, 또는 커밋 전 `scripts/qa.sh`와는 별개로 "PHP 런타임 골격이 계약대로
동작하는가"를 사람이 다시 훑어볼 때 사용한다.

`docs/portability-phase-qa-checklist.md`, `docs/acl-phase-qa-checklist.md`
와 동일한 형식을 따른다 — 각 항목은 "무엇을 확인하는가"와 "어떤 자동화가
이미 이를 커버하는가"를 함께 적는다. 자동화가 있다고 해서 항목을 건너뛰어도
된다는 뜻은 아니다.

이 체크리스트는 태스크 0439 Notes가 지정한 네 영역 — **parity, autoload,
health, module skeleton** — 을 절 단위로 다룬다.

## 사용법

```bash
cd php && composer install && cd -
php/scripts/qa.sh
.venv/bin/python -m pytest tests/test_php_qa_scripts.py tests/test_qa_script_php_hook.py -v
```

위 명령으로 아래 체크리스트가 참조하는 자동 검사를 한 번에 실행할 수
있다. 개별 실행 후에는 반드시 `scripts/test.sh`와 `scripts/qa.sh`도
통과해야 한다 — `php` CLI가 설치되어 있으면 `scripts/qa.sh`가
`php/scripts/qa.sh`를 선택 실행하므로(0431), `php` CLI가 있는 환경에서는
`scripts/qa.sh` 통과만으로 아래 1~4절 대부분이 사실상 자동으로
확인된다. `php` CLI가 없는 환경에서는 `scripts/qa.sh`가 PHP QA를 명확히
skip하므로, 이 체크리스트를 사람이 별도로 훑어봐야 한다.

## 1. Autoload

- [ ] `php/composer.json`이 PSR-4 오토로드로 `MintWiki\\` 접두사를
      `src/`에 매핑한다. See `php/tests/AutoloadSmokeTest.php`,
      `docs/php-namespace-mapping.md`.
- [ ] `composer install`이 네트워크 접근 없이 끝난다 —
      `php/composer.json`의 `require-dev`에 외부 패키지가 없다(0392
      "shared hosting 대응을 위해 의존성은 최소화한다"). See
      `docs/php-test-bootstrap.md`, `tests/test_php_qa_scripts.py`.
- [ ] `vendor/autoload.php`가 없는 상태에서 각 `*Test.php`를 실행하면
      안내 메시지와 함께 exit code 1로 끝난다(무음 실패 없음). See
      `php/tests/AutoloadSmokeTest.php`, `php/tests/Http/HealthRouteTest.php`.
- [ ] `php/scripts/test.sh`가 `php/tests/` 아래 모든 `*Test.php`를
      찾아 `php` CLI로 하나씩 실행하고, 파일별 `PASS`/`FAIL`과 전체
      통과 개수를 출력하며, 하나라도 실패하면 exit code 1로 끝난다. See
      `tests/test_php_qa_scripts.py`.

## 2. Health

- [ ] `public/index.php`가 등록하는 `/health` route가 기본값으로
      `{"status":"ok","app":"wiki-engine"}`를 `application/json`
      Content-Type과 status 200으로 반환한다. See
      `php/tests/Http/HealthRouteTest.php`.
- [ ] `WIKI_APP_NAME` 환경변수가 설정되어 있으면 `/health` 응답의
      `app` 필드가 그 값을 반영한다. See
      `php/tests/Http/HealthRouteTest.php`, `php/src/App/ConfigLoader.php`.
- [ ] `/health`가 등록되지 않은 method(`POST /health`)나 경로
      (`GET /other`)에는 매칭되지 않는다. See
      `php/tests/Http/HealthRouteTest.php`, `php/tests/Http/RouterTest.php`.
- [ ] `php -S`로 실제 HTTP 서버를 띄운 프론트 컨트롤러 레벨에서도
      `/health`가 같은 계약을 지킨다. See
      `tests/test_php_public_front_controller.py`.

## 3. Module skeleton

- [ ] `docs/modules.md` 기준 12개 모듈(`document`, `revision`, `parser`,
      `render`, `acl`, `discussion`, `search`, `cache`, `jobs`, `user`,
      `admin`, `audit`) 각각에 대응하는 `php/src/Modules/<Module>/`
      디렉터리가 존재한다. See `php/src/Modules/README.md`.
- [ ] 각 `php/src/Modules/<Module>/` 디렉터리 이름과 namespace가
      `docs/php-namespace-mapping.md`가 고정한 `MintWiki\<Module>` ↔
      Python `modules.<module>` 매핑과 1:1로 대응한다 — 누락되거나
      이름이 어긋난 모듈이 없다.
- [ ] 골격 단계를 넘어 실제 값 객체/포트/서비스가 추가된 모듈
      (`Document`, `Revision`, `Acl`, `User`, `Discussion`, `Cache`,
      `Jobs`, `Audit`, `Admin`)은 각각 대응하는 `php/tests/Modules/<Module>/`
      테스트 디렉터리를 갖는다. See `php/tests/Modules/*/*.php`.
- [ ] `php/src/App`(`ConfigLoader`, `ErrorCodeRegistry`)와
      `php/src/Http`(`Request`, `Response`, `Router`)가 도메인
      모듈(`php/src/Modules/**`)을 import하지 않는다 — 골격 단계에서도
      계층 방향이 뒤집히지 않는다. See `docs/php-no-framework-domain-rule.md`.
- [ ] 모듈별 PHP 구현 상태(`not-started`/`partial`/`parity`/`pass`)가
      `docs/php-module-replacement-matrix.md`에 최신으로 기록되어
      있다 — 이 체크리스트가 새 클래스/테스트를 추가시키면 그 문서도
      함께 갱신한다.

## 4. Parity

- [ ] `php/tests/Support/FixtureLoader.php`가
      `tests/modules/<module>/fixtures/`와 `tests/fixtures/`
      (`docs/fixture-directory-convention.md`) 아래 교차언어 JSON
      fixture를 읽고, `docs/cross-language-fixture-schema.md`가 고정한
      `schema_version`/`input`/`expected`/`errors` 구조를 검증한다. See
      `php/tests/Support/FixtureLoaderTest.php`.
- [ ] document title 정규화 fixture와 ACL decision code fixture는 PHP
      러너가 Python 러너와 같은 fixture 파일을 그대로 읽어 같은 결과를
      낸다(parity 판정 기준, `docs/php-parity-test-plan.md`). See
      `php/tests/Modules/Document/TitleFixtureRunnerTest.php`,
      `php/tests/Modules/Acl/DecisionCodeFixtureRunnerTest.php`.
- [ ] `DocumentService::create()`/`get()`이 Python
      `test_service.py::TestDocumentService`와 같은 시나리오(빈 title
      예외, 중복 제목 예외, id 발급, `normalizedTitle`/`currentRevisionId`
      필드)에서 같은 결과를 낸다. See
      `php/tests/Modules/Document/ServiceParityTest.php`.
- [ ] 문서 생성 시 `source`가 첫 리비전으로 연결되는 통합 시나리오가
      in-memory document/revision repository로 검증된다. See
      `php/tests/Modules/Document/RevisionIntegrationTest.php`,
      `php/src/Modules/Document/InMemoryRepository.php`,
      `php/src/Modules/Revision/InMemoryRepository.php`.
- [ ] 아직 포팅되지 않은 `parser`/`render` 모듈은 실제 parity 비교
      대신 expected-failure placeholder 정책(가드 + 미래 클래스
      부재 확인 + fixture 무결성 검증 3단계)을 따른다 — 포트가
      `ready`로 바뀌기 전까지는 이 정책 위반(예: 조용히 스킵되는 테스트)
      이 없어야 한다. See
      `php/tests/Modules/Parser/ParityPlaceholderTest.php`,
      `php/tests/Modules/Render/ParityPlaceholderTest.php`,
      `docs/php-parity-test-plan.md`.
- [ ] 위반이 있으면 `php/scripts/test.sh`가 파일별 `FAIL`과 실패
      원인을 stderr로 출력하고 exit code 1로 끝나며, `php` CLI가 있는
      환경에서는 `scripts/qa.sh` 전체가 실패한다.

## 이 체크리스트가 다루지 않는 것

- Phase A(PHP Replacement Contract, 0351-0390) 산출물의 무결성 —
  `docs/portability-phase-qa-checklist.md`가 담당한다.
- 모듈별 최신 ready/not-ready 판정 갱신 — `docs/php-module-replacement-matrix.md`
  와 `docs/php-replacement-readiness-checklist.md`의 역할이며, 이
  체크리스트는 Phase B 골격 산출물 자체가 계약대로 존재/동작하는지만
  확인한다.
- DB 단계로 넘어가기 전 완료 조건의 최종 판정 — 0440(Add PHP replacement
  readiness gate)이 별도 gate 문서로 다룬다.
- 실제 배포 환경(shared hosting/Docker)에서의 성능/부하 특성 —
  `docs/php-runtime-docker-note.md`가 다루는 실행 환경 차이와는 별개로,
  이 체크리스트는 기능적 정확성과 계약 정합성만 다룬다.

## 관련 문서

- `docs/portability-phase-qa-checklist.md` — Phase A QA 체크리스트,
  이 문서가 형식을 따르고 후속으로 이어받은 선행 문서.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase B(0391-0440)
  전체 태스크 목록.
- `docs/php-test-bootstrap.md` — autoload/health 절이 참조하는 테스트
  실행 방식의 원본 문서.
- `docs/php-namespace-mapping.md`, `docs/php-no-framework-domain-rule.md`
  — module skeleton 절이 참조하는 namespace/경계 규칙.
- `docs/php-parity-test-plan.md`, `docs/php-module-replacement-matrix.md`,
  `docs/php-replacement-readiness-checklist.md` — parity 판정 기준과
  모듈별 상태의 원본 문서.
- `php/scripts/README.md` — `php/scripts/test.sh`/`qa.sh`의 동작 상세.
