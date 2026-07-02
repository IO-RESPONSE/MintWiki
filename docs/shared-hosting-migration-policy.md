# Shared Hosting Migration Policy

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[DB Web Hosting Constraints](db-web-hosting-constraints.md)가 공용 웹호스팅의
권한 제약과 문자셋 제약을 다루었다면, 이 문서는 **그 제약 아래에서 스키마 변경을
단계적으로 수행하는 프로세스**를 정의한다. 특히 공용 웹호스팅에서는 DDL 권한이
없거나 제한적이므로, 애플리케이션이 **웹 인터페이스에서 마이그레이션 진행 상태를
확인하고 필요한 조작을 수행**할 수 있는 방식을 제시한다.

## 목적

공용 웹호스팅에 배포된 애플리케이션이 새 버전으로 업그레이드될 때, 호스팅사
관리자의 개입 없이 또는 최소한의 개입으로 스키마 변경을 적용할 수 있는
**웹 기반 마이그레이션 인터페이스**의 설계 원칙을 정의한다. 이 원칙은:

1. **DDL 권한 제약**: 애플리케이션 계정이 DDL 실행 불가 상황을 기본으로 가정
2. **호스팅사 협력 모델**: 필요한 스키마 변경을 호스팅사에 요청하는 절차
3. **웹 인터페이스 기반**: 운영자가 브라우저에서 마이그레이션 상태를 모니터링하고 제어

를 포괄한다.

## 적용 범위

