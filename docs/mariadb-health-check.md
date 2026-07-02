# MariaDB 헬스 체크

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
로컬 개발 환경 및 CI 환경에서 MariaDB 서버의 연결 상태를 확인하는 방법을 기술한다.
이 문서는 새 정책을 만들지 않는다 — 운영자가 기존 정책 하에서 MariaDB 연결 상태를
확인할 수 있는 절차와 명령을 정리한다.

## 목적과 범위

- **대상**: 로컬 개발 환경 또는 CI 환경에서 MariaDB 서버가 가용한지 확인하려는
  개발자 및 운영자.
- **범위**: 세 가지 헬스 체크 방법을 제시한다.
  1. 애플리케이션 `/health` 엔드포인트를 통한 기본 상태 확인.
  2. `mysql`/`mariadb` CLI 클라이언트를 이용한 직접 연결 확인.
  3. 포괄적 smoke 테스트(`scripts/mariadb_smoke_check.py`)를 통한 스키마
     적용 가능성 검증.
- **이 문서가 정하지 않는 것**:
  - MariaDB 서버 설치/부팅 절차 — Docker Compose로 로컬 부팅하는 방법은
    [MariaDB 로컬 Compose Override](mariadb-local-compose-override.md) 참고.
  - 운영 환경(프로덕션) MariaDB 모니터링 — 별도 운영 가이드 범위.
  - 성능/부하 모니터링, 로그 분석 — MariaDB 공식 운영 가이드 참고.
  - 자동화된 헬스 체크 엔드포인트 구현(DB 연결 포함) — [0518 Add database
    health check](php-db-ui-micro-job-prompts-0351-0670.md) 범위.

## 1. 애플리케이션 헬스 엔드포인트

애플리케이션은 `GET /health` 엔드포인트를 제공한다. 이는 현재 기본적인
애플리케이션 상태만 반환하며 **데이터베이스 연결 상태는 포함하지 않는다**
(DB 헬스 체크는 0518 범위).

### 엔드포인트 명세

```http
GET /health
```

**응답 예시** (200 OK):
```json
{
  "status": "ok",
  "app": "wiki-engine",
  "environment": "development"
}
```

### 사용 예

```bash
# 로컬 개발 서버 상태 확인 (앱이 실행 중인지만 확인)
curl http://localhost:8000/health

# 출력 (앱이 실행 중이면)
# {"status":"ok","app":"wiki-engine","environment":"development"}

# 상태 코드 확인 (반환 코드 200 = 앱 가용, 0이 아닌 코드 = 앱 비가용)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
```

**주의**: 이 엔드포인트는 애플리케이션 프로세스가 실행 중인지만 확인한다.
MariaDB 연결 여부는 확인하지 않는다.

## 2. CLI 클라이언트를 통한 직접 연결 확인

MariaDB 또는 MySQL CLI 클라이언트를 이용해 직접 연결을 테스트할 수 있다.

### 전제 조건

- `mysql` 또는 `mariadb` CLI 클라이언트가 설치되어 있어야 한다.
  ```bash
  # 설치 확인
  which mysql
  which mariadb
  ```

- MariaDB 서버가 실행 중이어야 한다 ([MariaDB 로컬 Compose Override](mariadb-local-compose-override.md) 참고).

### 연결 테스트

#### 호스트에서 직접 연결 (로컬 개발 환경)

```bash
# 기본 연결 테스트
mysql -u wiki -p -h localhost -P 3306 -D wiki_engine

# 프롬프트에서 비밀번호 입력 (기본값: wiki)
# 또는 비밀번호를 직접 전달 (권장하지 않음)
mysql -u wiki -pWIKI_PASSWORD -h localhost -P 3306 -D wiki_engine
```

**연결 성공**: `mysql>` 프롬프트가 나타난다.

**연결 실패 오류 메시지**:
```
ERROR 2003 (HY000): Can't connect to MySQL server on 'localhost' (111)
```
→ 서버가 실행 중이지 않거나 포트가 다를 수 있다. 포트 설정을 확인하자.

