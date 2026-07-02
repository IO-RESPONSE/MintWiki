# Web Hosting DB Constraints

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Adapter Selection Guide](db-adapter-selection.md)의 "공용 웹호스팅" 섹션이
지적한 제약 기반 선택과 트레이드오프를 구체화한다. 공용 웹호스팅(shared hosting,
cPanel/Plesk/DirectAdmin 등)에서는 중앙 관리자가 데이터베이스 사용자와 권한을
사전 구성해 주므로, 애플리케이션이 받는 DB 계정의 권한이 제한적이다. 이 문서는
**권한 제한**, **문자셋 제약**, **마이그레이션 권한 제약**을 다루고, 각 제약
아래에서 애플리케이션이 어떻게 동작해야 하는지를 정리한다.

## 목적과 범위

- **대상**: 공용 웹호스팅에서 PHP 애플리케이션을 배포/운영할 때 DB
  연결 설정과 스키마 관리를 담당하는 사람.
- **다루는 것**:
  - 웹호스팅 호스팅사가 일반적으로 부여하는 DB 사용자 권한 수준.
  - DDL(테이블 생성/삭제) 권한 제약 아래에서 마이그레이션 전략.
  - 문자셋 기본값 차이와 통일 방법.
  - 스키마 버전 관리와 초기화 절차.
  - 개발 환경과 호스팅 환경의 차이 대응.

- **다루지 않는 것**:
  - 호스팅사별 구체적 설정 GUI (cPanel vs Plesk 등). 각 호스팅사 매뉴얼 참고.
  - 연결 풀링, SSL 튜닝 등 고급 성능 옵션.
  - 데이터베이스 백업/복구 운영 절차(별도 문서).

## 1. 권한 제한 (Permission Constraints)

### 1.1 기본 사용자 권한 모델

공용 웹호스팅의 DB 사용자는 **단일 데이터베이스 내에서만 작업할 수 있고**,
**DDL 권한이 제한**되는 경우가 많다. 중앙 관리자(호스팅사)가 미리 테이블을
생성해 두면, 애플리케이션 계정은 **DML만**(SELECT, INSERT, UPDATE, DELETE)
수행 가능한 경우가 일반적이다.

| 권한 | 기본 사용자 | 관리 사용자 |
|---|---|---|
| SELECT / INSERT / UPDATE / DELETE | ✓ | ✓ |
| CREATE TABLE / ALTER TABLE | ✗ (제약 기본) | ✓ |
| CREATE INDEX / DROP INDEX | ✗ (제약 기본) | ✓ |
| GRANT / REVOKE | ✗ | ✓ |
| CREATE VIEW / DROP VIEW | ✗ (제약 기본) | ✓ |

**현실의 예시**:

- **cPanel**: 호스팅사 관리자가 MySQL 사용자를 만들면, 기본적으로 CREATE/ALTER는
  불가능하다. 고급 권한 설정에서 명시적으로 부여하지 않는 한.
- **Plesk**: 비슷한 정책. 데이터베이스 사용자는 "read/write" 수준만 기본 부여.
- **DirectAdmin**: 도메인 소유자 또는 리셀러 계정은 자신의 데이터베이스에 한정된
  권한만 가진다.

### 1.2 단일 데이터베이스 제약

웹호스팅 계정 하나에 보통 **하나의 데이터베이스만** 할당된다. 예:

- 계정명: `example_user`
- 데이터베이스: `example_user_wiki` (계정명 접두어 + 앱명)
- 데이터베이스 사용자: `example_user_wiki`
- 권한: `example_user_wiki` 데이터베이스에만 접근 가능

이는 [db-adapter-contract.md](db-adapter-contract.md)의 "단일 데이터베이스 가정"과
일치한다. 데이터베이스 명시 없이 스키마 간 교차 참조가 필요하면 호스팅사에 추가
데이터베이스 신청(유료)을 해야 한다.

