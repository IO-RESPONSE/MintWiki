# DB Adapter Selection Guide

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.

이 문서는 Python, PHP, 공용 웹호스팅이라는 배포 환경별로 **어떤 DB adapter를
선택할 것인가**에 대한 의사결정 기준을 제공한다. 모든 환경은
[db-adapter-contract.md](db-adapter-contract.md)가 정의한 동일한 계약을
만족해야 한다 — 이 문서는 그 계약을 구현하는 **방식**이 환경별로 어떻게
달라지는지를 설명한다.

## 목적과 범위

- **대상**: 각 배포 환경에서 DB 연결을 설계하고 구현할 때 adapter 선택의
  근거를 제시해야 하는 사람.
- **다루는 것**:
  - Python 개발 환경 (로컬 + CI) — SQLAlchemy AsyncSession adapter
  - PHP 구현 — PDO + 드라이버별 차이
  - 공용 웹호스팅 — 제약 기반 선택과 트레이드오프
  - 각 선택이 [db-adapter-contract.md](db-adapter-contract.md) 계약을
    만족하는지 검증 기준

- **다루지 않는 것**:
  - 계약 정의 자체 —
    [db-adapter-contract.md](db-adapter-contract.md)에서 다룬다.
  - 특정 adapter 구현체의 상세 코드 —
    [0450](php-db-ui-micro-job-prompts-0351-0670.md)(Python skeleton),
    [0484](php-db-ui-micro-job-prompts-0351-0670.md) 이후(PHP PDO)에서
    다룬다.
  - 성능 튜닝이나 연결 풀 관리 —
    프로덕션 운영 문서에서 다룬다.

## 배포 환경별 선택 매트릭스

### Python: SQLAlchemy AsyncSession (개발 + CI 기본)

**선택 근거**:

- SQLAlchemy는 이미 프로젝트 의존성에 포함되어 있다.
- 비동기 지원(`AsyncSession`)으로 FastAPI와 자연스럽게 통합된다.
- PostgreSQL과 MariaDB 모두 지원하는 드라이버
  (`postgresql+asyncpg://`, `mysql+aiomysql://`)가 존재한다.
- 로컬 개발과 CI 환경에서 구현체를 공용할 수 있다.

**adapter 구현**:

```python
class SqlAlchemyDbAdapter(DbAdapter):
    """SQLAlchemy AsyncSession을 DbAdapter 계약으로 감싼다.
    
    이 어댑터는 python/src/persistence/adapters/ 아래 위치한다 (0450).
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, row: object) -> None:
        self._session.add(row)

    async def fetch_one(self, statement: object) -> Optional[object]:
        return await self._session.scalar(statement, execution_options={"synchronize_session": False})

    async def fetch_all(self, statement: object) -> list[object]:
        result = await self._session.scalars(statement)
        return result.all()

    async def execute(self, statement: object) -> None:
        await self._session.execute(statement)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

**설정**:

- PostgreSQL (로컬 개발): `WIKI_DATABASE_URL=postgresql://localhost/wiki_engine`
- PostgreSQL (CI): 마찬가지로 위 형식, CI 환경 변수에서 주입
- MariaDB 테스트: `WIKI_MARIADB_DSN=mysql://root@localhost:3306/wiki_engine`
  (0470 이후 차량 실제 드라이버 전환)

**제약 위반 신호 처리**:

- SQLAlchemy의 `IntegrityError`를 잡아
  [0474 portable duplicate key handling](portable-duplicate-key-handling.md)
  정책에 따라 도메인 예외로 변환한다.
- 에러 메시지 문자열 매칭은
  [portable-schema-naming-policy.md](portable-schema-naming-policy.md)의
  예측 가능한 제약 이름에 의존할 수 있다.

### PHP: PDO + 드라이버별 분기 (웹호스팅 친화적)

**선택 근거**:

- PHP 표준 라이브러리에 포함되므로 외부 의존성이 필요 없다.
- 공용 웹호스팅에서 보편적으로 지원된다 (ext-pdo, ext-pdo-mysql,
  ext-pdo-pgsql).
- 동기 모델만 지원하므로 복잡한 비동기 런타임이 필요 없다.
- 간단한 트랜잭션 제어로 계약을 만족할 수 있다.

**adapter 구현**:

