# Portable Query Builder Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md#2-최소-동작-집합)가 statement의
구체 표현 방식을 이 문서로 위임한 지점과, [SQL Dialect Abstraction
Skeleton](../src/persistence/dialect.py)(0450)이 `object` 타입으로 열어 둔
statement 표현을 이어받아 확정한다. 이 문서는 정책 선언이며, 기존 코드
(`src/modules/*/repository.py`)를 지금 바꾸지 않는다 — 아래에서 확인하듯
기존 코드는 이미 이 정책이 요구하는 방식(SQLAlchemy 쿼리 빌더, ad hoc
문자열 SQL 없음)으로 동작하고 있고, 이 문서는 그 동작을 앞으로도 유지할
규칙으로 명문화하는 것이다.

## 목적

[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)는 "어떤 SQL
기능을 쓸 수 있는가"를 정했지만, "그 SQL을 코드에서 어떻게 만드는가"는
정하지 않았다. 문자열을 이어 붙이거나(`f"SELECT * FROM document WHERE
id = '{id}'"`) `%`/`.format()`으로 값을 보간해 SQL 텍스트를 직접 조립하면,
값 이스케이프가 SQL 문법·드라이버마다 달라 SQL 인젝션 위험이 생기고,
PostgreSQL과 MariaDB가 문자열 리터럴 이스케이프 규칙(따옴표 처리 등)이
달라 같은 문자열 조립 코드가 두 DB에서 다르게 깨질 수 있다. 이 문서는
**모든 SQL statement를 쿼리 빌더(SQLAlchemy Core/ORM 표현식)로만 생성**해,
값 바인딩을 드라이버에 위임하고 SQL 텍스트 조립 자체를 코드에서 없앤다.

## 적용 범위

이 정책은 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md#적용-범위)와
동일한 코드에 적용된다.

- `src/modules/*/repository.py`
- `src/persistence/` 아래 트랜잭션 헬퍼, DB adapter 구현체
  ([db-adapter-contract.md](db-adapter-contract.md)의 `fetch_one`/`fetch_all`/
  `execute`에 전달되는 statement)
- `migrations/versions/` 아래 Alembic 마이그레이션이 실행하는 DDL/DML

적용되지 않는 것:

- `alembic`이 내부적으로 관리하는 `alembic_version` 테이블 등 프레임워크
  자체 동작.
- 테스트 전용 SQLite 설정, fixture 데이터 삽입에 쓰이는 ORM 객체 생성
  (이미 쿼리 빌더/ORM을 거치므로 별도 예외가 아니다).
- SQL을 쓰지 않는 코드(`redis.py` 등 캐시 어댑터, 도메인 계층).

## 1. 정책: 모든 statement는 쿼리 빌더로 생성한다

**정책: SQL을 실행하는 모든 statement는 SQLAlchemy Core/ORM 표현식
(`select()`, `insert()`, `update()`, `delete()`와 그 메서드 체인)으로만
만든다. SQL 텍스트를 문자열로 조립해 실행하는 코드(ad hoc 문자열 SQL)는
금지한다.**

ad hoc 문자열 SQL로 간주해 금지하는 패턴:

- f-string/`%`-포맷/`.format()`/문자열 연결(`+`)로 SQL 텍스트를 만들어
  `session.execute()`에 전달.
- `sqlalchemy.text()`에 값을 문자열 보간으로 채워 넣는 사용
  (`text(f"... WHERE id = '{id}'")`) — `text()` 자체의 허용 범위는 2절 참고.
- 드라이버의 raw cursor(`connection.exec_driver_sql()` 등)에 조립한
  문자열을 직접 전달.

이 기준은 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의
금지 목록(`RETURNING`, `ILIKE` 등 *어떤 SQL 기능*을 쓰는가)과 독립적이다 —
이 문서는 *허용된 기능이라도 어떻게 SQL을 만드는가*를 규정한다. 쿼리
빌더로 만든 statement라도 금지 기능을 쓰면 여전히 0447 검사 대상이다.

## 2. 허용되는 표현

- **표준 경로**: `select(Model).where(Model.column == value)`처럼 ORM
  모델과 컬럼 속성을 사용하는 쿼리 빌더 표현식. 값은 항상 Python 값으로
  전달하고, SQLAlchemy가 파라미터 바인딩(placeholder + bound parameter)으로
  변환한다 — 아래 4절 예시 참고.
- **`update()`/`delete()`도 동일**: `update(Model).where(...).values(...)`
  형태로 조건과 값을 메서드 체인으로 전달한다. `values()`에 넘기는 값도
  Python 값이어야 하며, 값 자체에 SQL 텍스트를 조립해 넣지 않는다.
