# PHP DB Configuration

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
PHP 애플리케이션에서 데이터베이스 연결을 설정하고 사용하는 방법을 정의한다.
[db-adapter-contract.md](db-adapter-contract.md)(§1 연결/세션 소유권)가 정한
"애플리케이션 조립 계층에서만 연결을 만든다"는 원칙에 따라, 환경 설정에서
데이터베이스 연결 정보를 읽어 `PDO` 인스턴스를 생성하는 방식을 정리한다.
일반적인 환경(개발, 테스트, 자체 서버 배포)에서는 환경 변수(`WIKI_DATABASE_URL`,
`WIKI_MARIADB_DSN` 등)로 설정하고, 웹호스팅 환경에서는 환경 변수 대신
설정 파일을 사용하는 대안을 제시한다.

## 목적과 범위

- 대상: PHP 애플리케이션의 bootstrap 계층에서 데이터베이스 연결을 생성하는
  부분.
- 다루는 것:
  - `MintWiki\Persistence\ConnectionConfig` 불변 value object의 역할과 사용.
  - `MintWiki\Persistence\PdoConnectionFactory`로 `PDO` 인스턴스 생성하기.
  - 환경 변수로 설정하는 표준 방식(환경 기반 배포).
  - 환경 변수가 없을 때 설정 파일로 대체하는 방식(웹호스팅).
  - PostgreSQL(`pgsql`)과 MariaDB(`mysql`) 두 가지 드라이버 지원.

- 다루지 않는 것:
  - Repository 계층에서의 연결 사용(그건 [db-adapter-contract.md](db-adapter-contract.md)
    에서 다룬다).
  - 연결 풀링(connection pooling)과 재사용 정책.
  - SSL/TLS 같은 고급 연결 옵션(필요한 경우는 `PdoConnectionFactory::dsn()`
    에서 쿼리 파라미터로 추가할 수 있다).

## 1. 핵심 클래스와 역할

### ConnectionConfig (불변 value object)

```php
$config = new ConnectionConfig(
    driver: 'mysql',                // 'mysql' 또는 'pgsql'
    host: 'localhost',
    port: 3306,
    database: 'wiki_engine',
    username: 'wiki',
    password: 'wiki'
);
```

`ConnectionConfig`는 **데이터베이스 연결에 필요한 모든 설정을 담는 불변 value
object**이다(0484). 다섯 가지 필드(host, port, database, username, password)
와 두 가지 지원 드라이버(mysql, pgsql)만 다룬다.

- **불변성**: 생성 후 필드를 변경할 수 없다. 이는 의도하지 않은 설정 변경을
  방지한다.
- **도메인 무지성**: SQL 방언이나 DSN 조립 방식을 알지 않는다 — 순수하게
  설정 데이터만 담는다.

### PdoConnectionFactory (DSN 조립과 연결 생성)

```php
$pdo = PdoConnectionFactory::connect($config);
```

`PdoConnectionFactory`는 정적 메서드 두 개를 제공한다(0484):

- **`dsn(ConnectionConfig $config): string`** — 설정으로부터 PDO DSN 문자열을
  조립한다. `mysql`이면 utf8mb4를 문자셋으로 추가한다
  ([mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md)
  참고).

  ```
  # PostgreSQL의 경우
  pgsql:host=localhost;port=5432;dbname=wiki_engine

  # MariaDB의 경우 (문자셋 포함)
  mysql:host=localhost;port=3306;dbname=wiki_engine;charset=utf8mb4
  ```

- **`connect(ConnectionConfig $config): PDO`** — 조립한 DSN으로 실제 `PDO`
  연결을 연다. `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION`을 강제해
  ([db-adapter-contract.md](db-adapter-contract.md) §3 참고) 제약 위반이
  항상 예외로 신호된다.

### SqlDialect (타입 안전한 드라이버 표현)

```php
$dialect = SqlDialect::fromDriver($config->driver());
// 또는 시도만 하고 null 반환:
$dialect = SqlDialect::tryFromDriver('invalid');
```

`SqlDialect`는 열거형으로, 드라이버 문자열을 타입 안전하게 다루는 도구다
(0486). Repository나 query builder 계층에서 드라이버별 SQL 분기가 필요할 때
사용한다.

```php
match ($dialect) {
    SqlDialect::PostgreSQL => '드라이버별 PostgreSQL SQL',
    SqlDialect::MySQL => '드라이버별 MariaDB SQL',
    SqlDialect::SQLite => '...',
}
```