### 1.3 애플리케이션 대응 전략

**아래 세 단계로 권한 제약에 대응한다**:

1. **초기 스키마 생성**:
   - 호스팅사 관리 도구(cPanel의 "MySQL 데이터베이스" 탭 등)에서 관리자 권한으로
     테이블을 생성한다.
   - 또는 호스팅사가 제공하는 "초기 SQL 실행" 기능을 이용한다.
   - Alembic 마이그레이션을 "오프라인(offline) 모드"로 미리 생성하고,
     설치 단계에서 SQL을 호스팅사에 제출해 수행하게 할 수 있다.

2. **런타임 DML 작업**:
   - 애플리케이션 계정은 SELECT, INSERT, UPDATE, DELETE만 수행한다.
   - [db-adapter-contract.md](db-adapter-contract.md)의 계약 구현은 DML만 가정한다.

3. **스키마 변경**:
   - 스키마 버전을 관리하는 전용 테이블(`schema_version`, read-only 필드 권장)을
     두고, 애플리케이션은 이 테이블을 읽어 필요한 마이그레이션 여부를 판단한다.
   - DDL이 필요하면 (0518) 호스팅사 지원팀에 요청하거나, cPanel 등에서
     수동으로 실행한다.

## 2. 문자셋 제약 (Charset Constraints)

### 2.1 MariaDB 기본값 문제

MariaDB 호스팅 환경에서 **데이터베이스의 기본 문자셋이 `utf8`(3바이트)로
설정**되어 있을 수 있다. 이는
[mariadb-compatibility-matrix.md](mariadb-compatibility-matrix.md)에서 명시한
`utf8mb4` 요구사항과 충돌한다.

- **3바이트 `utf8`의 문제**: 이모지, 일부 한자, 특수 유니코드 문자를 저장할
  수 없다. 한글은 저장 가능하지만, 애플리케이션이 이모지를 지원하려면
  `utf8mb4`가 필수다.
- **호스팅사 기본값**: 오래된 서버는 여전히 `utf8` 기본값을 쓴다.

**현실의 예**:

```sql
-- 호스팅사 관리 도구에서 생성한 데이터베이스
CREATE DATABASE example_user_wiki DEFAULT CHARSET=utf8;
-- ↑ 이렇게 utf8이 기본값으로 설정되어 있을 수 있다.

-- 내부 테이블도 같은 charset 상속
CREATE TABLE document (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255),
    -- ↑ 테이블도 charset=utf8 상속 → 이모지 저장 불가
) CHARSET=utf8;
```

### 2.2 charset 통일 전략

**정책: 호스팅 환경에서도 모든 데이터베이스/테이블/컬럼의 문자셋을
`utf8mb4`로 명시적으로 설정한다.**

#### 2.2.1 호스팅사 관리 도구에서

호스팅 제공자 관리 도구(cPanel, Plesk 등)에서 데이터베이스를 생성할 때:

1. "고급 옵션" 또는 "Charset" 선택지가 있는지 확인한다.
2. 있으면 `utf8mb4`를 명시적으로 선택한다.
3. 없으면 호스팅사 지원팀에 문의하거나, 초기 SQL 스크립트로 아래 명령을 실행한다:

```sql
-- 데이터베이스 charset 변경 (생성 후)
ALTER DATABASE example_user_wiki CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

-- 기존 테이블 변경
ALTER TABLE document CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE revision CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
-- ... 모든 테이블
```

#### 2.2.2 애플리케이션 생성 쿼리에서

Alembic 마이그레이션이나 초기 스키마 생성 시, `CREATE TABLE`에 명시한다:

```python
# alembic 마이그레이션 예
def upgrade():
    op.create_table(
        'document',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(255)),
        # ... 다른 컬럼
        sa.UniqueConstraint('normalized_title', name='uq_document_normalized_title'),
        mysql_charset='utf8mb4',  # ← MariaDB용 명시적 지정
        mysql_collate='utf8mb4_bin',
    )
```