```php
class PdoDbAdapter implements DbAdapter {
    private PDO $connection;
    private SqlDialect $dialect;

    public function __construct(PDO $connection, SqlDialect $dialect) {
        $this->connection = $connection;
        $this->dialect = $dialect;
    }

    public function add($row): void {
        // PHP는 ORM 모델 개념이 약하므로 실제 INSERT 쿼리는
        // PHP repository 계층에서 처리하고, adapter는 execute()로
        // 위임한다(0487 이후 확정).
        throw new \BadMethodCallException('add() is not supported in PHP — use execute() for INSERT');
    }

    public function fetchOne($statement): ?object {
        $stmt = $this->connection->prepare($statement);
        $stmt->execute();
        return $stmt->fetchObject();
    }

    public function fetchAll($statement): array {
        $stmt = $this->connection->prepare($statement);
        $stmt->execute();
        return $stmt->fetchAll(PDO::FETCH_OBJ);
    }

    public function execute($statement): void {
        $this->connection->exec($statement);
    }

    public function commit(): void {
        $this->connection->commit();
    }

    public function rollback(): void {
        $this->connection->rollBack();
    }
}
```

**설정**:

- PostgreSQL: `$dsn = 'pgsql:host=localhost;port=5432;dbname=wiki_engine'`
- MariaDB: `$dsn = 'mysql:host=localhost;port=3306;dbname=wiki_engine;charset=utf8mb4'`
- 드라이버 선택은 DSN 스킴(pgsql vs mysql)으로 결정된다.

**제약 위반 신호 처리**:

- `PDOException`을 잡아 위와 동일한 0474 정책으로 변환한다.
- PHP에서는 SQLSTATE 코드(`23000` = 무결성 제약) 또는 에러 메시지 파싱으로
  식별할 수 있다.

### 공용 웹호스팅: PHP + 파일/간단 저장소 (제약 기반)

**선택 근거**:

- 환경 변수 지원이 불안정하거나 불가능한 경우가 많다.
- 비동기/스레딩 지원이 제한적이다.
- 관리자가 데이터베이스와 권한을 사전 구성해 준다.

**adapter 선택 규칙**:

1. **DB 연결 설정**:
   - 환경 변수 `WIKI_DATABASE_URL` 또는 `WIKI_MARIADB_DSN`이 있으면 그것을
     사용한다.
   - 없으면 설정 파일(`config/database.php` 등)에서 읽는다
     ([php-db-config.md](php-db-config.md) 참고).
   - 관리자가 제공한 접속 정보를 설정 파일에 입력한다.

2. **대체 저장소** (선택적, DB 연결 불가 시):
   - Jobs: 파일 기반 queue (JSON 파일, 임시 디렉터리)로
     폴백한다 (0516 부분).
   - Cache: 로컬 메모리 캐시(세션 종료 시 소실) 또는 파일 기반.
   - Session: PHP 내장 파일 기반 세션 저장소.

3. **migration 권한 제약**:
   - 웹호스팅 계정이 DDL 권한을 갖지 못할 수 있다.
   - Installer는 schema version 테이블(read-only 필드 제약)만
     확인한다 (0518).
   - 초기 스키마 생성은 호스팅 제공자(cPanel, Plesk 등)의 관리 도구나
     수동 SQL 실행으로 준비한다.

**구체 예시**:

```php
// config/database.php (환경 변수 없을 때)
return [
    'driver' => 'mysql',  // 또는 'pgsql'
    'host' => '호스팅제공자-db-host.example.com',
    'port' => 3306,
    'database' => 'account_wiki',
    'username' => 'account_user',
    'password' => getenv('DB_PASSWORD'), // .htaccess 또는 제공자 설정
];

// bootstrap에서:
$config = require 'config/database.php';
$connection = PdoConnectionFactory::connect($config);
$adapter = new PdoDbAdapter($connection, SqlDialect::fromDriver($config['driver']));
```

## 환경별 계약 준수 체크리스트

각 adapter가 [db-adapter-contract.md](db-adapter-contract.md) 계약을 만족하는지
확인:

### Python (SQLAlchemy AsyncSession)

- [ ] §1 연결/세션 소유권: Repository 생성자에 AsyncSession 주입받음
  (`DatabaseDocumentRepository.__init__(self, session: AsyncSession)`)
- [ ] §2 최소 동작 집합: add/fetch_one/fetch_all/execute/commit/rollback 모두 구현
- [ ] §3 통합 제약 위반: IntegrityError를 하나의 신호로 잡아 변환
  (0474에서 확정)
- [ ] §4 드라이버 타입 격리: Repository 상위로 Row/scalar 원본 타입을 반환하지
  않음

### PHP (PDO)

- [ ] §1 연결/세션 소유권: bootstrap 계층에서 PDO 생성, Repository에 주입
- [ ] §2 최소 동작 집합: fetchOne/fetchAll/execute/commit/rollback 구현
  (add는 ORM 부재로 인해 PHP 저장소에서 직접 쿼리)
- [ ] §3 통합 제약 위반: PDOException을 하나의 신호로 잡아 변환
- [ ] §4 드라이버 타입 격리: PDOStatement, row object 원본을 상위로 노출하지 않음

### 공용 웹호스팅 (PHP + 파일/제약)

- [ ] §1 연결/세점 소유권: Installer/bootstrap 계층에서 설정 파일 읽음
  (관리자 사전 구성)