- **`text()`의 제한적 허용**: 값 보간 없이 정적인 SQL 조각(리터럴 문자열,
  바인드 파라미터 placeholder만 포함)을 표현해야 하는 경우에 한해
  `sqlalchemy.text("... WHERE id = :id").bindparams(id=value)`처럼
  **바인드 파라미터를 통해서만** 값을 전달하면 허용한다. 값을 문자열에
  직접 섞어 넣는 순간 1절의 금지 대상이 된다. 현재 코드베이스에는
  `text()` 사용 사례가 없다 — 필요해지면 이 조건을 만족하는지 코드
  리뷰에서 확인한다.

## 3. PHP 이식 대응

PHP 쪽 구체 구현([db-adapter-contract.md](db-adapter-contract.md#계약을-만족하는-구현체)의
`0484` 이후 PDO skeleton)은 SQLAlchemy 쿼리 빌더가 없으므로, 동일한 원칙을
PDO **prepared statement**로 만족한다.

- SQL 텍스트에 값을 문자열로 보간하지 않는다 — `PDO::prepare()`가 받는 SQL
  문자열은 `:name` 또는 `?` placeholder만 포함하고, 값은 항상
  `bindValue()`/`execute([...])`로 별도 전달한다.
  `"SELECT * FROM document WHERE id = '" . $id . "'"`처럼 값을 SQL 문자열에
  직접 이어 붙이는 코드는 Python 쪽의 ad hoc 문자열 SQL 금지와 동일하게
  금지한다.
  이는 PHP 쪽에도 이 문서가 정의하는 "쿼리 빌더/바인드 파라미터로만 값을
  전달한다"는 동일한 원칙을 적용하는 것이며, 이 문서가 두 언어 모두를
  아우르는 근거다.
- PHP 쪽에 별도 쿼리 빌더 라이브러리를 도입할지 여부(예: Doctrine DBAL)는
  이 문서의 범위 밖이다 — `0484` 이후 PHP 구현 태스크가 prepared statement
  직접 사용으로 충분한지 판단한다. 이 문서가 요구하는 최소 기준은
  "SQL 텍스트에 값을 문자열 보간하지 않는다"이며, 이를 만족하면 별도
  쿼리 빌더 라이브러리 도입은 선택 사항이다.

## 4. 예시

현재 저장소 코드는 이미 이 정책을 만족한다.

```python
# src/modules/document/repository.py — 허용되는 형태
query = select(DocumentORM).where(DocumentORM.id == id)
result = await self.session.execute(query)
```

```python
# 금지되는 형태 (코드베이스에 없음 — 반례로만 제시)
query = f"SELECT * FROM document WHERE id = '{id}'"
result = await self.session.execute(text(query))
```

| 패턴 | 판정 | 이유 |
|---|---|---|
| `select(Model).where(Model.col == value)` | 허용 | 값이 파라미터 바인딩으로 전달됨 |
| `update(Model).where(...).values(col=value)` | 허용 | 동일 |
| `text("... WHERE id = :id").bindparams(id=value)` | 허용(제한적) | 값이 바인드 파라미터로만 전달됨 — 2절 |
| `text(f"... WHERE id = '{value}'")` | 금지 | SQL 텍스트에 값이 문자열로 보간됨 |
| `session.execute(f"SELECT ...")` | 금지 | ad hoc 문자열 SQL |

## 이 문서 이후 단계

- **0452, 0453**([document/revision portable repository
  tests](php-db-ui-micro-job-prompts-0351-0670.md)): document/revision
  저장소가 이 정책을 만족하는 상태로 portability 테스트를 통과하는지
  검증한다.
- 자동 검사: [0447 SQL feature denylist
  check](php-db-ui-micro-job-prompts-0351-0670.md)(`scripts/check_sql_denylist.py`)는
  아직 이 문서의 ad hoc 문자열 SQL 패턴(f-string SQL 조립 등)을 탐지하지
  않는다 — 현재는 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의
  PostgreSQL 전용 기능 금지 목록만 검사한다. 이 문서의 기준을 자동
  검사에 포함하는 작업은 번호가 아직 배정되지 않은 이후 태스크의
  범위이며, 그 전까지는 코드 리뷰가 유일한 강제 수단이다.

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md#2-최소-동작-집합) — 이
  문서가 확정하는 statement 표현이 채우는 계약의 위임 지점.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — "어떤 SQL
  기능을 쓸 수 있는가"를 정한 문서. 이 문서는 "SQL을 어떻게 만드는가"를
  다룬다는 점에서 상호 보완적이다.
- [SQL Dialect Abstraction Skeleton](../src/persistence/dialect.py) — 이
  문서가 확정한 쿼리 빌더 표현이 dialect별 upsert 등에서 반환하는 statement
  형태의 전제.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
