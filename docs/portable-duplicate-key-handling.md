# Portable Duplicate Key Handling

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Contract §3](db-adapter-contract.md#3-통합-제약-위반-신호)이
"어댑터는 제약 위반을 하나의 통합 신호로 전달해야 한다"는 존재만 확정하고
미뤄둔 **"위반된 제약을 구체적으로 어떻게 식별하는가"**를 이 문서가
확정한다. 이 문서는 정책 선언이며, `src/modules/document/repository.py`
등 기존 코드를 바꾸지 않는다 — 실제 구현 반영과 테스트 보강은
[0475 document duplicate handling test](php-db-ui-micro-job-prompts-0351-0670.md)의
범위다.

## 목적

지금 `DatabaseDocumentRepository.create`는 다음과 같이 `IntegrityError`를
잡는다.

```python
except IntegrityError as e:
    await self.session.rollback()
    if "normalized_title" in str(e):
        raise DuplicateNormalizedTitleError(...)
    raise
```

`str(e)`에는 원본 SQL 문(`INSERT INTO document (..., normalized_title, ...)
VALUES (...)`)과 psycopg2가 반환한 원본 에러 메시지가 그대로 이어붙는다.
`"normalized_title"`이라는 부분 문자열은 **컬럼 이름이 SQL 문 자체에 항상
등장하기 때문에** 매칭에 성공할 뿐, 실제로 유일성 제약이 위반됐는지와는
무관하다 — 예를 들어 같은 INSERT 문에서 FK 위반이나 NOT NULL 위반이 나도
SQL 문 텍스트에 `normalized_title`이 포함돼 있으면 (컬럼 순서에 따라)
오탐할 여지가 있고, 반대로 드라이버나 로케일에 따라 에러 메시지 문형이
달라지면 매칭이 깨진다. PHP `PDOException->getMessage()`는 형식이 전혀
다르므로 이 매칭은 그대로 이식할 수 없다. 이 문서는 두 언어/두 DB에서
동일하게 동작하는 식별 방법을 고정해, 0475가 코드에 반영할 기준을
남긴다.

## 적용 범위

적용 대상:

- `src/modules/*/repository.py`의 Database* 구현체가 `UNIQUE` 제약 위반을
  도메인 예외(`DuplicateNormalizedTitleError` 등)로 변환하는 모든 지점.
- [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후 PHP PDO 기반 SQL
  repository의 동일한 변환 지점.

적용되지 않는 것:

- FK/NOT NULL/CHECK 등 유일성 외 제약 위반의 처리 —
  [db-adapter-contract.md §3](db-adapter-contract.md#3-통합-제약-위반-신호)이
  다루는 "통합 신호로 받는다"는 존재 확인 이상은 이 문서의 범위가 아니다.
  FK 위반의 portability 테스트는 [0476](php-db-ui-micro-job-prompts-0351-0670.md)의
  범위다.
- commit/rollback을 호출하는 시점 자체 —
  [repository-transaction-policy.md](repository-transaction-policy.md)가
  이미 확정했다. 이 문서는 그 rollback 이후 "어떤 예외를 도메인 예외로
  바꾸는가"만 다룬다.
- 실제 코드 변경(`repository.py`의 `except` 블록 수정) — 이 문서가 정한
  정책을 코드에 반영하고 검증하는 것은
  [0475](php-db-ui-micro-job-prompts-0351-0670.md)의 범위다.

## 1. 금지: DB별 오류 메시지 문자열 매칭

**정책: 예외의 문자열 표현(`str(e)`, `e.args`의 자유 텍스트, PHP
`PDOException::getMessage()`)에 대해 "포함 여부"나 부분 문자열 검색으로
제약 위반을 식별하지 않는다.**

이유:

- 메시지 문형은 DB 벤더, 드라이버, 서버/클라이언트 로케일에 따라 달라진다
  (예: PostgreSQL은 `duplicate key value violates unique constraint
  "uq_document_normalized_title"`, MariaDB는 `Duplicate entry '...' for
  key 'uq_document_normalized_title'` — 단어 자체가 다르다).
- SQLAlchemy의 `str(IntegrityError)`는 원본 SQL 문과 파라미터까지 포함하므로,
  컬럼 이름 부분 문자열 매칭은 "그 컬럼이 제약을 위반했다"가 아니라 "그
  컬럼이 실행된 SQL 문에 등장했다"만을 보장한다 — 다른 제약 위반과
  오탐/미탐이 뒤섞일 수 있다.
- PHP `PDOException`의 메시지 형식은 SQLAlchemy와 전혀 다르므로, 이 방식은
  애초에 이식되지 않는다.

## 2. 위반 종류 식별: SQLSTATE 클래스

**정책: "제약 위반이 유일성(duplicate key) 위반인지"는 SQLSTATE 코드로
판별한다. 메시지 텍스트가 아니라 구조화된 에러 코드를 본다.**

SQLSTATE는 ANSI SQL 표준이 정의하며 PostgreSQL과 MariaDB가 동일한 클래스
체계를 따른다 — [MariaDB Compatibility
Matrix](mariadb-compatibility-matrix.md#3-트랜잭션-매트릭스)가 이미
"표준 오류 클래스로 판단한다"고 전제한 원칙을 여기서 구체화한다.

| 상황 | PostgreSQL | MariaDB | 판별 기준 |
|---|---|---|---|
| 유일성 제약(UNIQUE/PK) 위반 | SQLSTATE `23505` | SQLSTATE `23000`, 드라이버 errno `1062` | SQLSTATE 클래스 `23`(integrity constraint violation) 전체가 아니라, 유일성 위반만 좁혀 판별하려면 PostgreSQL은 정확한 코드 `23505`를, MariaDB는 SQLSTATE `23000` + errno `1062`(Duplicate entry) 조합을 함께 본다 — MariaDB의 `23000`은 FK 위반(`1216`/`1217`/`1451`/`1452`)과 NOT NULL 위반(`1048`) 등 다른 위반과 공유되므로 errno 없이는 좁혀지지 않는다 |

- Python(SQLAlchemy): `IntegrityError.orig`가 드라이버 예외를 감싼다.
  psycopg는 `exc.orig.sqlstate`(또는 `exc.orig.diag.sqlstate`)로, PyMySQL/
  mysqlclient는 `exc.orig.args[0]`(errno, 예: `1062`)로 구조화된 코드를
  노출한다 — 둘 다 메시지 텍스트가 아니라 속성 접근이다.
- PHP: `PDOException::errorInfo`가 `[SQLSTATE, driver_code,
  driver_message]` 3-튜플을 돌려준다. `errorInfo[0]`(SQLSTATE)과
  `errorInfo[1]`(driver_code)을 위 표와 동일하게 판별에 쓴다.
  `errorInfo[2]`(driver_message)는 사람이 읽기 위한 텍스트일 뿐 판별에
  쓰지 않는다.
- 이 판별 로직(코드 표 → "유일성 위반 여부" 불리언)은 DB adapter 계층
  하나에만 존재해야 한다 — [db-adapter-contract.md
  §3](db-adapter-contract.md#3-통합-제약-위반-신호)이 요구하는 "통합된
  신호"가 바로 이 불리언이다. 각 모듈 `repository.py`는 이 신호만 받고,
  SQLSTATE나 errno 값 자체를 알 필요가 없다.

## 3. 위반된 제약 식별: 제약 이름

**정책: 유일성 위반이 확인되면, "어떤 제약이 위반됐는가"는 제약 **이름**으로
판별한다. [portable-schema-naming-policy.md
§4](portable-schema-naming-policy.md#4-인덱스제약-이름-패턴)가 이미
`uq_<table>_<column>` 패턴(예: `uq_document_normalized_title`)을
강제하므로, 이 이름이 도메인 예외로의 매핑 키가 된다.**

```python
# 정책이 요구하는 형태 (예시 — 실제 반영은 0475)
UNIQUE_VIOLATION_TO_ERROR = {
    "uq_document_normalized_title": DuplicateNormalizedTitleError,
}

constraint_name = extract_constraint_name(exc.orig)  # 드라이버별 구조화 접근, 아래 참고
error_cls = UNIQUE_VIOLATION_TO_ERROR.get(constraint_name)
if error_cls is not None:
    raise error_cls(f"...")
raise  # 매핑에 없는 유일성 위반은 원본 예외를 그대로 전파한다
```

제약 이름을 얻는 방법도 메시지 문자열 전체를 대상으로 한 자유 검색이
아니라, 각 드라이버가 구조적으로 제공하는 위치에서 읽는다:

- **PostgreSQL(psycopg)**: `exc.orig.diag.constraint_name`이 제약 이름을
  그대로 준다 — 파싱이 필요 없는 구조화된 필드다.
- **MariaDB(PyMySQL/mysqlclient)**: 드라이버가 별도 필드를 주지 않으므로,
  `Duplicate entry '...' for key 'uq_document_normalized_title'` 메시지에서
  마지막 `'...'`로 감싸인 토큰만 정규식으로 추출한다. 이는 §1이 금지하는
  "메시지 포함 여부 매칭"과 다르다 — 매칭 대상이 메시지의 자유 텍스트가
  아니라, [portable-schema-naming-policy.md](portable-schema-naming-policy.md)가
  이미 고정한 예측 가능한 식별자(제약 이름) 하나뿐이고, 그 식별자가 등장하는
  위치(마지막 따옴표 쌍)는 MariaDB 에러 포맷 문서가 보장하는 고정 형식이다.
  단어 순서나 언어(로케일)가 바뀌어도 이 위치는 바뀌지 않는다.
- **PHP(PDO, MariaDB/PostgreSQL 공통)**: `errorInfo[2]`(driver_message)에서
  동일한 규칙으로 제약 이름 토큰만 추출한다. PostgreSQL PDO 드라이버는
  메시지에 `"uq_..."` 형태로 제약 이름을 포함하므로 동일한 정규식 접근이
  두 DB에서 통일된다.
- 위 세 경로 모두 최종적으로 "제약 이름 문자열 하나"를 얻는 것이 목적이다.
  그 이후(§3 표 조회)는 DB/언어에 무관하게 동일한 로직이다 — 제약 이름을
  얻는 방법만 드라이버별로 다르고, 그 뒤의 도메인 예외 매핑은 완전히
  portable하다.

## 4. 매핑에 없는 위반: 원본 예외 재전파

**정책: `UNIQUE_VIOLATION_TO_ERROR`류 매핑에 없는 제약 이름은 도메인
예외로 감싸지 않고 원본 예외(`IntegrityError`/`PDOException`)를 그대로
다시 던진다.** 새 유일성 제약을 추가한 모듈이 매핑 등록을 잊었을 때 이를
조용히 삼키지 않고 눈에 띄게 실패하게 하기 위함이다 — §2의 `raise`(매핑
없음)가 이 규칙이다.

## 이 정책을 만족하는 구현체

| 구현체 | 시점 | §1 (메시지 매칭 금지) | §2 (SQLSTATE/errno 판별) | §3 (제약 이름 매핑) |
|---|---|---|---|---|
| `DatabaseDocumentRepository.create` | 지금 | 미충족 — `"normalized_title" in str(e)` 사용 중 | 미충족 | 미충족 |
| `DatabaseDocumentRepository.create` | [0475](php-db-ui-micro-job-prompts-0351-0670.md) 이후 | 이 문서를 따라야 함 | 이 문서를 따라야 함 | 이 문서를 따라야 함 |
| PHP document SQL repository | [0487](php-db-ui-micro-job-prompts-0351-0670.md) 이후 | 이 문서를 따라야 함 | 이 문서를 따라야 함 | 이 문서를 따라야 함 |

## 이 문서 이후 단계

- **0475**([document duplicate handling
  test](php-db-ui-micro-job-prompts-0351-0670.md)): `DatabaseDocumentRepository.create`의
  예외 처리를 이 정책대로 바꾸고, SQLSTATE/errno/제약 이름 기반 판별을
  error code 중심 테스트로 검증한다.
- **0476**([portable FK behavior
  tests](php-db-ui-micro-job-prompts-0351-0670.md)): 이 문서가 다루지 않은
  FK 위반의 판별/재시도 정책을 별도로 확정한다.
- **0487** 이후: PHP document SQL repository가 §3의 PDO `errorInfo` 접근
  방식을 그대로 구현한다.

## 관련 문서

- [DB Adapter Contract §3](db-adapter-contract.md#3-통합-제약-위반-신호) —
  이 문서가 확정을 미룬 "통합 제약 위반 신호"의 원출처.
- [Repository Transaction Policy](repository-transaction-policy.md) —
  rollback을 호출하는 시점(이 문서가 다루는 예외 변환보다 앞선 단계).
- [Portable Schema Naming Policy
  §4](portable-schema-naming-policy.md#4-인덱스제약-이름-패턴) — 이 문서가
  식별 키로 쓰는 `uq_<table>_<column>` 제약 이름 패턴의 원출처.
- [MariaDB Compatibility
  Matrix](mariadb-compatibility-matrix.md#3-트랜잭션-매트릭스) — "표준
  오류 클래스로 판단한다"는 원칙이 처음 언급된 곳.
- [User Portable Repository
  Plan](user-portable-repository-plan.md) — `user_block.account_id` 등
  다른 모듈의 유일성 위반도 이 문서와 동일한 방식으로 변환돼야 한다는
  전제.