### PdoTransaction (트랜잭션 래퍼)

```php
$tx = new PdoTransaction($pdo);
$tx->begin();
// ... Repository 작업 ...
$tx->commit();  // 또는 $tx->rollback()
```

`PdoTransaction`은 [db-adapter-contract.md](db-adapter-contract.md) §2가
정한 최소 동작 집합(begin/commit/rollback)을 노출한다(0485). 연결을 스스로
만들거나 닫지 않으며, 주입받은 `PDO` 인스턴스를 감싼다.

## 2. 환경 변수를 사용한 설정 (표준 방식)

개발/테스트/서버 환경에서는 환경 변수로 데이터베이스 설정을 받는다.

### 환경 변수 형식

| 변수명 | 형식 | 설명 |
|---|---|---|
| `WIKI_DATABASE_URL` | `postgresql://user:pass@host:port/dbname` | PostgreSQL DSN (선택사항, 기본값 있음) |
| `WIKI_MARIADB_DSN` | `mysql+pymysql://user:pass@host:port/dbname` | MariaDB DSN (선택사항, 아직 미사용) |

현재 PHP 단계에서는 `WIKI_DATABASE_URL`이 주이지만, 향후 MariaDB 드라이버
전환 시 `WIKI_MARIADB_DSN`을 읽도록 전환된다.

**.env 파일 예제**:

```bash
# PostgreSQL (개발 환경, 기본값)
WIKI_DATABASE_URL=postgresql://wiki:wiki@localhost:5432/wiki_engine

# MariaDB (테스트 환경용, 아직 사용 중 아님)
# WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine
```

### PHP에서 읽기

환경 변수는 일반적으로 PHP application bootstrap에서 읽는다(0415 PHP config
loader skeleton):

```php
<?php
// bootstrap/config.php

$databaseUrl = getenv('WIKI_DATABASE_URL')
    ?? throw new RuntimeException('WIKI_DATABASE_URL 환경 변수가 설정되지 않았습니다.');

// DSN에서 ConnectionConfig 파싱하기 (이하 예제)
$config = parsePostgresqlDsn($databaseUrl);
// 또는 MariaDB로 전환된 후:
// $config = parseMariadbDsn(getenv('WIKI_MARIADB_DSN'));

$pdo = PdoConnectionFactory::connect($config);
```

### DSN 파싱 헬퍼 (예제)

실제 구현에서는 DSN 문자열을 `ConnectionConfig`로 변환하는 헬퍼 함수를 만든다.
이 문서에서 제시하는 것은 개념이며, 구체 구현은 0415(PHP config loader
skeleton)와 후속 bootstrap 태스크에서 확정한다.

```php
function parsePostgresqlDsn(string $dsn): ConnectionConfig {
    // postgresql://wiki:wiki@localhost:5432/wiki_engine 형태를 파싱
    $parts = parse_url($dsn);
    
    return new ConnectionConfig(
        driver: 'pgsql',
        host: $parts['host'] ?? 'localhost',
        port: $parts['port'] ?? 5432,
        database: ltrim($parts['path'] ?? '/wiki_engine', '/'),
        username: $parts['user'] ?? 'postgres',
        password: $parts['pass'] ?? '',
    );
}

function parseMariadbDsn(string $dsn): ConnectionConfig {
    // mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine 형태를 파싱
    // (스킴의 +pymysql 부분은 무시하고 host:port:database를 추출)
    $parts = parse_url($dsn);
    
    return new ConnectionConfig(
        driver: 'mysql',
        host: $parts['host'] ?? 'localhost',
        port: $parts['port'] ?? 3306,
        database: ltrim($parts['path'] ?? '/wiki_engine', '/'),
        username: $parts['user'] ?? 'root',
        password: $parts['pass'] ?? '',
    );
}
```

[postgresql-dsn-compatibility.md](postgresql-dsn-compatibility.md)에서
필드 단위 형식을 다루므로, 실제 파싱 구현은 그 문서의 필드 정의와 일치해야
한다.

## 3. 웹호스팅 환경: 설정 파일 대안

웹호스팅 환경(shared hosting)에서는 환경 변수를 설정할 수 없는 경우가 많다.
그 대신 **설정 파일**에서 읽는 방식을 지원한다.

### 설정 파일 구조