- [ ] §2 최소 동작: DB 연결 가능 시 PHP adapter와 동일. 불가 시 대체 저장소로
  폴백
- [ ] §3 제약 위반: DB 연결 가능 시 PHP adapter와 동일. 파일 저장소는 고유
  오류 처리
- [ ] §4 격리: PHP adapter와 동일 격리 정책

## 드라이버 선택: PostgreSQL vs MariaDB

모든 adapter는 두 DB 모두를 지원해야 한다:

| 환경 | 기본 | 대체 | 선택 기준 |
|---|---|---|---|
| Python 로컬 개발 | PostgreSQL | MariaDB (0470 이후) | 개발자 선호, CI 일관성 |
| Python CI | PostgreSQL | MariaDB (테스트 추가) | 두 DB 모두 테스트 (0452-0453) |
| PHP 로컬 개발 | PostgreSQL 또는 MariaDB | (둘 다 지원) | 대상 호스팅 환경 일치 |
| 웹호스팅 | MariaDB (주류) | PostgreSQL (일부) | 호스팅 제공자 지원 여부 |

**기준**:

- **PostgreSQL**: 로컬/CI 개발 기본, 고급 기능(CTE, 윈도우 함수) 많음, 하지만
  호스팅에서 제한적.
- **MariaDB**: 웹호스팅 광범위 지원, ANSI SQL + MariaDB 10.6+ 기본 기능만
  사용 시 이식 용이.

## 드라이버 능력 모델 (Capability Model)

[0472 DB driver capability model](php-db-ui-micro-job-prompts-0351-0670.md)에서
확정하겠지만, 미리 고려할 사항:

| 기능 | PostgreSQL | MariaDB 10.6+ |
|---|---|---|
| RETURNING 절 | 지원 | 8.0.20+ (일부 호스팅 미포함) |
| JSON 네이티브 | JSONB 지원 (금지함, 0441) | JSON 기본 (금지함) |
| 전문 검색 | ts_vector (금지함) | 아님 (0479 search adapter 뒤로) |
| 트랜잭션 DDL | 지원 | 미지원 (암묵적 커밋) |

## 결정 흐름도

```
당신의 배포 환경은?

┌─ Python 로컬 개발
│  └─> SQLAlchemy AsyncSession adapter
│      (선택) PostgreSQL 또는 MariaDB
│      See: src/app/database.py, 0450

├─ Python CI/테스트
│  └─> SQLAlchemy AsyncSession adapter
│      필수: PostgreSQL + MariaDB 양쪽 테스트 (0452-0453)
│      See: scripts/test.sh, .github/workflows/

├─ PHP 로컬 개발
│  └─> PDO adapter
│      (선택) PostgreSQL 또는 MariaDB
│      (선택) 호스팅 환경과 일치시키기
│      See: php/src/Persistence/, 0484+

├─ 웹호스팅 (PHP)
│  └─> PDO adapter
│      기본: MariaDB 10.6+
│      설정: config/database.php (환경 변수 우선)
│      대체: 파일 기반 store (DB 연결 불가 시)
│      See: php-db-config.md, 0509

└─ 상세 불명
   └─> 이 문서의 §매트릭스부터 시작
```

## 마이그레이션 및 테스트 고려사항

### Python ↔ PHP 전환 (0484+)

- 두 구현이 동일 adapter 계약을 만족해야 한다.
- Python 테스트 fixture를 PHP와 공용한다 (0490-0492).
- 드라이버 능력 차이는 adapter 뒤로 숨긴다 (0472).

### 로컬 PostgreSQL ↔ 웹호스팅 MariaDB 전환

- 개발 환경에서 MariaDB 컨테이너(docker-compose)로 테스트한다
  (0502).
- 마이그레이션은 DB별 차이를 명시한다 (0448, 0461-0468).
- 설정 변경은 DSN만 바꾸면 된다 (adapter 계약이 통일되어 있으므로).

## 관련 문서

- [DB Adapter Contract](db-adapter-contract.md) — 계약 정의.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — 금지 SQL
  기능.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — DB 기능
  차이.
- [PHP DB Configuration](php-db-config.md) — PHP 설정 상세.
- [DB Phase Risk Register](db-phase-risk-register.md) — 이식 위험 요소.
- [Portable Query Builder Policy](portable-query-builder-policy.md) (0451) —
  쿼리 작성 규칙.
- [DB Driver Capability Model](php-db-ui-micro-job-prompts-0351-0670.md) (0472)
  — 드라이버별 기능 차이.
- [Portable Duplicate Key Handling](portable-duplicate-key-handling.md) (0474)
  — 제약 위반 처리.
- [Web Hosting DB Constraints](db-web-hosting-constraints.md) (0509) — 웹호스팅
  제약 상세.
