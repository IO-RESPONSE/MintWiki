# tests/fixtures/seed — Portable Seed 픽스처

Portable seed fixture는 PostgreSQL과 MariaDB 양쪽에서 동일하게 실행할 수 있는 INSERT 문을 포함한다.

## 파일 구조

- 각 파일은 하나의 테이블을 위한 seed 데이터를 포함한다.
- 파일명은 테이블명과 동일하다: `<table>.sql` (예: `documents.sql`, `revisions.sql`).
- 모든 SQL은 [ANSI SQL Persistence Policy](../../../docs/ansi-sql-persistence-policy.md)의 금지 목록을 따른다.

## 작성 규칙

### 1. SQL 문법

- PostgreSQL과 MariaDB 양쪽에서 동일하게 실행되는 ANSI SQL만 사용한다.
- 방언별 함수(SERIAL, gen_random_uuid(), UUID() 등)를 사용하지 않는다.
- UUID는 문자열 상수로 고정값을 직접 입력한다.
- TIMESTAMP는 ISO 8601 형식(`2026-01-01T00:00:00Z`)으로 명시한다.

### 2. 데이터 일관성

- 모든 값은 결정론적(deterministic)이어야 한다: 같은 fixture를 여러 번 로드하면 동일한 데이터가 되어야 한다.
- FK 참조는 이전 테이블에서 삽입된 ID와 일치해야 한다.
- 테이블 순서는 FK 종속성을 고려한다: 참조되는 테이블이 먼저 온다.

### 3. 기본 데이터

- **documents.sql**: 3개의 기본 문서
  - 각 문서는 고정 UUID, 제목, 정규화된 제목을 갖는다.
  - `current_revision_id`는 revisions.sql에서 삽입될 리비전을 참조한다.
  
- **revisions.sql**: 4개의 기본 리비전
  - 각 리비전은 문서를 참조하는 FK를 갖는다.
  - 리비전들은 부모-자식 관계를 형성한다(revision chain).

### 4. UUIDs

테스트 일관성을 위해 UUID는 다음 패턴으로 생성한다:
- 문서: `doc-<number>-00000000-0000-0000-0000-0000000000`
- 리비전: `rev-<number>-00000000-0000-0000-0000-0000000000`
- 사용자/작가: `user-<number>-0000-0000-0000-0000000000`

### 5. Timestamps

모든 timestamp는 UTC 기준 ISO 8601 형식:
```
2026-01-01T00:00:00Z  (document 생성)
2026-01-02T00:00:00Z  (revision 생성)
...
```

MariaDB 문자열 변환:
- PostgreSQL: `TIMESTAMP '2026-01-01T00:00:00Z'` (또는 문자열 자동 변환)
- MariaDB: 동일한 문자열이 자동 변환됨 (호스트 time_zone이 UTC일 때)

모든 값은 애플리케이션이 UTC로 정규화한 값이므로, 두 DB 모두 동일한 문자열 형식을 사용한다.

## 특수 케이스

### NULL 처리

- FK 필드가 선택사항(nullable)인 경우 NULL 값을 사용할 수 있다.
- 예: `parent_revision_id`는 첫 리비전에서 NULL이다.

### 재실행 안전성

- 같은 fixture를 여러 번 로드할 때 중복 삽입을 방지하려면, fixture 로더가 DELETE 또는 사전 검사를 수행해야 한다.
- 이 파일들은 순수 INSERT 문만 포함하며, 중복 처리는 loader 로직에서 수행한다.
