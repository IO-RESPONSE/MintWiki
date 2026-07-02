# Repository Transaction Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract](db-adapter-contract.md)의 §2(최소 동작 집합)는
`commit`/`rollback`이 "존재해야 한다"는 계약만 고정하고, 정확한 호출
시점과 크로스 모듈 트랜잭션 경계는 이 문서로 미뤘다. 이 문서는 새 정책을
만들지 않는다 — 지금 `DatabaseDocumentRepository`,
`DatabaseRevisionRepository`, `DocumentRevisionTransaction`
([persistence-boundaries.md](persistence-boundaries.md#cross-module-transactions))이
이미 암묵적으로 따르는 커밋 시점 패턴을 명문화해, PHP PDO 구현이 같은
경계를 지키게 하는 것이 목적이다.

## 목적

지금 Database* 저장소들은 메서드마다 `flush()` 다음에 `commit()`을
호출한다. 이 커밋 시점이 "왜 거기인지", "메서드 하나가 트랜잭션 하나와
같은 것인지", "여러 모듈에 걸친 쓰기는 어떻게 원자성을 지키는지"는 코드를
읽어야만 알 수 있고 문서 어디에도 규칙으로 적혀 있지 않다. PHP 포팅
시점에는 PDO의 `beginTransaction()`/`commit()`/`rollBack()`을 같은
자리에 놓아야 하므로, 지금 이 경계를 규칙으로 고정하지 않으면 PHP
구현자가 임의로 커밋 시점을 정해 Python 쪽과 다른 원자성 보장을 갖게 될
위험이 있다.

## 적용 범위

적용 대상:

- `src/modules/*/repository.py`의 Database* 구현체가 단일 테이블에
  쓰기를 수행하는 모든 메서드(`create`, `update` 등).
- `src/persistence/transaction.py`의 `DocumentRevisionTransaction`처럼
  둘 이상의 모듈 테이블에 걸쳐 원자적 쓰기를 수행하는 트랜잭션 헬퍼.
- [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP 쪽 PDO 기반
  SQL repository와 트랜잭션 헬퍼.

적용되지 않는 것:

- InMemory* 구현체 — 세션/커밋 개념이 없으므로 이 정책의 대상이 아니다.
- 조회 전용 메서드(`get`, `list_by_document_id` 등) — 쓰기가 없으므로
  commit/rollback을 호출하지 않는다.
- 제약 위반을 식별하는 구체적인 방법(에러 메시지 매칭 vs 제약 이름) —
  [0474 portable duplicate key handling](php-db-ui-micro-job-prompts-0351-0670.md)이
  다룬다. 이 문서는 "언제 rollback을 호출하는가"만 다루고, "어떤 예외를
  도메인 예외로 바꾸는가"는 다루지 않는다.

## 1. 트랜잭션 경계: 저장소 메서드 하나 = 트랜잭션 하나

**계약: 단일 테이블에 쓰는 Database* 저장소 메서드는 자기 자신이 하나의
완결된 트랜잭션이다.** 메서드가 반환하기 전에 반드시 commit되거나
rollback되며, 호출자(Service 계층)가 이어서 커밋할 필요가 없다.

- 이미 만족: `DatabaseDocumentRepository.create`,
  `DatabaseRevisionRepository.create`,
  `DatabaseDocumentRepository.update`(`update_current_revision` 등) 모두
  메서드 내부에서 `commit()`까지 호출하고 반환한다.
- 이 경계의 함의: 한 메서드 호출이 반환했다면 그 변경은 이미 durable하다
  (또는 예외와 함께 완전히 취소됐다). 호출자가 "저장소 메서드 여러 개를
  부르고 마지막에 한 번에 커밋"하는 패턴을 쓸 수 없다 — 그런 원자성이
  필요하면 §3의 크로스 모듈 트랜잭션 헬퍼를 쓴다.

## 2. commit/rollback의 정확한 시점

**계약: 쓰기 메서드는 `flush()`(또는 대응하는 문 실행) 직후, 같은
`try` 블록 안에서 `commit()`을 호출한다. 그 블록에서 통합 제약 위반
신호([db-adapter-contract.md §3](db-adapter-contract.md#3-통합-제약-위반-신호))가
발생하면 `rollback()`을 호출한 뒤 예외를 다시 던진다(또는 도메인
예외로 변환해 던진다).**

순서는 항상 다음과 같다:

1. `add`(신규 행) 또는 `execute`(UPDATE 문)로 변경을 세션에 올린다.
2. `flush()`로 제약을 검증한다 — 아직 커밋 전이므로 이 시점에 실패해도
   DB에는 아무것도 남지 않는다.
3. 검증을 통과하면 `commit()`으로 확정한다.
4. 2~3 사이에서 통합 제약 위반이 발생하면 `rollback()`을 호출해 세션을
   깨끗한 상태로 되돌린 뒤, 원본 예외를 다시 던지거나 도메인 예외로
   변환해 던진다. `rollback()` 없이 예외만 던지지 않는다 — 세션이 실패
   상태로 남아 다음 호출에 영향을 줄 수 있다.

```python
# DatabaseDocumentRepository.create가 따르는 순서
orm_document = DocumentORM.from_domain(document)
self.session.add(orm_document)                  # 1
try:
    await self.session.flush()                    # 2
    await self.session.commit()                    # 3
except IntegrityError as e:
    await self.session.rollback()                   # 4
    raise DuplicateNormalizedTitleError(...)
```

- 제약 위반이 없는 단순 쓰기(예: `DatabaseRevisionRepository.create`,
  FK만 있고 애플리케이션 레벨 유일성 검사가 없는 경우)는 `try`/`except`
  없이 `flush()` → `commit()`만으로 충분하다 — 위반 시 세션 계층이
  던지는 예외가 그대로 호출자에게 전파된다. 다만 이 경우에도 위반이
  발생하면 세션은 실패 상태로 남으므로, 같은 세션을 재사용하는 호출자는
  다음 호출 전에 별도로 rollback을 처리해야 한다는 점을 인지한다(§3의
  트랜잭션 헬퍼처럼 명시적으로 `try`/`except`를 감싸는 쪽이 더 안전한
  기본값이다 — 새 쓰기 메서드를 추가할 때는 `except`를 생략하지 않는
  쪽을 기본으로 삼는다).
- `commit()`은 메서드당 정확히 한 번만 호출한다. 조회(`fetch_one`,
  `fetch_all`)는 commit을 호출하지 않는다 — 읽기 전용 문은 트랜잭션
  상태를 바꾸지 않는다.

## 3. 크로스 모듈 트랜잭션 경계

**계약: 두 개 이상의 모듈 테이블에 걸친 원자적 쓰기가 필요하면, 개별
저장소의 `create`/`update`를 순서대로 호출하지 않는다. 대신
`DocumentRevisionTransaction`처럼 전용 트랜잭션 헬퍼를 만들어, 그 헬퍼
안에서 여러 `session.add`/`session.execute`를 모은 뒤 단 한 번
`commit()`한다.**

- 이유: §1에 따라 저장소 메서드 하나는 이미 그 자체로 하나의 완결된
  트랜잭션이다. `DocumentRepository.create()`를 부르고 이어서
  `RevisionRepository.create()`를 부르면, 첫 번째 호출이 이미 커밋된
  뒤에 두 번째 호출이 실패할 수 있다 — 문서만 남고 리비전이 없는
  부분 쓰기가 발생한다. 이는
  [persistence-boundaries.md](persistence-boundaries.md#current-revision-pointer)가
  금지하는 상태다.
- 이미 만족: `DocumentRevisionTransaction.create_document_with_revision`은
  두 ORM 객체를 모두 `session.add`한 뒤 `flush()` → `commit()`을 한 번만
  호출한다. 실패 시 `rollback()`을 호출해 두 변경 모두 취소한다(§2와
  동일한 순서).
- 트랜잭션 헬퍼는 `src/persistence/`에 두고, 어느 한 모듈이 다른 모듈의
  ORM을 직접 다루는 것을 정당화하지 않는다 — 헬퍼 자체는 여러 모듈의
  ORM을 알아도 되지만, 각 모듈의 `repository.py`는 여전히 자기 테이블만
  다룬다([persistence-boundaries.md](persistence-boundaries.md#persistence-module-responsibilities)의
  Persistence Module Responsibilities와 동일한 경계).
- Service 계층은 두 저장소를 직접 조합하는 대신 이 트랜잭션 헬퍼를
  주입받아 호출한다. 새로운 크로스 모듈 쓰기가 필요해지면(예: revision
  생성과 audit 이벤트 기록의 원자적 결합) 새 저장소 메서드를 조합하지
  말고, 그 조합 전용 트랜잭션 헬퍼를 추가한다.

## 4. Python/PHP commit 경계 정렬

**계약: PHP PDO 구현은 위 §1~§3과 동일한 지점에서 트랜잭션을 시작하고
끝낸다.** SQLAlchemy `AsyncSession`과 PDO는 API 이름이 다를 뿐, 트랜잭션
경계 자체는 언어에 무관하게 같은 자리에 있어야 한다.

| Python (`AsyncSession`) | PHP (`PDO`) | 시점 |
|---|---|---|
| (암묵적, `session.add` 이전엔 트랜잭션 없음) | `beginTransaction()` | 쓰기 메서드 진입 직후, 첫 `add`/구문 실행 전 |
| `session.add(orm)` / `session.execute(stmt)` | `$stmt->execute()`(prepared statement) | §2 순서의 1단계 |
| `session.flush()` | (PDO에는 별도 flush 없음 — `execute()` 자체가 즉시 반영) | §2 순서의 2단계. PDO 구현은 flush 단계를 생략하고 execute 직후 제약 위반 여부를 확인한다 |
| `session.commit()` | `commit()` | §2 순서의 3단계, 메서드당 정확히 한 번 |
| `session.rollback()` | `rollBack()` | §2 순서의 4단계, 통합 제약 위반 시 |

- 핵심 차이: SQLAlchemy는 `flush()`(검증)와 `commit()`(확정)이 분리돼
  있지만, PDO는 `execute()`가 곧바로 문을 실행하므로 별도 flush 단계가
  없다. PHP 구현은 `beginTransaction()` 이후 각 `execute()`가 던지는
  `PDOException`을 §2의 "2~3 사이 실패"와 동일하게 취급한다 — 즉 아직
  `commit()`을 부르지 않았다면 DB에는 확정되지 않은 상태이므로,
  `PDOException`을 잡아 `rollBack()`을 호출하는 지점은 Python의 "flush
  실패 시 rollback"과 같은 논리적 위치다.
  - MariaDB에서 DDL이 암묵적 커밋을 유발하는 것과 달리
    ([mariadb-compatibility-matrix.md §3](mariadb-compatibility-matrix.md#3-트랜잭션-매트릭스)),
    이 표는 DML(INSERT/UPDATE)에만 적용된다. DDL은 마이그레이션 범위이며
    이 문서가 다루는 저장소 트랜잭션 경계 밖이다.
- 크로스 모듈 트랜잭션 헬퍼(§3)도 동일하게 정렬된다: PHP 쪽 헬퍼는
  `beginTransaction()`을 한 번만 호출하고, 여러 `execute()`를 모은 뒤
  `commit()`을 한 번만 호출한다 — Python `DocumentRevisionTransaction`과
  같은 "여러 문, 단일 커밋" 구조.
- 이 표는 [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP SQL
  repository 골격을 작성할 때 그대로 따라야 할 경계다. PDO 드라이버
  선택이나 prepared statement 바인딩 방식 자체는
  [portable-query-builder-policy.md](portable-query-builder-policy.md)의
  범위이며 이 문서가 다루지 않는다.

## 이 정책을 만족하는 구현체

| 구현체 | 시점 | 언어/드라이버 | §1 (메서드=트랜잭션) | §2 (commit/rollback 시점) | §3 (크로스 모듈 헬퍼) |
|---|---|---|---|---|---|
| `DatabaseDocumentRepository` | 지금 | Python, SQLAlchemy `AsyncSession` | 만족 | 만족(`create`) | 해당 없음(단일 테이블) |
| `DatabaseRevisionRepository` | 지금 | Python, SQLAlchemy `AsyncSession` | 만족 | 만족(`try`/`except` 없이 flush→commit) | 해당 없음(단일 테이블) |
| `DocumentRevisionTransaction` | 지금 | Python, SQLAlchemy `AsyncSession` | 해당 없음(헬퍼 자체가 §3 대상) | 만족(`create_document_with_revision`) | 만족 |
| PHP SQL repository 골격 | [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 | PHP, PDO | 이 문서의 §1~§2를 따라야 함 | §4 표를 따라야 함 | §4 표를 따라야 함 |

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — 이 문서가 확정을 미룬
  §2(commit/rollback 존재)의 원출처.
- [Persistence Boundaries](persistence-boundaries.md) — 세션 소유권,
  `DocumentRevisionTransaction` 사용 예시(Cross-Module Transactions)의
  원출처.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) —
  DDL의 암묵적 커밋 등 트랜잭션 관련 PostgreSQL/MariaDB 차이.
- [0474 portable duplicate key handling](php-db-ui-micro-job-prompts-0351-0670.md) —
  rollback 이후 어떤 예외를 도메인 예외로 바꾸는지 확정하는 후속 문서.