#### 2.2.3 PDO 연결 레벨에서

PHP PDO 연결 시, DSN에 charset을 명시한다:

```php
// php/src/Persistence/PdoConnectionFactory.php
public static function dsn(ConnectionConfig $config): string {
    if ($config->driver() === 'mysql') {
        return sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
            $config->host(),
            $config->port(),
            $config->database(),
        );
    }
    // PostgreSQL은 원래 UTF8 기본
    return sprintf(
        'pgsql:host=%s;port=%d;dbname=%s',
        $config->host(),
        $config->port(),
        $config->database(),
    );
}
```

이 방법은 한 번의 연결 설정만으로 모든 쿼리가 `utf8mb4` 콘텐츠를 올바르게
처리하도록 보장한다.

### 2.3 검증 및 모니터링

배포 후 실제 문자셋이 정확한지 확인:

```sql
-- 데이터베이스 charset 확인
SHOW CREATE DATABASE example_user_wiki\G
-- Character Set: utf8mb4 여야 함

-- 테이블 charset 확인
SHOW CREATE TABLE document\G
-- CHARACTER SET utf8mb4 여야 함

-- 컬럼별 collation 확인 (portable-text-collation-policy.md 참고)
SHOW FULL COLUMNS FROM document\G
```

## 3. 마이그레이션 권한 제약 (Migration Permission Constraints)

### 3.1 DDL 불가 상황과 대응

웹호스팅 계정에 DDL 권한이 없으면, 애플리케이션이 `ALTER TABLE`,
`CREATE INDEX` 등을 실행할 수 없다. 이는 Alembic 같은 자동화 마이그레이션
도구를 통상적인 방식(런타임 자동 적용)으로 사용할 수 없다는 뜻이다.

**대응 전략은 아래 세 가지**:

#### 3.1.1 방법 A: 호스팅사 사전 스키마 구성 (권장)

초기 배포 시, 필요한 모든 스키마를 **호스팅사 관리자에게 요청해 미리 생성**해 둔다.

**절차**:

1. Alembic을 로컬 환경에서 "오프라인(offline)" 모드로 실행하거나,
   마이그레이션 파일의 SQL을 추출한다.
2. 추출한 SQL을 호스팅사에 제출한다 (지원팀 티켓 또는 cPanel의 "phpMyAdmin"
   SQL 실행 탭).
3. 호스팅사 관리자가 SQL을 실행한다.
4. 애플리케이션은 스키마 버전 테이블로 버전 상태를 읽기만 한다(아래 참고).

**장점**: 안전성 우수, 버전 관리 명확.
**단점**: 매 배포마다 호스팅사 개입 필요, 배포 속도 느림.

#### 3.1.2 방법 B: 스키마 버전 테이블 (Self-Managed Schema)

DDL 권한이 없으므로, 애플리케이션은 DML만 사용해 **스키마 상태를 추적**한다.

**구현**:

```sql
-- 호스팅사 관리자가 미리 생성 (DDL 필요)
CREATE TABLE schema_version (
    version_id INT PRIMARY KEY,
    description VARCHAR(255),
    installed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time INT,  -- ms, 정보용
    is_applied BOOLEAN DEFAULT TRUE,
    -- charset 명시
) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
```

**애플리케이션 로직 (PHP 또는 Python)**:

```php
<?php
// PHP 예제: 스키마 버전 확인
function ensureSchemaVersion($pdo, $requiredVersion) {
    // 스키마 버전 조회 (읽기만, DML)
    $stmt = $pdo->prepare('SELECT MAX(version_id) as max_version FROM schema_version');
    $stmt->execute();
    $row = $stmt->fetch(PDO::FETCH_OBJ);
    
    $currentVersion = $row->max_version ?? 0;
    
    if ($currentVersion < $requiredVersion) {
        // 버전 불일치: 관리자에게 알림 또는 읽기 전용 모드 전환
        error_log("Schema version mismatch: current=$currentVersion, required=$requiredVersion");
        // 또는 설정에 따라 읽기 전용 모드 활성화
        // throw new Exception("Schema version outdated; manual migration required.");
    }
}

// 애플리케이션 bootstrap에서
ensureSchemaVersion($pdo, REQUIRED_SCHEMA_VERSION);
```

