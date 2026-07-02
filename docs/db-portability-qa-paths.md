# DB Portability QA Paths

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[Migration Portability Checklist](migration-portability-checklist.md),
[MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md),
[Runner](runner.md)가 이미 정의한 개별 검사/스크립트를, **"이 검사는 언제,
어디서, 누가 실행하는가"** 기준으로 로컬/CI/수동 세 경로로 지도화한다. 이
문서는 새 검사를 만들지 않는다 — Phase C가 지금까지 흩어진 채로 추가한
검사(`scripts/check_sql_denylist.py`, `scripts/test.sh`, `scripts/qa.sh`,
`scripts/mariadb_smoke_check.py`, `scripts/postgresql_smoke_check.py`)를
실행 경로별로 재배열한 것이다.

## 목적

Phase C 태스크들은 각자 자신이 추가한 검사 하나만 설명해 왔다(0469 lint
테스트, 0480 smoke 계획, 0481/0482 선택 스크립트). 그 결과 "커밋 전에
자동으로 도는 것은 무엇이고, 사람이 DB 서버를 준비해야만 도는 것은
무엇인가"를 한 곳에서 확인할 방법이 없었다. 이 문서는 그 간극을 메워,
새 DB portability 검사를 추가하거나 기존 검사를 실행할 때 세 경로 중
어디에 속하는지 바로 판단할 수 있게 한다.

## 적용 범위

- 대상: 0441-0483까지 Phase C가 추가한 DB portability 관련 자동 검사와
  선택 스크립트 전체.
- 이 문서가 정하지 않는 것(범위 밖):
  - [0500 Add DB phase QA checklist](php-db-ui-micro-job-prompts-0351-0670.md)
    — ANSI lint, MariaDB smoke, PHP PDO skeleton을 하나의 완결된 QA
    체크리스트로 통합하는 후속 작업. 이 문서는 그 통합 대상이 될 세 경로의
    현재 상태만 기록한다.
  - 새로운 외부 CI 도구(GitHub Actions 등) 도입 — 이 저장소는 지금
    [Runner](runner.md)의 자동 커밋 게이트를 CI 경로로 취급한다는 전제만
    기록하며, 별도 CI 파이프라인을 새로 구성하지 않는다.

## 1. 로컬 경로 (개발자 수동 실행, DB 서버 불필요)

개발자가 작업 중 언제든 실행할 수 있고, 실제 PostgreSQL/MariaDB 서버 없이
항상 결정적으로 끝난다.

```bash
scripts/test.sh   # pytest 전체 (mariadb_smoke_check.py/postgresql_smoke_check.py의
                   # skip 로직 등 순수 로직 테스트 포함, 실제 접속은 하지 않음)
scripts/qa.sh     # check_boundaries.py + check_sql_denylist.py + scripts/test.sh
                   # + git diff --check
```

`scripts/check_sql_denylist.py`는 `db/schema/*.sql`, `migrations/versions/*.py`
등을 정적으로만 검사하므로([Migration Portability Checklist §1](migration-portability-checklist.md#1-sql-feature-금지-목록-자동-검사됨))
DB 서버 유무와 무관하게 항상 실행된다.

## 2. CI 경로 (커밋 전 자동 게이트)

이 저장소는 별도 CI 서버 대신 [Runner](runner.md)가 커밋 게이트 역할을
한다 — `scripts/run-next-task.sh`가 매 태스크 완료 후 **동일한**
`scripts/test.sh`와 `scripts/qa.sh`를 자동으로 실행하고, 종료 코드가
0이 아니면 커밋하지 않고 변경을 되돌린다([runner.md](runner.md) "QA must
pass ... before any changes are committed").

- CI 경로가 검사하는 대상은 §1 로컬 경로와 완전히 동일하다(같은 스크립트,
  같은 조건) — 로컬에서 통과한 검사는 CI에서도 같은 결과를 낸다.
- §3의 MariaDB/PostgreSQL smoke 스크립트는 `scripts/qa.sh`가 호출하지
  않으므로 CI 경로에 포함되지 않는다 — 이 저장소의 러너 환경이 기본으로
  실제 DB 서버를 띄우지 않기 때문이다([MariaDB Migration Smoke Plan
  §1](mariadb-migration-smoke-plan.md#1-실행-조건-선택-실행)과 동일한
  이유).

## 3. 수동/선택 경로 (실제 DB 서버가 있을 때만)

사람이 실제 PostgreSQL/MariaDB 서버를 준비하고 DSN 환경 변수를 설정한
뒤 직접 실행해야 한다. `scripts/qa.sh`/CI 경로에는 포함되지 않으며,
DSN이 없으면 실패가 아니라 skip(종료 코드 0)으로 끝난다.

```bash
WIKI_MARIADB_DSN=mysql+pymysql://user:pass@host:3306/db \
  .venv/bin/python scripts/mariadb_smoke_check.py

WIKI_DATABASE_URL=postgresql://user:pass@host:5432/db \
  .venv/bin/python scripts/postgresql_smoke_check.py
```

두 스크립트 모두 `db/schema/*.sql`을 FK 의존 순서대로 격리된 smoke
데이터베이스에 적용해 보고 정리한다([MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md)).

## 경로 요약

| 경로 | 실행 주체 | 트리거 | DB 서버 필요 | 실패 시 처리 |
|---|---|---|---|---|
| 로컬 | 개발자 | 수동 (`scripts/test.sh`, `scripts/qa.sh`) | 불필요 | 0이 아닌 종료 코드 → 커밋 전 수정 |
| CI | Runner (`scripts/run-next-task.sh`) | 태스크 완료마다 자동 | 불필요 | 커밋하지 않고 변경 되돌림([runner.md](runner.md)) |
| 수동/선택 | 사람 | 수동, DSN 설정 시에만 | 필요 | DSN 없음 → skip(0), DDL/테이블 확인 실패 → 실패(1) |

## 이 문서 이후 단계

- **0500**([Add DB phase QA checklist](php-db-ui-micro-job-prompts-0351-0670.md)):
  이 세 경로를 ANSI lint, MariaDB smoke, PHP PDO skeleton과 함께 하나의
  완결된 QA 체크리스트로 통합한다.

## 관련 문서

- [Migration Portability Checklist](migration-portability-checklist.md) —
  §1 자동 검사(로컬/CI 공통)의 원출처.
- [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) — §3
  수동/선택 경로 스크립트의 실행 조건·단계·실패 판정 기준.
- [Runner](runner.md) — CI 경로로 취급하는 커밋 게이트의 원출처.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