웹호스팅 환경에서는 application root 외부의 안전한 경로에 PHP 설정 파일을
둔다(0617 config file permission docs). 예:

```
/home/username/
├── public_html/              # 웹루트 (공개)
│   └── index.php
└── config/
    └── database.php           # 설정 파일 (공개되지 않음, .gitignore)
```

**`../config/database.php` 예제** (절대 경로):

```php
<?php
// 이 파일은 repository에 커밋되지 않음 (.gitignore 대상)
// 배포 시 수동으로 생성하거나, 설치 스크립트가 만든다.

return [
    'driver' => 'mysql',           // 또는 'pgsql'
    'host' => 'db.example.com',
    'port' => 3306,
    'database' => 'mysite_db',
    'username' => 'mysite_user',
    'password' => 'secure_password_here',
];
```

**설정 파일 로드 및 사용** (bootstrap):

```php
<?php
// bootstrap/config.php

// 1. 환경 변수 시도 (있으면 사용)
$databaseUrl = getenv('WIKI_DATABASE_URL');

// 2. 없으면 설정 파일에서 읽기
if (!$databaseUrl) {
    $configPath = dirname(__DIR__, 2) . '/config/database.php';
    
    if (!is_file($configPath)) {
        throw new RuntimeException(
            sprintf('설정 파일을 찾을 수 없습니다: %s', $configPath)
        );
    }
    
    $configData = require $configPath;
    
    $config = new ConnectionConfig(
        driver: $configData['driver'],
        host: $configData['host'],
        port: $configData['port'],
        database: $configData['database'],
        username: $configData['username'],
        password: $configData['password'],
    );
} else {
    // 환경 변수가 있으면 파싱
    $config = parsePostgresqlDsn($databaseUrl);
}

$pdo = PdoConnectionFactory::connect($config);
```

### 웹호스팅 설정 파일 권한

설정 파일은 웹에서 직접 접근되지 않도록 보호해야 한다
(0617 config file permission docs):

```bash
# 소유자만 읽기 가능
chmod 600 /home/username/config/database.php

# 또는 웹서버 프로세스만 읽기
chmod 640 /home/username/config/database.php
# chown user:www-data /home/username/config/database.php
```

웹루트(`public_html/`)에는 **절대로 두지 않는다**. 설정 파일이 공개되면
데이터베이스 인증정보가 노출된다.

## 4. 기본값과 폴백 정책

애플리케이션 bootstrap은 다음 우선순위로 설정을 결정한다:

1. **환경 변수** (가장 높은 우선순위)
   - `WIKI_DATABASE_URL` (PostgreSQL) 또는 `WIKI_MARIADB_DSN` (MariaDB)

2. **설정 파일** (환경 변수 없을 때)
   - `../config/database.php` (웹호스팅 대안)

3. **기본값** (선택사항, 개발 환경용)
   - 개발 환경에서만 하드코딩된 기본값을 제공할 수 있다.
   - 프로덕션에서는 명시적 설정이 필수다.

```php
<?php
function loadDatabaseConfig(): ConnectionConfig {
    // 1. 환경 변수 확인
    if ($url = getenv('WIKI_DATABASE_URL')) {
        return parsePostgresqlDsn($url);
    }
    
    if ($dsn = getenv('WIKI_MARIADB_DSN')) {
        return parseMariadbDsn($dsn);
    }
    
    // 2. 설정 파일 확인
    $configPath = dirname(__DIR__, 2) . '/config/database.php';
    if (is_file($configPath)) {
        $configData = require $configPath;
        return new ConnectionConfig(
            driver: $configData['driver'],
            host: $configData['host'],
            port: $configData['port'],
            database: $configData['database'],
            username: $configData['username'],
            password: $configData['password'],
        );
    }
    
    // 3. 개발 환경 기본값 (선택사항)
    if (getenv('APP_ENV') === 'development') {
        return new ConnectionConfig(
            driver: 'pgsql',
            host: 'localhost',
            port: 5432,
            database: 'wiki_engine',
            username: 'wiki',
            password: 'wiki',
        );
    }
    
    throw new RuntimeException(
        '데이터베이스 설정을 찾을 수 없습니다. ' .
        'WIKI_DATABASE_URL 환경 변수를 설정하거나 ' .
        '../config/database.php 파일을 생성하세요.'
    );
}
```

## 5. PostgreSQL과 MariaDB 설정 비교

