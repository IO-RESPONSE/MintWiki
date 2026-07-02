# Migration Portability Checklist

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md),
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md),
[Portable Schema Naming Policy](portable-schema-naming-policy.md),
[Portable ID Column Policy](portable-id-column-policy.md),
[Portable Timestamp Column Policy](portable-timestamp-column-policy.md),
[Portable Text Collation Policy](portable-text-collation-policy.md)가
컬럼/타입/이름 단위로 정한 규칙들을, **마이그레이션 파일 하나를 작성하거나
리뷰할 때** 빠짐없이 확인할 수 있는 체크리스트로 묶는다. 이 문서는 새
정책을 만들지 않는다 — 위 문서들이 이미 정한 규칙을 마이그레이션 작성
시점에 적용하는 순서로 재배열한 것이다.
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md#3-트랜잭션-매트릭스)가
"0448 migration portability checklist에서 확정"으로 보류했던 "DDL은
암묵적 커밋을 유발하며 롤백되지 않는다"는 전제를 3절에서 확정한다.

## 목적

지금은 `migrations/versions/`의 Alembic 마이그레이션만 존재하지만, 이
엔진은 PHP + MariaDB로 이식될 계획이라 향후 PHP 쪽에도 동등한 마이그레이션
메커니즘([0459 portable migration directory skeleton](php-db-ui-micro-job-prompts-0351-0670.md)
이후)이 생긴다. 두 마이그레이션 런타임이 같은 스키마 결과를 내려면,
개별 정책 문서에 흩어진 규칙을 마이그레이션 작성 시점에 놓치지 않고 모두
확인해야 한다. 이 문서는 그 확인 절차를 **하나의 체크리스트**로 고정해,
Alembic 마이그레이션(지금)과 PHP 마이그레이션(이후)이 같은 기준으로
리뷰되게 한다.

## 적용 범위

- 지금: `migrations/versions/` 아래 Alembic 마이그레이션 파일.
- 이후: `db/schema` 아래 portable SQL 원본과, 그 원본을 실행하는 PHP
  마이그레이션 스크립트([0459](php-db-ui-micro-job-prompts-0351-0670.md)
  이후 골격이 생긴 뒤).

적용되지 않는 것:

- 마이그레이션이 아닌 일반 쿼리 코드(`repository.py` 등)의 SQL feature
  금지 규칙 — 이는 [ansi-sql-persistence-policy.md](ansi-sql-persistence-policy.md)와
  `scripts/check_sql_denylist.py`가 이미 다룬다(1절 참고).
- 데이터 백필/시드 스크립트 — 별도 잡([0490](php-db-ui-micro-job-prompts-0351-0670.md)
  이후 seed fixture 잡)의 범위다.

## 1. SQL feature 금지 목록 (자동 검사됨)

- [ ] 새 마이그레이션이 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#postgresql-전용-기능-금지-목록)의
  금지 목록(`RETURNING`, `JSONB`, `ARRAY`, `ILIKE`, `SERIAL`/`gen_random_uuid()`,
  `ON CONFLICT`, `SKIP LOCKED`, 네이티브 `ENUM` 등)을 쓰지 않는다.
- [ ] `scripts/check_sql_denylist.py`가 `migrations/versions/*.py`를 이미
  검사 대상에 포함하므로(`scripts/qa.sh` 경유), 이 항목은 로컬에서
  `scripts/qa.sh` 실행으로 자동 확인된다 — 리뷰어가 수작업으로 표를
  대조할 필요는 없다. PHP 마이그레이션 쪽은 아직 동등한 자동 검사가
  없으므로, 골격이 생기기 전까지는 이 표를 수작업으로 대조한다.

## 2. 이름 (수작업 확인)

[Portable Schema Naming Policy](portable-schema-naming-policy.md) 기준.

- [ ] 새로 만드는 테이블/컬럼/인덱스/제약 이름이 소문자 ASCII, 숫자, 밑줄만
  쓴다(대문자·공백·하이픈·멀티바이트 없음).