**버전 기록** (호스팅사 관리자가 스키마 업데이트 후 기록):

```sql
-- 호스팅사가 새 버전을 적용한 후 기록
INSERT INTO schema_version (version_id, description, execution_time, is_applied)
VALUES (1, 'Initial schema', 1234, TRUE);

-- 다음 버전
INSERT INTO schema_version (version_id, description, execution_time, is_applied)
VALUES (2, 'Add index on document.normalized_title', 567, TRUE);
```

**장점**: 순환 배포 시 버전 추적 가능, 읽기만 사용.
**단점**: 버전 기록을 수동으로 관리해야 함.

#### 3.1.3 방법 C: 지연된 마이그레이션 (Deferred Alembic)

로컬에서 Alembic 마이그레이션을 생성한 후, 호스팅 환경에서는 마이그레이션을
실행하지 않고, **버전만 기록**하는 방식.

```php
<?php
// PHP 예제: 마이그레이션 버전만 기록
function recordMigrationVersion($pdo, $migrationId, $description) {
    // 호스팅사가 이미 DDL 적용했다고 가정
    // 애플리케이션은 DML로 버전만 기록
    $stmt = $pdo->prepare(
        'INSERT INTO schema_version (version_id, description, is_applied) VALUES (?, ?, TRUE)'
    );
    $stmt->execute([$migrationId, $description]);
}

// bootstrap에서, 각 배포 시
recordMigrationVersion($pdo, 202607_01_001, 'Create document table');
```

**장점**: Alembic 워크플로우와 호환, 로컬과 호스팅 환경 검증 가능.
**단점**: 여전히 호스팅사 개입 필요.

### 3.2 스키마 버전 테이블 설계

모든 방법에서 공통으로 사용할 스키마 버전 테이블:

```sql
CREATE TABLE schema_version (
    version_id INT NOT NULL PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    installed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time INT,  -- 마이그레이션 소요시간 (ms), 정보용
    is_applied BOOLEAN DEFAULT TRUE,
    
    CHARSET utf8mb4 COLLATE utf8mb4_bin
);
```

**필드 설명**:

- `version_id`: 마이그레이션 버전 번호 (Alembic은 타임스탬프 기반이지만,
  간단히 하려면 증가 정수 사용).
- `description`: 마이그레이션 목적 (예: "Add index on document.id").
- `installed_on`: 자동 타임스탐프, 호스팅사가 마이그레이션을 실행한 시간.
- `execution_time`: 참고용, 필수 아님. 마이그레이션 소요시간을 기록할 수 있음.
- `is_applied`: 논리값, 기본 TRUE. 롤백된 마이그레이션은 FALSE로 표시
  (호스팅 환경에서는 거의 사용 안 함).

### 3.3 초기 스키마 배포 체크리스트

웹호스팅에 애플리케이션을 처음 배포할 때:

1. **호스팅사 구성 확인**:
   - [ ] 데이터베이스 이름, 사용자, 비밀번호 확인
   - [ ] 데이터베이스 charset이 utf8mb4인지 확인 (아니면 위의 2.2.2 절차 따르기)
   - [ ] 마이그레이션을 위한 관리 계정/권한 확인

2. **초기 스키마 준비**:
   - [ ] 로컬 환경에서 Alembic으로 필요한 모든 마이그레이션 생성
   - [ ] `migrations/versions/` 아래 생성된 마이그레이션 파일 확인
   - [ ] 마이그레이션 SQL 추출 (또는 `alembic upgrade` 오프라인 모드)