```
ERROR 1045 (28000): Access denied for user 'wiki'@'localhost' (using password: YES)
```
→ 사용자명 또는 비밀번호가 잘못되었다. 설정을 확인하자.

#### Docker Compose 컨테이너 내부에서 연결 (로컬 개발 환경)

[MariaDB 로컬 Compose Override](mariadb-local-compose-override.md)에서
`docker compose --profile mariadb up`으로 MariaDB를 부팅한 경우:

```bash
# 컨테이너 내부에서 CLI 실행
docker compose exec -it mariadb mysql -u wiki -p -h localhost

# 또는 bash를 통해 실행
docker compose exec -it mariadb bash
mysql> mysql -u wiki -p -h localhost
```

### 기본 상태 쿼리

연결 성공 후, 다음 쿼리로 서버 상태를 확인할 수 있다:

```sql
-- 서버 버전 확인
SELECT VERSION();

-- 현재 사용자/연결 정보 확인
SELECT USER(), DATABASE();

-- 간단한 연결 테스트
SELECT 1;

-- 데이터베이스 목록 확인
SHOW DATABASES;

-- 현재 데이터베이스의 테이블 확인 (wiki_engine 대상)
SHOW TABLES;

-- 테이블 상세 정보 (예: account 테이블)
DESCRIBE account;

-- 현재 세션 정보 확인
SHOW VARIABLES LIKE '%version%';
```

### 일회성 쿼리 실행

CLI 프롬프트를 열지 않고 한 번에 결과를 얻을 수 있다:

```bash
# SELECT 1로 연결 가능 여부 확인 (반환 코드로 판단)
mysql -u wiki -p -h localhost -D wiki_engine -e "SELECT 1;" 2>/dev/null && echo "연결 성공" || echo "연결 실패"

# 테이블 목록 확인
mysql -u wiki -p -h localhost -D wiki_engine -e "SHOW TABLES;"

# 특정 테이블 행 수 확인
mysql -u wiki -p -h localhost -D wiki_engine -e "SELECT COUNT(*) FROM account;"
```

**팁**: `-p` 플래그만 사용하면 프롬프트에서 비밀번호를 묻는다(보안상 권장).
스크립트에서 비밀번호를 자동화하려면 `~/.my.cnf` 파일에 자격증명을 저장할 수 있다.

## 3. 포괄적 Smoke 테스트를 통한 검증

[MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md)에서 계획한
자동 smoke 테스트를 실행하면, 연결 + 스키마 적용 가능성까지 한번에 검증할 수 있다.

### 전제 조건

1. **MariaDB 서버 가용**: 로컬 또는 CI 환경에서 실행 중.
2. **`WIKI_MARIADB_DSN` 환경 변수 설정**:
   ```bash
   export WIKI_MARIADB_DSN="mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine"
   ```
   또는 `.env` 파일에 설정:
   ```env
   WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine
   ```

3. **`mysql` 또는 `mariadb` CLI 클라이언트 설치**.

### 실행

```bash
# 로컬 개발 환경: MariaDB 프로필 부팅 후 smoke 테스트
docker compose --profile mariadb up -d
python scripts/mariadb_smoke_check.py

# 또는 qa.sh에 포함된 자동 실행
WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine scripts/qa.sh
```

### 결과 해석

**통과** (반환 코드 0):
```
✅ MariaDB smoke 테스트 통과: 12개 테이블 모두 생성 확인
```

이는 다음을 의미한다:
- MariaDB 서버에 성공적으로 연결됨.
- `db/schema/*.sql`의 모든 테이블이 FK 의존 순서대로 적용되었음.
- 스키마가 MariaDB 문법과 호환됨.

**Skip** (반환 코드 0, skip 메시지):
```
⏭  MariaDB smoke 테스트 skip: WIKI_MARIADB_DSN 이 설정되지 않았습니다
```

