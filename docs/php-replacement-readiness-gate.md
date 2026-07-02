# PHP Replacement Readiness Gate

이 문서는 로드맵 **Phase B: PHP Runtime Skeleton, 0391-0440**
(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)을 마치고 **Phase C:
ANSI SQL and MariaDB Portable DB Layer, 0441-0520**로 넘어가기 전 만족해야
하는 완료 조건을 하나의 gate로 고정한다. `docs/php-runtime-phase-qa-checklist.md`
가 135-136행에서 "DB 단계로 넘어가기 전 완료 조건의 최종 판정 —
0440(Add PHP replacement readiness gate)이 별도 gate 문서로 다룬다"라고
미리 가리킨 바로 그 문서다.

## 이 gate 가 판정하지 않는 것 (범위 구분)

Phase B/C 기간에는 이미 세 개의 문서가 각자 다른 질문에 답하고 있다. 이
gate 문서는 그 위에서 "Phase C 를 시작해도 되는가"라는 **하나의
예/아니오 질문**에만 답한다 — 아래 질문들을 다시 판정하지 않는다.

- **"이 모듈이 Python 에서 PHP 로 전환할 준비가 되었는가?"** —
  `docs/php-replacement-readiness-checklist.md`(0388)의 5-gate 판정.
  `docs/php-replacement-strategy.md`가 이미 명시하듯 Phase A/B 기간에는
  구조적으로 모든 모듈이 not-ready이며, 이 gate는 그 사실을 바꾸지
  않는다.
- **"각 모듈의 PHP 구현 진행 단계는 어디까지 왔는가?"** —
  `docs/php-module-replacement-matrix.md`(0433)의 not-started/partial/
  parity/pass 표.
- **"Phase B 골격 산출물 자체가 계약대로 동작하는가?"** —
  `docs/php-runtime-phase-qa-checklist.md`(0439)의 autoload/health/module
  skeleton/parity 4개 절.

## Gate 조건

Phase C 를 시작하려면 아래 7개 조건이 **전부** 성립해야 한다. 하나라도
실패하면 Phase C 작업을 시작하지 않고, 실패한 조건을 먼저 해소한다.

1. **Phase B QA 체크리스트 통과** — `docs/php-runtime-phase-qa-checklist.md`
   가 지정한 절차대로 `scripts/test.sh`, `scripts/qa.sh` 가 모두 exit
   code 0으로 끝난다. `php` CLI가 있는 환경에서는 `scripts/qa.sh` 가
   `php/scripts/qa.sh` 를 함께 실행하므로 이 조건에 포함된다.
2. **Phase A 기준선 유지** — `docs/php-replacement-readiness-checklist.md`
   의 Gate 1(manifest 검증)과 Gate 2(경계 검사)가 모든 모듈에서 여전히
   충족된다. `python scripts/check_module_manifests.py`,
   `python scripts/check_boundaries.py` 가 위반 없이 끝나야 한다.
3. **모듈 matrix drift 없음** — `docs/php-module-replacement-matrix.md`
   (0433)에 적힌 각 모듈의 상태가 `php/src/Modules/<Module>/`,
   `php/tests/Modules/<Module>/` 의 실제 코드와 어긋나지 않는다.
   `docs/contract-drift-report.md` 가 정의한 절차로 확인한다.
4. **PHP 보안 기준 문서화 완료** — `docs/php-runtime-security-baseline.md`
   (0438)가 규정한 escaping/session/upload/path traversal 기준이
   문서로 고정되어 있고, Phase B 산출물(`php/public/index.php`,
   `php/src/Http/*`)이 그 기준을 위반하지 않는다.
5. **금지된 결합 미발생** — `docs/php-replacement-strategy.md`의
   "금지할 결합" 목록을 위반하지 않는다. 특히 PHP 런타임은 아직 실제
   RDBMS(PostgreSQL/MariaDB)에 연결되지 않고 in-memory repository만
   사용해야 한다(0435, 0436) — Phase C 이전에는 이것이 정상 상태이며,
   Phase C 가 시작되기 전에 DB 연결 코드가 먼저 추가되어 있다면 오히려
   이 gate 는 실패다.
6. **Phase B 태스크 전량 완료** — 로드맵의 0391-0440 태스크가 모두
   `tasks/done/`에 존재한다(진행 중이거나 큐에 남은 Phase B 태스크가
   없다).