3. **호스팅사에 제출**:
   - [ ] 초기 스키마 SQL을 텍스트 파일로 준비
   - [ ] 호스팅사 지원팀에 제출하거나 cPanel 등에서 수동 실행
   - [ ] 스키마 생성 완료 확인

4. **애플리케이션 배포**:
   - [ ] PHP 설정 파일(`../config/database.php`) 준비
   - [ ] 스키마 버전 확인 로직이 정상 작동하는지 테스트
   - [ ] 애플리케이션 첫 실행 후 로그에서 오류 없음 확인

### 3.4 스키마 업그레이드 절차

이후 기능 추가로 스키마를 변경해야 할 때:

1. **로컬에서 개발/테스트**:
   - [ ] PostgreSQL 로컬 환경에서 마이그레이션 작성 및 테스트
   - [ ] Alembic `upgrade/downgrade` 검증

2. **마이그레이션 SQL 추출**:
   - [ ] Alembic 오프라인 모드로 SQL 생성, 또는
   - [ ] 마이그레이션 파일의 `upgrade()` 함수 코드 읽어 SQL로 변환

3. **호스팅사에 요청**:
   - [ ] 변경 SQL을 지원팀에 제출
   - [ ] 변경사항과 롤백 방법 함께 제시
   - [ ] 변경 완료 확인

4. **애플리케이션 배포**:
   - [ ] 로컬 MariaDB에서 같은 SQL 실행해 호환성 재확인
   - [ ] 애플리케이션 코드 변경사항 배포
   - [ ] 스키마 버전 테이블 업데이트 (또는 자동 기록)

## 4. 개발 환경과 호스팅 환경의 차이 대응

### 4.1 로컬 개발 (PostgreSQL/MariaDB 자유)

로컬에서는 DDL, 권한 제약이 거의 없다. 표준 Alembic 워크플로우:

```bash
# 로컬 개발
python -m alembic revision -m "Add new table"
python -m alembic upgrade head
```

### 4.2 호스팅 환경 (MariaDB, DDL 제약)

호스팅에서는 DDL이 제한되므로, 개발 환경에서:

1. 로컬에서 표준 Alembic 워크플로우로 마이그레이션 작성
2. 생성된 마이그레이션 파일을 **읽기만 하고 실행하지 않기** (또는 오프라인 모드)
3. 호스팅사에 SQL 추출해 제출
4. 호스팅사가 적용 후, 로컬 MariaDB 테스트 환경에서 검증

**예제: 로컬 MariaDB 테스트 환경**:

```bash
# MariaDB 테스트용 docker-compose 실행 (0502 task)
docker-compose -f docker-compose.yml up -d mariadb

# MariaDB에 대해 Alembic 실행 (검증용)
WIKI_DATABASE_URL=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine \
python -m alembic upgrade head

# 호스팅과 동일한 환경에서 동작 확인
```

### 4.3 교차 환경 테스트

PHP 애플리케이션이 두 DB(PostgreSQL + MariaDB) 모두 지원해야 하므로:

- 로컬 개발: PostgreSQL (빠름, 고급 기능)
- MariaDB 호스팅 검증: docker-compose 또는 외부 테스트 인스턴스
- CI 테스트: 두 DB 모두 실행 (0452, 0453)

[db-portability-qa-paths.md](db-portability-qa-paths.md)와
[db-adapter-selection.md](db-adapter-selection.md)의 드라이버 선택 부분을
참고한다.

## 5. 트러블슈팅

### 문제: 이모지 저장 시 "Illegal mix of collations" 또는 데이터 손실

**원인**: 데이터베이스 또는 테이블 charset이 `utf8`(3바이트)로 설정되어 있음.

**해결**:

```sql
-- 데이터베이스 charset 변경
ALTER DATABASE example_user_wiki CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

-- 모든 테이블 변경
ALTER TABLE document CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
ALTER TABLE revision CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

-- PDO 연결도 명시적으로 utf8mb4 지정 (위의 2.2.3 절)
```

### 문제: "Access denied for user 'app_user'@'%' to database" 또는 DDL 오류

**원인**: 애플리케이션 계정에 권한이 없음.

**해결**:

- DDL 작업(테이블 생성 등)은 호스팅사 관리자 계정으로 수행해야 함.
- 호스팅사 지원팀에 연락하거나, cPanel 등에서 관리자 도구 사용.

### 문제: "Table 'schema_version' doesn't exist" on startup

**원인**: 스키마 버전 테이블을 미리 호스팅사가 생성하지 않음.

**해결**:

- 호스팅사에 `schema_version` 테이블 생성 요청 (위의 3.2 절 SQL 제공)
- 또는 애플리케이션 코드에서, 테이블 없음 예외를 잡아 무시하거나 경고 로깅

## 6. 체크리스트: 웹호스팅 배포 준비

### 전제 조건 확인

- [ ] 호스팅사 DB 계정(사용자명, 비밀번호, host) 확인
- [ ] 할당된 데이터베이스명 확인
- [ ] 데이터베이스 charset 현재값 확인 (`utf8` or `utf8mb4`?)

### 권한 확인

- [ ] 애플리케이션 계정으로 SELECT 가능 확인
- [ ] 애플리케이션 계정으로 INSERT/UPDATE/DELETE 가능 확인
- [ ] 애플리케이션 계정으로 CREATE/ALTER **불가** 확인 (예상대로라면 정상)
- [ ] 호스팅사 관리 도구 또는 관리자 계정 접근 확인

### 스키마 준비

- [ ] 로컬 환경에서 모든 Alembic 마이그레이션 생성 완료
- [ ] 마이그레이션 SQL 추출 또는 오프라인 모드 테스트 완료
- [ ] `schema_version` 테이블 생성 SQL 준비

### charset 설정

- [ ] 호스팅사에 데이터베이스 charset을 `utf8mb4`로 설정 요청
- [ ] PHP 연결 문자열에 `charset=utf8mb4` 포함 확인

### 마이그레이션 전략 선택

- [ ] 방법 A (호스팅사 사전 구성) / 방법 B (버전 테이블) / 방법 C (Deferred Alembic)
  중 하나 선택 및 문서화

### 배포

- [ ] 설정 파일(`../config/database.php`) 작성 및 권한 설정 (0617)
- [ ] PHP 애플리케이션 업로드
- [ ] 초기 접속 후 로그 확인 (오류 없음)

## 관련 문서

- [DB Adapter Selection Guide](db-adapter-selection.md) — 웹호스팅 adapter 선택과
  제약 개요.
- [PHP DB Configuration](php-db-config.md) — 환경 변수와 설정 파일을 통한
  DB 연결 설정.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) —
  MariaDB 지원 버전과 charset 관련 기술 상세.
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  charset과 collation 설정 규칙 (utf8mb4_bin).
- [Migration Portability Checklist](migration-portability-checklist.md) —
  Alembic 마이그레이션 작성 규칙.
- [DB Phase QA Checklist](db-phase-qa-checklist.md) — 웹호스팅 배포 전
  테스트 항목.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md)
  — Phase C 잡 목록 전체.

## 이 문서 이후 단계

- **0518**: [Schema Installer](php-db-ui-micro-job-prompts-0351-0670.md) — 호스팅
  환경에서 스키마 버전 테이블만 확인하는 읽기 전용 installer 구현.
- **0617**: [Config File Permission Docs](php-db-ui-micro-job-prompts-0351-0670.md) —
  웹호스팅에서 설정 파일 보안 관리 전담 문서.
- **0620-0630** (이후 단계): PHP 배포 매뉴얼 및 호스팅사별 구체 설정 가이드.
