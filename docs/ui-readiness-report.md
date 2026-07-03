# UI Readiness Report (Placeholder)

이 문서는 Phase D(Server-rendered UI after PHP and DB, 0521-0610) 완료 후 
웹호스팅 배포를 위한 UI 계층의 최종 준비 상태를 보고하는 리포트의 골격을 고정한다.

이 태스크는 리포트의 **형식과 실행 방법만** 고정하는 placeholder 다 —
Phase D가 실제로 완료된 후에 구체적인 UI 상태 검증 로직은 만들지 않는다.

## UI Readiness 정의

**UI Readiness** 는 웹호스팅 배포를 위한 UI 계층이 다음 기준을 만족하는지 판정하는 것이다:

- `docs/php-ui-readiness-gate.md` 가 정의한 7개 조건(라우터/템플릿, HTML escaping,
  CSRF, 보안 헤더, 모바일 반응형, 접근성)이 모두 통과했는가?
- `php/src/Http/` 와 `php/src/Ui/` 의 라우터와 템플릿이 완성되었는가?
- `php/public/assets/` 의 정적 자산이 배포 가능 상태에 있는가?
- 자동 테스트(`scripts/test.sh`, `scripts/qa.sh`, `php/scripts/qa.sh`)가 모두
  통과했는가?

## 현재 상태: 측정 불가 (Phase D 완료 전)

이 리포트를 생성하는 `scripts/ui_readiness_report.py` 는 각 체크포인트에 대해 아래 정보만 출력한다:

- `aspect`: 검사 항목 (라우터, escaping, CSRF, 헤더, 모바일, 접근성, 정적 자산).
- `status`: 현재 상태 (ready, warning, not_measurable, in_progress).
- `gate_pass`: 해당 항목이 배포 게이트를 통과했는지 여부.

Phase D가 진행 중인 동안(0521-0610)은 대부분 항목의 판정이 구조적으로 `not_measurable` 이다 —
완성도가 낮거나 테스트가 아직 실행 가능하지 않기 때문이다. 이 스크립트는 `not_measurable` 
상태를 이유로 실패(비정상 종료)하지 않는다 — 미완성은 Phase D의 정상 상태이므로, 
readiness 리포트는 그 사실을 정보성으로만 보고한다.

## 실행 방법

```bash
python scripts/ui_readiness_report.py
```

표준 출력으로 항목별 한 줄짜리 표를 출력하고, 항상 종료 코드 0 을 반환한다. 이 스크립트는 
배포 gate를 내리는 것이 아니라 현재 상태를 보여주는 리포트이므로 `scripts/qa.sh` 에는 
연결하지 않는다 — `docs/php-ui-readiness-gate.md` 와 달리, readiness 리포트는 
각 항목의 준비 상황을 정보성으로 제시할 뿐, 미준비된 항목이 배포를 자동으로 차단하지 않는다.

## 이후 확장 (이 태스크의 범위 밖)

Phase D가 완료된 후(0610 이후) 아래 항목이 채워질 수 있다 —
실제 구현은 후속 태스크가 담당하며, 이 문서는 그 방향만 남긴다.

- **라우터/템플릿 상태**: `php/src/Http/` 와 `php/src/Ui/` 의 파일 존재 여부,
  각 라우터별 구현 완성도 스캔.
- **HTML Escaping 준수**: `php/tests/Modules/Document/HtmlEscapingTest.php` 
  통과 여부를 readiness 판정에 반영.
- **CSRF 방어**: state-changing 폼의 CSRF token 필드 구조 존재 확인.
- **Security Headers**: `php/tests/Http/SecurityHeadersTest.php` 통과 여부.
- **모바일 반응형**: `php/tests/UI/MobileTest.php` viewport/media query 확인.
- **접근성 기초**: `php/tests/UI/AccessibilityBaselineTest.php` lang/landmark/role 확인.
- **정적 자산**: `php/public/assets/` 디렉터리 구조와 파일 존재 여부.
- **자동 검사**: `scripts/test.sh`, `scripts/qa.sh`, `php/scripts/qa.sh` 통과 여부.

## 이 문서가 하지 않는 것

- Phase D UI 구현 자체를 검사하지 않는다 — 검사는 `docs/php-ui-readiness-gate.md` 가 담당.
- `scripts/qa.sh` 에 이 스크립트를 자동 연결하지 않는다.
- 미준비 상태를 이유로 배포를 차단하지 않는다 — readiness 리포트는 상태 확인 도구일 뿐.

## 관련 문서

- `docs/php-ui-readiness-gate.md` — Phase D 배포 게이트 조건 (7개 항목, 필수 통과).
- `docs/php-ui-phase-qa-checklist.md` — Phase D 회귀 검사 기준.
- `docs/php-ui-architecture.md` — Phase D UI 아키텍처 원본.
- `docs/php-static-asset-serving.md` — 정적 자산 정책.
- `docs/shared-hosting-migration-policy.md` — 웹호스팅 배포 정책.
- `scripts/ui_readiness_report.py` — 이 리포트의 구현 스크립트.
- `tests/test_ui_readiness_report.py` — 리포트 스크립트 테스트.
