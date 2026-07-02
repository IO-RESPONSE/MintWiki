# Portable LIKE Search Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)가 금지한 `ILIKE` 연산자의 대체 방식을
구체화하고, [Portable Text Collation Policy](portable-text-collation-policy.md)의
"대소문자 비구분 검색" 항목을 확정한다. 이 문서는 정책 선언이며, 기존 코드를 지금 바꾸지
않는다 — 이 정책이 요구하는 패턴을 새로 추가될 검색 쿼리에 적용할 규칙을 명문화하는 것이다.

## 목적

PostgreSQL의 `ILIKE`는 대소문자를 무시한 패턴 매칭을 하는 연산자다. MariaDB는 이와 동등한
연산자가 없다 — `LIKE`는 항상 기본 collation을 따르는데, 기본 collation이 대소문자를 구분하는
`utf8mb4_bin`이면 대소문자 차이를 무시할 수 없다.
[Portable Text Collation Policy](portable-text-collation-policy.md)에 따라 모든 문자열 컬럼의
collation을 `utf8mb4_bin`(대소문자 구분)으로 고정했으므로, 대소문자를 무시한 검색이 필요한 경우에는
**애플리케이션 계층에서 값을 정규화한 뒤 비교**하는 방식을 써야 한다. 이 문서는 그 정규화 방식
두 가지(정규화된 컬럼, 함수 기반 비교)와 각각의 적용 시점을 정의한다.

## 적용 범위

이 정책은 아래가 정의하는 대소문자 무시 검색(`ILIKE` 대체)에 적용된다.

- `src/modules/*/repository.py` (저장소 어댑터)에서 대소문자 무시 패턴 매칭이 필요한 쿼리.
- `src/modules/*/service.py` (서비스 계층)에서 사용자 입력을 정규화해 저장소에 전달하는 로직.
- `migrations/versions/` 아래 Alembic 마이그레이션이 만드는 정규화 컬럼(스키마 정의).
- 추후 추가될 portable SQL 스키마 원본(0461 이후 `db/schema` 잡).

적용되지 않는 것:

- 이미 대소문자를 구분하지 않는 용도로 설계된 기존 컬럼(`document.normalized_title`처럼
  정규화가 이미 저장되는 경우). 이미 정규화 컬럼이 있으면 정책 1을 쓴다.
- 전문 검색(full-text search) — [search-adapter-design.md](search-adapter-design.md)와
  [portable-search-db-boundary.md](portable-search-db-boundary.md)에서 별개로 다룬다.
- ID나 숫자 컬럼처럼 대소문자 비교가 실질적으로 의미 없는 경우.

## 정책 1: 정규화된 컬럼 + `LIKE` (권장)

**적용 시점:** 동일 엔티티 내에서 대소문자 무시 검색이 자주 필요한 경우.

**패턴:** 원본 컬럼과 정규화된 컬럼(소문자)을 함께 유지한다.

```python
# 저장소 모델 (src/persistence/models.py)
class DocumentORM(Base):
    __tablename__ = "document"
    id = Column(String(255), primary_key=True)
    title = Column(String(500), nullable=False)  # 원본 (사용자 입력)
    normalized_title = Column(String(500), nullable=False, unique=True)  # 소문자 정규화
    # ...

# 저장소 쿼리 (src/modules/document/repository.py)
async def get_by_title_case_insensitive(self, title: str) -> Optional[Document]:
    """제목으로 문서를 검색한다 (대소문자 무시)."""
    normalized = title.lower().strip()
    stmt = select(DocumentORM).where(DocumentORM.normalized_title == normalized)
    result = await self.session.execute(stmt)
    row = result.scalar_one_or_none()
    return self._to_domain(row) if row else None
```

**장점:**
- 쿼리가 단순하다 (`= normalized_title`).
- 인덱스가 정규화 컬럼에 자동으로 적용된다 (성능 좋음).
- 정규화 로직이 투명하다 (컬럼이 이미 정규화된 값을 저장).

**단점:**
- 정규화 컬럼 추가로 테이블 폭이 늘어난다.
- INSERT/UPDATE 시 두 컬럼을 함께 유지해야 한다.