[postgresql-dsn-compatibility.md](postgresql-dsn-compatibility.md)가 DSN
형식 차이를 다루므로, 여기서는 `ConnectionConfig` 생성 차이만 정리한다.

### PostgreSQL 설정 예

```php
$config = new ConnectionConfig(
    driver: 'pgsql',           // 반드시 'pgsql'
    host: 'db.example.com',
    port: 5432,                // PostgreSQL 기본 포트
    database: 'wiki_engine',
    username: 'wiki_user',
    password: 'postgres_password',
);

$pdo = PdoConnectionFactory::connect($config);
// DSN: pgsql:host=db.example.com;port=5432;dbname=wiki_engine
```

### MariaDB 설정 예

```php
$config = new ConnectionConfig(
    driver: 'mysql',           // 반드시 'mysql' (MariaDB도 mysql 드라이버 사용)
    host: 'db.example.com',
    port: 3306,                // MariaDB 기본 포트
    database: 'wiki_engine',
    username: 'wiki_user',
    password: 'mysql_password',
);

$pdo = PdoConnectionFactory::connect($config);
// DSN: mysql:host=db.example.com;port=3306;dbname=wiki_engine;charset=utf8mb4
// (MariaDB는 자동으로 utf8mb4 문자셋 추가)
```

## 6. 테스트와 개발 환경 설정

개발 환경에서 PostgreSQL과 MariaDB 양쪽을 테스트할 때:

```php
<?php
// tests/bootstrap.php 또는 테스트 setup

// PostgreSQL 테스트
$pgConfig = new ConnectionConfig(
    driver: 'pgsql',
    host: 'localhost',
    port: 5432,
    database: 'wiki_engine_test',
    username: 'wiki',
    password: 'wiki',
);

$pgPdo = PdoConnectionFactory::connect($pgConfig);

// MariaDB 테스트
$mysqlConfig = new ConnectionConfig(
    driver: 'mysql',
    host: 'localhost',
    port: 3306,
    database: 'wiki_engine_test',
    username: 'wiki',
    password: 'wiki',
);

$mysqlPdo = PdoConnectionFactory::connect($mysqlConfig);
```

각 Repository 테스트는 두 `PDO` 인스턴스 모두에 대해 동일한 SQL을 실행해
[db-portability-qa-paths.md](db-portability-qa-paths.md)의 parity 검증을
수행한다(0452, 0453 portability test 태스크).

## 7. 웹호스팅 배포 체크리스트

PHP 애플리케이션을 웹호스팅으로 배포할 때:

- [ ] 설정 파일(`../config/database.php`)을 웹루트 외부에 배치
- [ ] 파일 권한 설정 (`chmod 600` 또는 `chmod 640`)
- [ ] `.gitignore`에 설정 파일을 추가 (민감한 데이터 보호)
- [ ] application bootstrap에서 환경 변수와 파일 폴백을 모두 지원 확인
- [ ] 테스트: 환경 변수 없이 설정 파일만으로 연결 가능 확인
- [ ] 호스팅사의 데이터베이스 자격증명(host, port, database 이름 등) 확인
- [ ] [mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md)의
  웹호스팅 버전 요구사항 확인 (최소 MariaDB 10.6 LTS)

## 관련 문서

- [db-adapter-contract.md](db-adapter-contract.md) — 연결/세션 소유권 원칙
  (§1)과 통합 제약 위반 신호(§3).
- [postgresql-dsn-compatibility.md](postgresql-dsn-compatibility.md) — DSN
  형식 필드 비교.
- [mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md) —
  지원 버전과 타입/트랜잭션 차이.
- [portable-id-column-policy.md](portable-id-column-policy.md) — ID 생성 정책
  (database.php bootstrap에서 영향 없지만, Repository 계층 설계에 영향).

## 이 문서 이후 단계

- **0415** [PHP config loader skeleton](php-db-ui-micro-job-prompts-0351-0670.md) — 실제 환경
  변수/파일 로드 로직을 구현한다.
- **0509** [DB web hosting constraints docs](php-db-ui-micro-job-prompts-0351-0670.md) —
  웹호스팅에서의 권한 제한, charset, migration 권한 등 추가 제약을 다룬다.
- **0617** [config file permission docs](php-db-ui-micro-job-prompts-0351-0670.md) — 설정
  파일 권한 관리를 전담 문서로 확대한다.