- 공용 웹호스팅 (cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 애플리케이션
- Alembic 마이그레이션 또는 db/schema 아래 portable SQL 원본으로 정의된 스키마 변경
- 애플리케이션 계정의 DDL 권한이 제한적인 환경

적용되지 않는 것:

- 전용 서버 또는 관리형 호스팅(Managed Hosting)에서 DDL 권한이 충분한 경우
- Docker/Kubernetes 같은 컨테이너 기반 배포 환경
- 로컬 개발 환경 (이는 표준 Alembic 워크플로우 사용)

## 1. 마이그레이션 실행 모델

### 1.1 세 가지 실행 경로

공용 웹호스팅 환경에서 마이그레이션을 실행하는 방식은 호스팅사 정책과 권한에
따라 세 가지로 나뉜다.

#### 경로 A: 호스팅사 사전 적용 (Pre-applied by Hosting Provider)

호스팅사 관리자가 애플리케이션 배포 **이전에** 필요한 스키마 변경을 모두 적용해
둔다.

**절차**:

1. 새 버전 배포 준비 단계에서, `migrations/versions/` 또는 `db/schema` 아래의
   마이그레이션 SQL을 추출한다.
2. 호스팅사 지원팀에 "새 버전 배포 예정, 다음 SQL을 미리 적용해 달라"는 요청을
   제출한다.
3. 호스팅사 관리자가 관리 계정으로 SQL을 실행한다.
4. 애플리케이션 코드는 새 버전으로 배포하면, 이미 스키마가 준비되어 있다.
5. 애플리케이션 bootstrap 단계에서 스키마 버전 테이블을 읽어 상태를 확인한다.

**장점**:
- 안전성 최우선 — 호스팅사 전문가가 적용
- 버전 추적 명확 — 사전에 기록되므로 실수 가능성 낮음
- 애플리케이션 코드 복잡도 낮음 — 마이그레이션 로직 불필요

**단점**:
- 배포 리드타임 증가 — 호스팅사 처리 기간 대기
- 호스팅사 협력 필수 — 외부 의존성 높음
- 응급 패치 어려움 — 긴급 스키마 변경이 필요하면 지체

#### 경로 B: 애플리케이션 웹 인터페이스 기반 (Web-based Installer/Maintenance Page)

애플리케이션이 웹 인터페이스를 제공하여, **운영자가 브라우저에서 마이그레이션
상태를 확인하고 조작**할 수 있게 한다. 실제 DDL 실행은 여전히 호스팅사가
수행하지만, 애플리케이션이 상태 추적과 알림을 담당한다.

**절차**:

1. 새 버전 배포 후, 애플리케이션의 `/installer` 또는 `/maintenance` 페이지에
   접속한다.
2. 페이지는 현재 스키마 버전과 필요한 마이그레이션을 비교해 표시한다:
   ```
   현재 스키마 버전: 3
   필요한 스키마 버전: 5
   
   대기 중인 마이그레이션:
   - [0004] Add index on document.normalized_title
   - [0005] Add audit_events table
   ```

3. 운영자는 호스팅사에 "마이그레이션 [0004]와 [0005]를 적용해 달라"고 요청하며,
   필요한 SQL을 웹 페이지에서 복사해 전달할 수 있다:
   ```sql
   -- [0004] Add index on document.normalized_title
   ALTER TABLE document ADD INDEX ix_document_normalized_title (normalized_title);
   
   -- [0005] Add audit_events table
   CREATE TABLE audit_events (
       id VARCHAR(255) PRIMARY KEY,
       ...
   ) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
   ```

4. 호스팅사 관리자가 SQL을 실행한다.
5. 호스팅사가 완료하면, 운영자가 `/installer` 페이지의 "마이그레이션 확인" 버튼을
   클릭하면, 애플리케이션이 스키마 버전 테이블을 업데이트하고 다음 상태로 진행한다.

**장점**:
- 웹 인터페이스로 상태 투명성 제공
- SQL을 미리 보여주므로 호스팅사와 커뮤니케이션 간편
- 부분 마이그레이션 추적 가능 — 일부만 적용된 상황 감지

**단점**:
- 여전히 호스팅사 개입 필요
- 애플리케이션 코드에 설치/유지보수 페이지 구현 필요
- 스키마 버전 테이블 관리 필요

#### 경로 C: 애플리케이션 자동 마이그레이션 (Full Application Auto-Migration)

애플리케이션 계정이 **최소한의 DDL 권한** (CREATE TABLE, ALTER TABLE)을 가진 경우,
애플리케이션 자체가 마이그레이션을 실행하고 상태를 기록한다.

**절차**:

1. 새 버전 배포 후 애플리케이션 bootstrap 단계에서:
   ```php
   // pseudo-code
   $migrationState = $app['migration.service']->checkState();
   if ($migrationState->hasPending()) {
       $migrationState->applyAll();  // 앱이 직접 실행
   }
   ```

2. 마이그레이션이 자동으로 실행되고, 결과가 스키마 버전 테이블에 기록된다.
3. 실패하면 로그에 기록되고, `/diagnostics` 페이지에서 운영자가 확인 가능하다.

**장점**:
- 배포 직후 즉시 새 스키마 사용 가능
- 호스팅사 개입 0 — 완전 자동화
- 응급 패치에 유리

**단점**:
- 호스팅사 권한 설정 필수 — 초기 구성이 복잡
- DDL 실패 시 수동 개입 필요
- 일부 호스팅사는 이 권한 제공 거부 가능

### 1.2 권장 경로별 호스팅 환경

| 호스팅 유형 | 권장 경로 | 이유 |
|---|---|---|
| cPanel (표준 공용호스팅) | 경로 B | DDL 권한 제공 안 함, 웹 인터페이스로 상태 투명화 권장 |
| Plesk | 경로 A 또는 B | 관리 도구 UI 제공, 경로 A 선호 가능 |
| DirectAdmin | 경로 A 또는 B | 관리자 권한 옵션 확인 후 경로 결정 |
| VPS / 관리형 호스팅 | 경로 C | 충분한 권한 가능성 높음 |
| 전용 서버 | 경로 C | 완전 권한, 표준 Alembic 워크플로우 사용 |

## 2. 웹 기반 마이그레이션 인터페이스 설계

### 2.1 마이그레이션 상태 조회 엔드포인트

애플리케이션은 다음 정보를 제공하는 엔드포인트를 구현한다. (경로 B, C에 필수)

#### `GET /installer/status` (또는 `/maintenance/status`)

현재 스키마 상태와 필요한 마이그레이션을 조회한다. (인증: 관리자만)

**응답 예시**:

```json
{
  "current_schema_version": 3,
  "required_schema_version": 5,
  "status": "migration_pending",
  "pending_migrations": [
    {
      "version_id": 4,
      "description": "Add index on document.normalized_title",
      "created_at": "2026-07-02T10:30:00Z"
    },
    {
      "version_id": 5,
      "description": "Add audit_events table",
      "created_at": "2026-07-02T11:00:00Z"
    }
  ],
  "database_connection": {
    "host": "localhost",
    "database": "wiki_engine",
    "charset": "utf8mb4"
  }
}
```

**필드 설명**:

- `current_schema_version`: 현재 적용된 스키마 버전
- `required_schema_version`: 현재 코드가 요구하는 스키마 버전
- `status`: 상태 코드 (`ok`, `migration_pending`, `migration_failed`, `permission_denied`)
- `pending_migrations`: 아직 적용되지 않은 마이그레이션 목록
- `database_connection`: 연결 정보 (호스팅사에 전달할 용도)

#### `GET /installer/migration/<version_id>/sql`

특정 마이그레이션의 SQL을 조회한다. (운영자가 호스팅사에 전달할 용도)

**응답 예시**:

```json
{
  "version_id": 4,
  "description": "Add index on document.normalized_title",
  "sql": "ALTER TABLE document ADD INDEX ix_document_normalized_title (normalized_title);",
  "estimated_duration_ms": 1500
}
```

### 2.2 마이그레이션 적용 엔드포인트 (경로 C 및 경로 B의 확인 단계)

#### `POST /installer/migration/<version_id>/apply`

마이그레이션을 적용한다. (경로 C: 애플리케이션이 직접 실행, 경로 B: 호스팅사 적용 후 확인)

**요청**:

```json
{
  "force": false,
  "dry_run": false
}
```

**응답 성공**:

```json
{
  "version_id": 4,
  "applied_at": "2026-07-02T12:00:00Z",
  "execution_time_ms": 1234,
  "status": "applied"
}
```

**응답 실패**:

```json
{
  "version_id": 4,
  "status": "failed",
  "error": "Insufficient permissions: ALTER not allowed on table 'document'",
  "recommended_action": "contact_hosting_provider"
}
```

### 2.3 마이그레이션 이력 조회

#### `GET /installer/history`

지금까지 적용된 모든 마이그레이션 이력을 표시한다.

**응답 예시**:

```json
{
  "applied_migrations": [
    {
      "version_id": 1,
      "description": "Initial schema",
      "applied_at": "2026-06-15T08:00:00Z",
      "execution_time_ms": 5000
    },
    {
      "version_id": 2,
      "description": "Add revision table",
      "applied_at": "2026-06-20T14:30:00Z",
      "execution_time_ms": 2100
    },
    {
      "version_id": 3,
      "description": "Add document.normalized_title column",
      "applied_at": "2026-07-01T10:00:00Z",
      "execution_time_ms": 800
    }
  ],
  "total_count": 3
}
```

## 3. 마이그레이션 단계별 프로세스

### 3.1 개발 단계: 로컬 환경에서 마이그레이션 작성

```bash
# 로컬 PostgreSQL/MariaDB에서 마이그레이션 작성 및 테스트
python -m alembic revision -m "Add document.normalized_title column"
python -m alembic upgrade head

# 마이그레이션이 [migration-portability-checklist.md](migration-portability-checklist.md)를 따르는지 확인
scripts/qa.sh  # includes SQL denylist check (0447)
```

### 3.2 배포 준비 단계: 마이그레이션 SQL 추출

마이그레이션 파일을 읽고, 호스팅 환경에서 실행할 수 있는 SQL을 준비한다.

```bash
# Alembic 마이그레이션을 보기 좋은 SQL로 변환
# Option 1: migrations/versions/*.py 파일을 직접 읽어 upgrade() 함수의 op.* 호출을 SQL로 해석
# Option 2: 오프라인 모드에서 SQL 생성 (0505 portable migration dry-run command에서 구현)

# 현재: 마이그레이션 파일 내용을 보고 수작업으로 SQL 작성
# 미래: scripts/migration_extract.sh 또는 admin page에서 자동 추출
```

**마이그레이션 SQL 작성 규칙**:

- 각 마이그레이션은 **논리적으로 독립된 하나의 변경**을 수행한다.
- 테이블 생성, 인덱스 추가, 컬럼 변경은 별도 마이그레이션으로 분리한다.
- 각 마이그레이션에는 설명과 예상 소요시간을 기록한다.

**마이그레이션 SQL 예시**:

```sql
-- Migration [0004]: Add document.normalized_title column
-- Purpose: Enable case-insensitive document title search
-- Estimated duration: 30 seconds on 50M rows

ALTER TABLE document 
ADD COLUMN normalized_title VARCHAR(255) 
CHARACTER SET utf8mb4 COLLATE utf8mb4_bin 
AFTER title;

-- Backfill existing documents
UPDATE document SET normalized_title = LOWER(title);

-- Add unique index
ALTER TABLE document 
ADD UNIQUE KEY uq_document_normalized_title (normalized_title);
```

### 3.3 배포 단계: 호스팅 환경에 적용

#### 경로 A: 호스팅사 사전 적용

**Step 1**: 호스팅사에 마이그레이션 요청

```
제목: [wiki-engine v1.2.0 배포] DB 마이그레이션 요청

예정 배포일: 2026-07-10
현재 스키마 버전: 3
필요한 스키마 버전: 5

다음 SQL을 미리 적용해 주세요:

-- Migration [0004]: Add document.normalized_title column
ALTER TABLE document ADD COLUMN normalized_title VARCHAR(255) ...

-- Migration [0005]: Add audit_events table
CREATE TABLE audit_events ( ... )
```

**Step 2**: 호스팅사 확인 대기 (보통 1-2 영업일)

**Step 3**: 호스팅사 완료 후 애플리케이션 배포

```bash
# 코드 배포
git checkout v1.2.0
# ... PHP 코드 업로드 ...

# 애플리케이션이 시작되면 자동으로 스키마 버전 확인
# (이미 호스팅사가 적용했으므로 문제 없음)
```

#### 경로 B: 웹 인터페이스 기반

**Step 1**: 새 버전 배포

```bash
git checkout v1.2.0
# ... PHP 코드 업로드 ...
```

**Step 2**: 관리자가 웹 인터페이스 접속

```
http://your-wiki.com/installer
```

**Step 3**: 마이그레이션 상태 확인

```
현재 스키마 버전: 3
필요한 스키마 버전: 5

대기 중인 마이그레이션:
☐ [0004] Add document.normalized_title column
  SQL: ALTER TABLE document ADD COLUMN normalized_title ...
  
☐ [0005] Add audit_events table
  SQL: CREATE TABLE audit_events ( ... )
```

**Step 4**: 호스팅사에 연락

```
호스팅사 지원팀에 다음 정보와 함께 "마이그레이션 요청" 메시지 전송:

데이터베이스: your_db_wiki
대기 중인 마이그레이션 버전: 0004, 0005
필요한 SQL: 웹 페이지의 "SQL 복사" 버튼으로 복사 후 전달
```

**Step 5**: 호스팅사 완료 후 확인

호스팅사가 SQL 실행 완료하면, 웹 인터페이스에서:

```
"마이그레이션 확인" 버튼 클릭
→ 애플리케이션이 스키마 버전 테이블 업데이트
→ 다음 대기 중인 마이그레이션 표시 (또는 "최신 상태")
```

#### 경로 C: 애플리케이션 자동 마이그레이션

**Step 1**: 새 버전 배포

```bash
git checkout v1.2.0
# ... PHP 코드 업로드 ...
```

**Step 2**: 자동 마이그레이션 실행

애플리케이션 부팅 시 자동으로:

```php
$migrations = $app['migration.service']->getPending();
foreach ($migrations as $migration) {
    try {
        $migration->apply();
        // 스키마 버전 테이블 업데이트
    } catch (PDOException $e) {
        // 로그 기록
        $app['logger']->error("Migration {$migration->version} failed", ['error' => $e->getMessage()]);
    }
}
```

**Step 3**: 완료 확인

```
로그 또는 관리 페이지 `/maintenance` 에서 마이그레이션 이력 확인
→ 모두 성공하면 운영 시작
→ 실패하면 호스팅사 또는 운영팀에 연락
```

## 4. 스키마 버전 관리

### 4.1 스키마 버전 테이블

모든 경로(A, B, C)가 공통으로 사용할 스키마 버전 추적 테이블:

```sql
CREATE TABLE schema_version (
    version_id INT NOT NULL PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    installed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    is_applied BOOLEAN DEFAULT TRUE,
    
    INDEX ix_schema_version_installed_on (installed_on)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
```

**필드**:

- `version_id`: 정수 버전 ID (Alembic 타임스탐프 대신 증가 정수 권장)
- `description`: 마이그레이션 목적 (예: "Add document.normalized_title column")
- `installed_on`: 자동 타임스탐프 — 호스팅사/앱이 마이그레이션 실행 시간
- `execution_time_ms`: 소요 시간 (참고용, 성능 추적)
- `is_applied`: 논리값 — 정상 적용 여부 (롤백 시 FALSE로 표시, 공용호스팅에서는 거의 사용 안 함)

### 4.2 버전 번호 규칙

Alembic의 타임스탐프 기반 리비전 대신, **증가 정수**를 사용한다.

**이유**:
- 순서가 명확하고 비교 쉬움
- `version_id < required_version` 조건으로 마이그레이션 판단 가능
- 호스팅사/운영자가 번호를 읽기 쉬움

**예**:
```
1 -> Initial schema
2 -> Add revision table
3 -> Add document.normalized_title
4 -> Add audit_events table
5 -> Add session table
```

## 5. 실패 처리 및 복구

### 5.1 마이그레이션 실패 시나리오

| 시나리오 | 원인 | 경로 | 복구 방법 |
|---|---|---|---|
| DDL 실패 (권한 부족) | 앱 계정에 DDL 권한 없음 | C | 호스팅사에 권한 부여 요청, 또는 경로 B로 전환 |
| 부분 적용 (일부만 성공) | 마이그레이션 중간에 오류 | A, B | 호스팅사에 실패한 마이그레이션 재실행 요청 |
| 스키마 버전 불일치 | 앱이 버전을 기록하지 못함 | B, C | 호스팅사가 SQL 실행 후 수작업으로 버전 기록 |
| 콘텐츠 손실 | 마이그레이션 SQL에 DELETE/DROP | 모든 경로 | 백업 복구 (별도 프로세스) |

### 5.2 복구 절차

#### 경로 A/B: 호스팅사 개입 필요

```
1. 호스팅사에 "마이그레이션 [X] 실패" 보고
2. 호스팅사가 상황 진단
3. 호스팅사가 롤백 또는 재실행
4. 앱의 /installer 페이지에서 상태 재확인
```

#### 경로 C: 애플리케이션 자동 복구 시도

```php
// 실패한 마이그레이션 재실행 (한 번만)
$failed = $app['migration.service']->getLastFailed();
if ($failed) {
    try {
        $failed->retry();
        // 성공
    } catch (Exception $e) {
        // 실패 → 수동 개입 필요
        $app['logger']->critical("Migration retry failed", ['version' => $failed->version]);
    }
}
```

## 6. 보안 고려사항

### 6.1 마이그레이션 인터페이스 접근 제어

- `/installer` 및 `/maintenance` 엔드포인트는 **관리자만** 접근 가능해야 한다.
- IP 호스트리스트 제한 권장 (호스팅사/관리자 IP만 허용)
- HTTPS 필수

### 6.2 SQL 표시 정책

- 마이그레이션 SQL은 로그에 남기되, **민감한 정보**(암호 변경 등)는 마스킹한다.
- `/installer/migration/<id>/sql` 엔드포인트는 관리자만 조회 가능해야 한다.

### 6.3 마이그레이션 자동 실행 (경로 C)

- 부팅 단계에서 일반 사용자 요청이 올 수 있으므로, 마이그레이션 실행 중에는
  "Maintenance Mode" 응답을 반환해야 한다.
- DDL 실패 시 앱을 읽기 전용 모드로 전환할 수 있다.

## 7. 웹호스팅별 체크리스트

### cPanel (표준 공용호스팅)

- [ ] 호스팅사에 DDL 권한 문의 (대부분 불가)
- [ ] 권한 불가 시 경로 B (웹 인터페이스 기반) 선택
- [ ] phpMyAdmin 또는 cPanel MySQL 도구에서 SQL 수행 가능 확인
- [ ] charset `utf8mb4` 확인 ([db-web-hosting-constraints.md](db-web-hosting-constraints.md#2-문자셋-제약))
- [ ] 애플리케이션 `/installer` 페이지 접속 (관리자 인증 필수)

### Plesk

- [ ] Plesk 관리 패널에서 MySQL 사용자 권한 확인
- [ ] DDL 권한 부여 가능 여부 확인 (일부 호스팅사는 제공)
- [ ] Plesk 데이터베이스 관리 도구 확인
- [ ] 경로 A (호스팅사 사전 적용) 또는 경로 B (웹 인터페이스) 선택

### DirectAdmin

- [ ] DirectAdmin 관리 패널 > MySQL 관리에서 권한 확인
- [ ] 리셀러/도메인 소유자 계정 권한 수준 파악
- [ ] 경로 A 또는 경로 B 선택

### VPS / 관리형 호스팅

- [ ] SSH 또는 관리 패널에서 root/admin 계정 접근 가능 확인
- [ ] 응용 프로그램 계정(www-data 등)의 권한 확인
- [ ] 경로 C (애플리케이션 자동 마이그레이션) 가능 여부 판단

## 8. 마이그레이션 모니터링

### 8.1 애플리케이션 로그

마이그레이션 성공/실패를 명확하게 로깅한다:

```
[2026-07-10 12:00:00] Migration [0004] started
[2026-07-10 12:00:01] Executing: ALTER TABLE document ADD COLUMN ...
[2026-07-10 12:00:02] Migration [0004] completed (1234ms)
[2026-07-10 12:00:03] schema_version updated: 4
```

### 8.2 운영 대시보드

`/maintenance` 페이지에서 다음을 표시한다:

- 현재 스키마 버전
- 필요한 스키마 버전
- 대기/성공/실패한 마이그레이션
- 마지막 마이그레이션 실행 시간
- 추천 조치 (예: "호스팅사에 연락하세요")

## 9. 관련 문서

- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — 권한과 문자셋 제약의 원출처
- [Migration Portability Checklist](migration-portability-checklist.md) — 마이그레이션 작성 규칙
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — SQL 기능 금지 목록
- [Portable Migration Directory Skeleton](php-db-ui-micro-job-prompts-0351-0670.md) — 0459 portable migration skeleton
- [DB Phase QA Checklist](db-phase-qa-checklist.md) — DB 단계 QA 절차

## 이 문서 이후 단계

- **0518**: [PHP Installer DB Check Skeleton](php-db-ui-micro-job-prompts-0351-0670.md) — 
  이 정책이 정의한 웹 인터페이스의 첫 골격 (스키마 버전 확인만).
- **0519**: [Installer DB Check Tests](php-db-ui-micro-job-prompts-0351-0670.md) — 
  설치 단계 테스트.
- **0520**: [ANSI DB Phase Summary](php-db-ui-micro-job-prompts-0351-0670.md) — 
  Phase C 완료 요약.