**기존 예시:** `document.normalized_title`은 이미 이 패턴을 쓴다
([persistence-boundaries.md](persistence-boundaries.md) 참고).

## 정책 2: 함수 기반 비교 (`LOWER()` + `LIKE`)

**적용 시점:** 대소문자 무시 검색이 드물거나 정규화 컬럼 추가가 비용이 큰 경우.

**패턴:** 쿼리 시점에 `LOWER()` 함수를 써 양쪽 값을 소문자로 변환해 비교한다.

```python
# 저장소 쿼리 (src/modules/document/repository.py)
from sqlalchemy import func

async def search_by_keywords_case_insensitive(
    self, keyword: str
) -> list[Document]:
    """키워드로 문서를 검색한다 (대소문자 무시, 부분 매칭)."""
    pattern = f"%{keyword.lower()}%"
    # LOWER()를 컬럼과 값 양쪽에 적용
    stmt = select(DocumentORM).where(
        func.lower(DocumentORM.title).like(pattern)
    )
    result = await self.session.execute(stmt)
    rows = result.scalars().all()
    return [self._to_domain(row) for row in rows]
```

**ANSI SQL 호환성:** `LOWER()` 함수와 `LIKE` 연산자 모두 ANSI 표준이므로
PostgreSQL과 MariaDB 양쪽에서 동일하게 동작한다.

**장점:**
- 정규화 컬럼 추가 없이 기존 컬럼만으로 검색 가능.
- 스키마 변경이 필요 없다 (기존 테이블에 적용 가능).

**단점:**
- 모든 행에 `LOWER()` 함수를 적용하므로 성능이 낮다 (인덱스 사용 불가).
- 대소문자 무시 검색이 자주 있으면 정책 1로 전환하는 것을 권장한다.

## 정책 3: Collation 변경 (제한적)

**적용 시점:** 특정 컬럼이 "항상" 대소문자를 구분하지 않아야 하는 경우
(매우 드문 경우).

**패턴:** 컬럼 collation을 MariaDB의 `utf8mb4_general_ci` 또는 `utf8mb4_unicode_ci`로
설정한다.

```sql
-- 마이그레이션 (migrations/versions/XXXX_add_case_insensitive_column.py)
def upgrade():
    op.add_column(
        'entity',
        sa.Column(
            'display_name',
            sa.String(255),
            mysql_collation='utf8mb4_unicode_ci'  # MariaDB 전용
        )
    )

def downgrade():
    op.drop_column('entity', 'display_name')
```