또는:
```
⏭  MariaDB smoke 테스트 skip: mysql/mariadb CLI 클라이언트를 찾을 수 없습니다
```

또는:
```
⏭  MariaDB smoke 테스트 skip: localhost:3306 접속에 실패했습니다
```

이는 실패가 아니라 skip이다 ([MariaDB Migration Smoke Plan §1](mariadb-migration-smoke-plan.md#1-실행-조건-선택-실행)
참고). 개발 환경/CI에서 MariaDB 서버가 항상 가용하지 않아도 다른 검사는
정상적으로 진행된다.

**실패** (반환 코드 1):
```
❌ MariaDB smoke 테스트 실패: DDL 적용 실패 (account.sql): ...
```

또는:
```
❌ MariaDB smoke 테스트 실패: 테이블 존재 확인 실패: 생성되지 않은 테이블 [...]
```

이는 실제 오류다. 원인을 분석하고 수정해야 한다 ([§4 실패 판정 기준](mariadb-migration-smoke-plan.md#4-실패-판정-기준) 참고).

### 상세 로그 확인

smoke 테스트가 실패했을 때 더 자세한 정보를 보려면 스크립트를 직접 실행하고
`stderr`를 확인한다:

```bash
python scripts/mariadb_smoke_check.py 2>&1 | tee mariadb_smoke.log
```

## 4. 트러블슈팅

### "Can't connect to MySQL server" 오류

```bash
# 1. 포트가 올바른지 확인
sudo netstat -tulpn | grep 3306

# 2. Docker 컨테이너가 실행 중인지 확인
docker compose ps | grep mariadb

# 3. 서버 로그 확인
docker compose logs mariadb | tail -50

# 4. 방화벽 규칙 확인 (필요시)
sudo ufw allow 3306
```

### "Access denied for user" 오류

```bash
# 1. 사용자명/비밀번호 확인 (docker-compose.yml 참고)
grep -A 5 "mariadb:" docker-compose.yml

# 2. .env 파일 확인
cat .env | grep MARIADB

# 3. 컨테이너 내 MySQL 사용자 확인 (필요시)
docker compose exec mariadb mysql -u root -e "SELECT User, Host FROM mysql.user;"
```

### Smoke 테스트의 "DDL 적용 실패"

```bash
# 1. 스키마 파일 확인
ls -la db/schema/

# 2. 개별 스키마 파일을 수동 적용해 오류 메시지 확인
mysql -u wiki -p -h localhost wiki_engine < db/schema/account.sql

# 3. MariaDB 버전 호환성 확인
mysql -u wiki -p -h localhost -e "SELECT VERSION();"

# 호환성 매트릭스 참고: [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)
```

### 권한(Permission) 오류

```bash
# 1. MariaDB가 스키마 파일을 읽을 수 있는지 확인
ls -la db/schema/*.sql

# 2. 필요시 권한 수정
chmod 644 db/schema/*.sql
```

## 관련 문서

- [MariaDB 로컬 Compose Override](mariadb-local-compose-override.md) —
  로컬 환경에서 MariaDB 부팅 방법.
- [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) —
  smoke 테스트 계획 및 실행 규칙.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) —
  PostgreSQL과 MariaDB의 호환성.
- [db/README.md](../db/README.md) — 스키마 파일 구조.
- [0518 Add database health check](php-db-ui-micro-job-prompts-0351-0670.md) —
  DB 연결 포함 헬스 체크 엔드포인트 구현 (향후 작업).

## 버전 및 업데이트

이 문서는 Phase C (0441-0520)에서:
- **0500**: DB phase QA checklist 작성
- **0501**: MariaDB 로컬 Compose Override 작성
- **0502**: MariaDB Compose profile 구현
- **0503**: 이 헬스 체크 문서 작성

를 거쳐 개발된다. 향후 0518에서 애플리케이션 내 DB 헬스 체크 엔드포인트가
추가되면, 이 문서의 1절이 확대될 것이다.
