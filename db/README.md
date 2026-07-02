# db/ — Portable Migration Directory

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 골격.
[Migration Portability Checklist](../docs/migration-portability-checklist.md)
§6이 "이후 확정" 항목으로 남겨 둔 PHP 마이그레이션 적용 이력 테이블 이름과
실행 방식을, 이 문서가 확정한다.

## 목적

지금 `migrations/versions/`의 Alembic 마이그레이션은 Python/SQLAlchemy에만
묶여 있다. 이 엔진은 완성 후 PHP + MariaDB로 이식될 계획이라
([ansi-sql-persistence-policy.md](../docs/ansi-sql-persistence-policy.md)),
Python과 PHP 양쪽이 같은 스키마 결과를 내도록 참고할 **portable SQL
원본의 위치**가 필요하다. `db/`가 그 위치다 — Alembic이 생성하는 DDL과
`db/` 아래의 portable SQL이 항상 같은 스키마를 가리켜야 한다.

이 태스크(0459)는 그 자리를 잡는 골격만 만든다. 실제 SQL 내용은 이후
태스크(0460 이후)가 채운다.

## 디렉토리 구조

```
db/
├── README.md      # 이 문서
└── migrations/    # 순번이 매겨진 portable 마이그레이션 원본 자리
```

- `db/schema/`는 아직 만들지 않는다 — base schema SQL draft를 추가하는
  [0460](../docs/php-db-ui-micro-job-prompts-0351-0670.md) 이후 태스크의
  범위다.
- `db/migrations/`는 지금 비어 있다. 실제 portable 마이그레이션 파일은
  `db/schema/`가 정의하는 테이블이 먼저 존재해야 의미가 있으므로, 내용은
  이후 태스크에서 채운다. 파일명은 `migrations/versions/`와 동일한 순번
  접두어 규칙(`0001_`, `0002_`, ...)을 따라 선형 체인을 유지한다
  ([Migration Portability Checklist §5](../docs/migration-portability-checklist.md)).

## 적용 이력 테이블 (Migration Portability Checklist §6 확정)

Alembic은 `alembic_version` 테이블로 적용된 리비전을 추적한다. PHP 쪽
portable 마이그레이션 러너(0484 이후)가 같은 역할로 쓸 테이블을 이 태스크가
확정한다.

- **테이블 이름:** `schema_migration`
  ([Portable Schema Naming Policy](../docs/portable-schema-naming-policy.md)에
  따라 단수형, 소문자 ASCII, 예약어 아님).
- **컬럼:**
  - `version VARCHAR(255) NOT NULL` — 적용된 마이그레이션 파일의 순번
    접두어(예: `"0001"`). PK.
  - `created_at TIMESTAMP NOT NULL` — 이 리비전이 적용된 시각
    ([Portable Timestamp Column Policy](../docs/portable-timestamp-column-policy.md)의
    `created_at` 네이밍을 그대로 따른다. DB `server_default`가 아니라
    애플리케이션이 값을 채운다).
  - 제약: `pk_schema_migration` (PK on `version`).
- **실행 방식:** 마이그레이션 러너는 `db/migrations/` 아래 파일을 순번
  접두어 오름차순으로 하나씩 실행하고, 각 파일 실행 성공 직후
  `schema_migration`에 해당 `version` 행을 삽입한다. 이미 기록된 `version`은
  다시 실행하지 않는다(재실행 안전성은 파일 자체가 아니라 이 기록이
  보장한다 — [Migration Portability Checklist §5](../docs/migration-portability-checklist.md)).
  구체 러너 구현은 이 태스크의 범위가 아니다(0484 이후 PHP skeleton,
  0505 dry-run 명령).

## 관련 문서

- [Migration Portability Checklist](../docs/migration-portability-checklist.md) —
  이 골격이 확정하는 §6 표의 원출처.
- [ANSI SQL Persistence Policy](../docs/ansi-sql-persistence-policy.md) —
  portable SQL 원본이 지켜야 할 SQL feature 제약.
- [DB Adapter Contract](../docs/db-adapter-contract.md) — 이 마이그레이션
  러너가 아닌, 쿼리 시점 어댑터 계약(별개 문서).
- [PHP, ANSI DB, UI micro job prompts 0351-0670](../docs/php-db-ui-micro-job-prompts-0351-0670.md) —
  0460(schema) 이후 잡 목록.