**경고:**
- `utf8mb4_unicode_ci` collation은 PostgreSQL과 MariaDB에서 정렬/비교 결과가 **동일하지 않을 수 있다**.
- [Portable Text Collation Policy](portable-text-collation-policy.md#2-기본-collation-utf8mb4_bin-mariadb-대소문자-구분)가
  모든 컬럼의 기본 collation을 `utf8mb4_bin` (대소문자 구분)으로 정의했으므로,
  이를 변경하려면 명확한 이유와 문서화가 필수다.
- 향후 데이터 이식/검증 시 collation 차이로 인한 부작용(UNIQUE 제약, 정렬 순서)을
  별도로 처리해야 한다.

**이 정책은 정책 1, 2로 불가능할 때만 마지막 수단이다.**

## 정책 간 선택 기준

| 상황 | 권장 정책 | 이유 |
|---|---|---|
| 정규화 검색이 자주 필요 (예: document 제목) | 정책 1 (정규화 컬럼) | 성능, 투명성 |
| 임시/한 번짜리 검색 | 정책 2 (`LOWER()` 함수) | 스키마 변경 최소화 |
| 애플리케이션이 이미 정규화된 값만 저장 | 정책 1 (기존 컬럼 사용) | 기존 패턴 유지 |
| 모든 비교가 대소문자 무시여야 함 | 정책 3 (collation 변경, 신중함) | 마지막 수단 — 이식성 주의 |

## 예시

### 예시 1: Document 제목 검색 (정책 1)

이미 구현되어 있다:

```python
# src/modules/document/repository.py
async def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
    """정규화된 제목으로 문서를 조회한다."""
    stmt = select(DocumentORM).where(DocumentORM.normalized_title == normalized_title)
    result = await self.session.execute(stmt)
    return self._to_domain(result.scalar_one_or_none())

# src/modules/document/service.py
async def get_by_title(self, title: str) -> Optional[Document]:
    """제목으로 문서를 조회한다 (대소문자 무시)."""
    normalized = title.lower().strip()  # 서비스 계층에서 정규화
    return await self.repository.get_by_normalized_title(normalized)
```

### 예시 2: 키워드 검색 (정책 2)

`search` 모듈이 필요로 하는 경우:

```python
# src/modules/search/repository.py (DB fallback adapter)
from sqlalchemy import func

async def search_documents_by_keyword(
    self, keyword: str
) -> list[Document]:
    """키워드로 문서 제목/요약을 검색한다 (대소문자 무시)."""
    pattern = f"%{keyword.lower()}%"
    stmt = (
        select(DocumentORM)
        .where(
            func.lower(DocumentORM.title).like(pattern)
            | func.lower(DocumentORM.summary).like(pattern)
        )
    )
    result = await self.session.execute(stmt)
    return [self._to_domain(row) for row in result.scalars().all()]
```

## ILIKE와의 차이

| 항목 | PostgreSQL `ILIKE` | 정책 1 (정규화 컬럼) | 정책 2 (`LOWER()`) |
|---|---|---|---|
| 문법 | `title ILIKE 'test%'` | `normalized_title = 'test...'` | `LOWER(title) LIKE 'test%'` |
| 성능 | 인덱스 사용 가능 | 인덱스 사용 (정규화 컬럼) | 인덱스 사용 불가 |
| 스키마 | 변경 없음 | 정규화 컬럼 추가 필요 | 변경 없음 |
| PostgreSQL | ✓ 지원 | ✓ (수동 정규화) | ✓ (LOWER 함수) |
| MariaDB | ✗ 미지원 | ✓ (정규화된 값 저장) | ✓ (LOWER 함수) |

## 이 문서 이후 단계

- **0447**: [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md)의 `ILIKE` 금지와
  함께 코드에서 `ILIKE` 키워드 사용을 자동 검사하는 스크립트에 포함한다.
  정책 2의 `LOWER()` 함수 사용이 정책 1로 전환할 기회인지를 코드 리뷰에서 판단한다.
- **0479**([Portable Search DB Boundary](portable-search-db-boundary.md)):
  정책 2(`LOWER()` 함수 기반 검색)가 DB fallback adapter(`search` 모듈)의
  기본 경로로 어떻게 구현되는지 정의한다.
- **향후**: 대소문자 무시 검색이 본격화되면, 정책 1로 정규화 컬럼을 추가하는 스키마
  마이그레이션을 평가한다 (성능 최적화).

## 관련 문서

- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — `ILIKE` 금지 항목의 원출처.
  이 문서가 그 금지 목록의 대체 방식을 구체화한다.
- [Portable Text Collation Policy](portable-text-collation-policy.md) — 컬럼 collation
  정책. 정책 3의 전제(기본 collation `utf8mb4_bin`)와 정책 2의 부작용(collation 변경 금지)을
  정의한다. 대소문자 비구분 검색 항목([정책 2](#이-문서-이후-단계))에서
  이 문서로 위임했다.
- [Portable ID Column Policy](portable-id-column-policy.md) — 정책 1의 실제 적용 사례가
  정규화되지 않은 ID를 다루는 방식.
- [Persistence Boundaries](persistence-boundaries.md) — `document.normalized_title`과
  정규화 패턴의 원출처. 정책 1의 기본 예시다.
- [Search Adapter Design](search-adapter-design.md) — 대소문자 무시 검색의 어댑터
  계층에서의 역할.
- [Portable Search DB Boundary](portable-search-db-boundary.md) — DB fallback
  adapter에서 정책 2를 구현하는 경계.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — collation
  차이의 원점 데이터.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.