7. **모듈 전환 완료를 요구하지 않음** — Phase C 시작 조건에 "어떤
   모듈이 parity 또는 pass 상태에 도달했는가"는 포함되지 않는다.
   `docs/php-replacement-strategy.md`가 이미 명시하듯 Phase A/B 동안
   PHP fixture 러너가 모듈 전체를 커버하지 못하므로 이는 구조적으로
   불가능하며, Phase C(DB 계층 이식)는 모듈 전환 완료가 아니라 DB
   계층 자체의 이식성을 다루는 단계이기 때문이다. 이 조건을 gate
   실패 사유로 사용하지 않는다.

## 재판정 방법

이 gate 의 통과 여부는 표로 고정된 값이 아니라, Phase C 를 시작하기
직전에 아래 절차로 다시 확인해야 한다 — 문서 작성 시점 이후 코드가
바뀌면 판정도 바뀔 수 있다.

```bash
python scripts/check_boundaries.py
python scripts/check_no_app_import_in_modules.py
python scripts/check_module_manifests.py
scripts/test.sh
scripts/qa.sh
cd php && composer install && cd -
php/scripts/qa.sh
```

위 명령이 모두 exit code 0으로 끝나면 조건 1, 2, 5가 충족된 것이다.
조건 3(matrix drift), 4(보안 기준), 6(태스크 전량 완료)은 문서/디렉터리
검토로 확인한다 — 자동화된 단일 명령은 없다.

## 이 문서 작성 시점 스냅샷 (Phase B 종료, 0391-0440)

이 문서를 추가하는 시점(0440, Phase B 마지막 태스크)에 위 재판정
절차를 실행한 결과는 다음과 같다.

- 조건 1: `scripts/test.sh`, `scripts/qa.sh`(php CLI 포함)가 모두 통과.
- 조건 2: `check_module_manifests.py`, `check_boundaries.py` 위반 없음.
- 조건 3: `docs/php-module-replacement-matrix.md`가 0439 QA 체크리스트
  작성 시점과 동일한 실제 코드 상태를 반영하고 있음(drift 없음).
- 조건 4: `docs/php-runtime-security-baseline.md`가 존재하고 Phase B
  산출물이 그 기준과 모순되지 않음.
- 조건 5: `php/src/Modules/Document/InMemoryRepository.php`,
  `php/src/Modules/Revision/InMemoryRepository.php`만 존재하며 실제
  RDBMS 연결 코드는 없음.
- 조건 6: `tasks/done/`에 0391-0439가 모두 존재하고, 0440은 이 문서를
  추가하는 태스크 자신이다.
- 조건 7: 위 3개 문서 어디에도 "모든 모듈이 parity/pass여야 한다"는
  요구가 없음을 확인.

**판정: PASS** — Phase C(ANSI SQL and MariaDB Portable DB Layer,
0441-0520) 착수 가능. 이 스냅샷은 시간이 지나면 stale 해질 수 있으므로,
실제로 Phase C 작업을 시작하기 직전에는 위 "재판정 방법" 절차를 다시
실행해 확인한다.

## 이 문서가 하지 않는 것

- 모듈별 readiness 판정 절차 자체를 새로 정의하지 않는다 —
  `docs/php-replacement-readiness-checklist.md`의 몫이다.
- 모듈별 최신 구현 진행 단계를 갱신하지 않는다 —
  `docs/php-module-replacement-matrix.md`의 몫이다.
- Phase B 골격 산출물의 상세 QA 항목을 다시 나열하지 않는다 —
  `docs/php-runtime-phase-qa-checklist.md`의 몫이다.
- Phase C(0441-0520) 작업 내용 자체를 계획하지 않는다 —
  `docs/php-db-ui-micro-job-prompts-0351-0670.md`의 Phase C 표가 담당한다.

## 관련 문서

- `docs/php-replacement-strategy.md` — Python 유지 기간, readiness gate
  원칙, 금지할 결합의 원본.
- `docs/php-replacement-readiness-checklist.md` — 모듈별 5-gate 판정
  절차.
- `docs/php-module-replacement-matrix.md` — 모듈별 최신 구현 진행 단계.
- `docs/php-runtime-phase-qa-checklist.md` — Phase B 골격 산출물 QA
  체크리스트, 이 문서를 미리 가리킨 선행 문서.
- `docs/php-runtime-security-baseline.md` — 이 gate의 조건 4가 참조하는
  보안 기준.
- `docs/contract-drift-report.md` — 이 gate의 조건 3이 참조하는 drift
  확인 절차.
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase B/C 태스크
  목록과 큐 정책.