- [ ] 모든 식별자가 63바이트 이하다(자동 생성되는 조합 이름 포함).
- [ ] 새 제약/인덱스에 `pk_<table>`/`fk_<table>_<column>`/`uq_<table>_<column>`/
  `ix_<table>_<column>`/`ck_<table>_<tag>` 패턴의 이름을 **명시적으로**
  지정했다(Alembic 자동 생성 이름에 의존하지 않는다).
- [ ] 새 테이블/컬럼 이름이 PostgreSQL/MariaDB 예약어 표(정책 문서 5절)와
  겹치지 않는다.

## 3. 트랜잭션 경계 (수작업 확인)

**정책: 마이그레이션은 각 DDL 문이 즉시 커밋되고 롤백되지 않는다는 전제로
작성한다.** PostgreSQL은 `CREATE TABLE`/`ALTER TABLE`을 트랜잭션에 묶어
롤백할 수 있지만, MariaDB는 대부분의 DDL이 **암묵적 커밋**을 유발하며
되돌릴 수 없다([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md#3-트랜잭션-매트릭스)의
"DDL의 트랜잭션 포함 여부" 항목).

- [ ] 하나의 마이그레이션 파일이 여러 DDL 문을 실행하더라도, 중간 실패 시
  이미 실행된 앞쪽 DDL이 자동으로 롤백된다고 가정하지 않는다. `upgrade()`
  중간에 실패하면 수동 정리가 필요할 수 있다는 전제로, 논리적으로 독립된
  스키마 변경은 **가능한 한 별도 마이그레이션 파일로 쪼갠다**(하나의 파일 =
  하나의 논리적 변경).
- [ ] `downgrade()`가 DDL 롤백을 "트랜잭션이 되돌려준다"는 가정 없이, 각
  단계를 명시적인 역방향 DDL(`drop_table`, `drop_column` 등)로 작성했다.
- [ ] DDL과 데이터 변경(DML)을 같은 마이그레이션에 섞어야 한다면, DML이
  DDL의 암묵적 커밋 이후에 실행된다는 것을 전제로 순서를 정한다(예: 컬럼
  추가 후 그 컬럼을 채우는 UPDATE는 별도 스텝으로 명확히 분리).

## 4. 컬럼 타입 (수작업 확인)

- [ ] 새 PK/FK 컬럼이 [Portable ID Column Policy](portable-id-column-policy.md)에
  따라 `String(255)`(`VARCHAR(255)`)이고, `SERIAL`/`AUTO_INCREMENT`/
  `server_default`로 DB가 값을 채우지 않는다.
- [ ] 새 timestamp 컬럼이 [Portable Timestamp Column Policy](portable-timestamp-column-policy.md)에
  따라 `DateTime(timezone=True)`이고, `server_default=func.now()`/
  `onupdate=func.now()`에 의존하지 않는다(3절이 명시한 좁은 backfill
  예외는 마이그레이션 코멘트에 근거를 남긴다).
- [ ] 새 문자열 컬럼(`String`/`Text`)이 [Portable Text Collation Policy](portable-text-collation-policy.md)에
  따른 collation 전제(MariaDB `utf8mb4_bin` 기본값, `utf8mb4` 문자셋)를
  깨지 않는다 — Alembic/SQLAlchemy는 지금 collation을 명시적으로 선언하지
  않으므로, PostgreSQL/MariaDB 각 서버·데이터베이스 기본 문자셋 설정이 이
  전제를 만족하는지 배포 문서에서 별도로 확인한다(컬럼 단위 강제는 이
  문서의 범위 밖).

## 5. 순방향/재실행 안전성 (수작업 확인)

- [ ] 마이그레이션은 순방향(`upgrade()`) 순서로만 연결된 단일 체인을
  이룬다(`down_revision` 분기가 생기지 않는다) — Alembic이 자동 생성하는
  선형 히스토리를 그대로 유지하며, 향후 PHP 마이그레이션도 같은 방식으로
  선형 순서를 유지할 수 있게 파일명에 순번 접두어(`0001_`, `0002_` 등)를
  둔다(기존 파일이 이미 이 패턴을 쓴다).
- [ ] 같은 마이그레이션을 두 번 실행해도 오류 없이 멱등하게 끝난다고
  가정하지 않는다 — 대신 Alembic/PHP 양쪽 모두 "적용된 리비전 기록"을
  단일 진실 소스로 삼아 동일 리비전을 재실행하지 않는 방식(Alembic의
  `alembic_version` 테이블과 동등한 메커니즘)을 전제로 한다. 이 메커니즘
  자체의 PHP 구현은 [0459](php-db-ui-micro-job-prompts-0351-0670.md)
  이후 골격 잡의 범위다.

## 6. Alembic ↔ PHP 마이그레이션 대응 기준

지금은 PHP 마이그레이션 런타임이 없으므로, 이 절은 향후 골격을 만들 때
지켜야 할 대응 기준을 미리 고정해 둔다.

| 기준 | Alembic (지금) | PHP 마이그레이션 (이후) |
|---|---|---|
| 리비전 식별자 | 파일명 접두어 + `revision`/`down_revision` 변수 | 동일한 순번 접두어를 파일명에 유지해 실행 순서를 일치시킨다 |
| 적용 이력 저장 | `alembic_version` 테이블 | 별도 테이블(이름은 [0459](php-db-ui-micro-job-prompts-0351-0670.md)에서 확정)에 동일한 리비전 식별자를 기록한다 |
| DDL 원본 | SQLAlchemy `op.*` 호출이 생성하는 SQL | [db/schema](php-db-ui-micro-job-prompts-0351-0670.md)의 portable SQL 원본을 그대로 실행한다(0460 이후) — Alembic이 생성하는 DDL과 결과 스키마가 동일해야 한다 |
| 본 체크리스트 적용 | 1~5절 전체 | 1절(자동 검사)을 제외한 2~5절을 PHP 마이그레이션 리뷰 시 동일하게 적용한다 |
| 검증 방법 | `scripts/qa.sh` (`check_sql_denylist.py` 포함) | PHP 쪽 자동 검사가 생기기 전까지는 이 표와 2~5절 체크리스트를 리뷰 시 수작업으로 대조한다 |

이 표의 목표는 "Alembic 마이그레이션을 그대로 옮기면 PHP 쪽도 동일한
스키마를 만든다"는 것을 보장하는 것이다. 두 런타임이 서로 다른 스키마를
만들면 이식 시점에 데이터 이관 자체가 막힌다.

## 이 문서 이후 단계

- **0450**([SQL dialect abstraction skeleton](php-db-ui-micro-job-prompts-0351-0670.md)):
  4절이 다루는 컬럼 타입 매핑을 실제 코드 skeleton으로 옮긴다.
- **0459**([portable migration directory skeleton](php-db-ui-micro-job-prompts-0351-0670.md)):
  6절 표가 미확정으로 남긴 PHP 마이그레이션 적용 이력 테이블 이름과 실행
  방식을 확정한다.
- **0469**([Add schema SQL lint test](php-db-ui-micro-job-prompts-0351-0670.md)):
  `db/schema`의 portable SQL 원본에 대해 1절과 동등한 자동 검사를 추가한다
  — 이 시점부터 PHP 쪽 마이그레이션 원본도 자동 검사 대상에 들어간다.
- **0505**([portable migration dry-run command](php-db-ui-micro-job-prompts-0351-0670.md)):
  이 체크리스트의 3절(트랜잭션 경계) 항목을 실행 전에 자동으로 점검하는
  dry-run 명령을 추가한다.

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 1절 금지
  목록의 원출처.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 3절이
  확정하는 DDL 암묵적 커밋 전제의 원출처.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) — 2절
  이름 규칙의 원출처.
- [Portable ID Column Policy](portable-id-column-policy.md),
  [Portable Timestamp Column Policy](portable-timestamp-column-policy.md),
  [Portable Text Collation Policy](portable-text-collation-policy.md) — 4절
  컬럼 타입 규칙의 원출처.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
