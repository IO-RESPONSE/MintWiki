# MariaDB 로컬 Compose Override

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
로컬 개발 환경에서 기본 PostgreSQL 대신 MariaDB를 사용하기 위한 Docker Compose
설정 방법을 설명한다. 이 문서는 정책을 새로 만들지 않는다 — 개발자가
[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)와
[Portable Schema Naming Policy](portable-schema-naming-policy.md) 등 기존 정책
하에서 로컬에서 MariaDB를 테스트하고자 할 때 따를 절차를 기술한다.

## 목적과 범위

- **대상**: 로컬 개발 환경에서 PostgreSQL 대신 MariaDB 10.6 LTS를 사용하고자
  하는 개발자.
- **범위**: `docker-compose.yml`의 기존 PostgreSQL 서비스를 유지하면서, Docker
  Compose의 **profiles** 기능을 통해 MariaDB 서비스를 선택적으로 활성화하는
  방법을 설명한다.
- **이 문서가 정하지 않는 것**:
  - 실제 `docker-compose.yml` 파일 구조 변경 — [0502 Add MariaDB compose
    profile](php-db-ui-micro-job-prompts-0351-0670.md)의 범위.
  - MariaDB 버전 선택, 이미지 소스, 시스템 성능 최적화 — 이 문서는 기본 10.6
    LTS 이미지 기준으로만 다룬다.
  - 프로덕션 MariaDB 배포 — 이는 로컬 개발 환경이 아닌 별도 배포 절차.
  - PHP 또는 다른 언어 스택의 MariaDB 통합 — 각 언어/프레임워크별 문서에서 다룬다.

## 소개: PostgreSQL과 MariaDB 병행 운영

`docker-compose.yml`은 기본적으로 **PostgreSQL** 서비스와 애플리케이션을
함께 부팅하는 설정이다([README.md](../README.md)의 "로컬 환경" 절 참고).
이 기본 설정은 변경되지 않는다.

개발자가 MariaDB 이식 가능성을 테스트하려면, 동일한 네트워크 안에서
**MariaDB 서비스를 선택적으로 추가**할 수 있다. Docker Compose의
`profiles` 기능을 통해:

- `docker compose up` (기본) — PostgreSQL 실행
- `docker compose --profile mariadb up` (프로필 활성화) — PostgreSQL과
  MariaDB 함께 실행

이 방식은 기존 PostgreSQL 의존 개발 작업을 막지 않으면서도, MariaDB
호환성을 병행 검증할 수 있게 한다.

## 전제 조건

1. **Docker & Docker Compose** — 로컬에 설치되어 있어야 한다.
   ```bash
   docker --version
   docker compose --version
   ```

2. **포트 가용성**:
   - PostgreSQL: `5432` (기본)
   - MariaDB: `3306` (새로 추가)
   
   이 포트들이 로컬에서 이미 사용 중이면 `docker-compose.yml`의
   포트 매핑을 조정해야 한다.

3. **환경 파일** — `.env` 파일이 준비되어 있어야 한다.
   ```bash
   cp .env.example .env
   ```
   자세한 설정은 다음 절을 참고한다.

## 환경 설정

### 1. `.env` 파일 준비

기본 `.env`는 PostgreSQL URL만 포함한다:
```env
WIKI_DATABASE_URL=postgresql://wiki:wiki@localhost:5432/wiki_engine
```

MariaDB를 사용할 때는 추가로 `WIKI_MARIADB_DSN` 변수를 설정한다:
```env
WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine
```

**주의**: 현재(Phase C 중) 애플리케이션은 여전히 `WIKI_DATABASE_URL`을
기본으로 사용한다. `WIKI_MARIADB_DSN`은
[config.py](../src/app/config.py)에서 읽기만 하고 실제 드라이버는
아직 전환되지 않았다(드라이버 전환은 0470 이후 잡의 범위).
MariaDB를 **네트워크에서 실행하고 스키마를 smoke 테스트**하려면
두 URL을 모두 설정하되, 애플리케이션 쿼리는 여전히 PostgreSQL을 통한다.

### 2. 포트 매핑 확인

기본 `docker-compose.yml`:
- app: `8000:8000`
- postgres: `5432:5432`

MariaDB 프로필 추가 후 (0502 작업):
- mariadb: `3306:3306`

기본 포트를 바꾸려면 `.env`에서 `docker-compose.yml`의 포트를 오버라이드할 수 있다
(Docker Compose variable 치환 참고).

### 3. 선택사항: 커스텀 포트

포트 충돌이 있으면, `docker-compose.yml` 또는 `.env`에서 MariaDB 포트를 변경:
```env
# .env에 추가 (docker-compose.yml에서 ${MARIADB_PORT:-3306} 같이 참조하도록 수정된 경우)
MARIADB_PORT=3307
```

## 사용 방법

### PostgreSQL 만 실행 (기본)

```bash
# 기본: PostgreSQL만 실행
docker compose up --build

# 접속 확인
psql postgresql://wiki:wiki@localhost:5432/wiki_engine
```

### PostgreSQL과 MariaDB 함께 실행

```bash
# mariadb 프로필 활성화
docker compose --profile mariadb up --build

# 또는 환경 변수로 프로필 지정
COMPOSE_PROFILES=mariadb docker compose up --build
```

이 명령 실행 후:
- PostgreSQL은 `localhost:5432`
- MariaDB는 `localhost:3306`
- app은 `http://localhost:8000`

에서 각각 가용하다.

### MariaDB 접속 및 기본 검사

```bash
# MySQL 클라이언트로 접속 (docker-compose 컨테이너 내부)
docker compose exec -it mariadb mysql -u wiki -p -h localhost
# 비밀번호: wiki (docker-compose.yml의 환경 변수 참고)

# 또는 호스트에서 (mysql 클라이언트가 설치된 경우)
mysql -u wiki -p -h localhost -P 3306 -D wiki_engine

# 기본 테이블 확인
SHOW TABLES;
```

## 스키마 적용 (Smoke Testing)

MariaDB가 실행 중일 때, portable SQL 스키마를 적용할 수 있다.

### 수동 적용 (개발 중)

```bash
# docker-compose 컨테이너 내부에서
docker compose exec mariadb mysql -u wiki -p -h localhost wiki_engine < /path/to/db/schema/table.sql

# 또는 호스트의 mysql 클라이언트 사용
mysql -u wiki -p -h localhost -P 3306 wiki_engine < db/schema/account.sql
```

### 자동 smoke 테스트

[0481 Add optional MariaDB test script](php-db-ui-micro-job-prompts-0351-0670.md)가
`WIKI_MARIADB_DSN` 환경 변수를 확인하여 자동으로 smoke 테스트를 실행한다.

```bash
# MariaDB 프로필 활성화 후, scripts/test.sh 또는 scripts/qa.sh 실행
COMPOSE_PROFILES=mariadb docker compose up -d
scripts/qa.sh
```

smoke 테스트는:
1. `WIKI_MARIADB_DSN`의 존재 여부를 확인한다.
2. 존재하면 `db/schema/*.sql`을 MariaDB에 순서대로 적용한다.
3. 존재하지 않으면 skip한다(실패로 처리하지 않음).

자세한 계획은 [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) 참고.

## PostgreSQL과 MariaDB 간 호환성 검증

### 1. 스키마 호환성 검증

`db/schema/` 아래 portable SQL 원본이 두 DB에서 모두 적용되는지
확인한다:

```bash
# PostgreSQL 대상 (기본 django 마이그레이션)
python -m pytest tests/ -v

# MariaDB 대상 (0481 smoke 스크립트)
COMPOSE_PROFILES=mariadb docker compose up -d
WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine scripts/qa.sh
```

### 2. 타입/인덱스/collation 검증

[MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md)의
"타입/인덱스/트랜잭션/collation 매트릭스"에 따라:

- `BOOLEAN` 타입은 MariaDB에서 `TINYINT(1)` 별칭이지만, SQLAlchemy
  `Boolean` 타입만 사용하면 양쪽 호환.
- `TIMESTAMP WITH TIME ZONE`은 MariaDB에서 지원 안 함 — 애플리케이션이
  UTC 정규화 필요 ([portable-timestamp-column-policy.md](portable-timestamp-column-policy.md) 참고).
- 인덱스/collation 정책은 [portable-schema-naming-policy.md](portable-schema-naming-policy.md),
  [portable-text-collation-policy.md](portable-text-collation-policy.md) 참고.

### 3. SQL 금지 항목 검사

`check_sql_denylist.py` 스크립트 (0447)로 PostgreSQL 전용 기능 도입을
자동 탐지한다:

```bash
python scripts/check_sql_denylist.py db/schema/
python scripts/check_sql_denylist.py src/
```

자세한 금지 목록은 [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) 참고.

## 트러블슈팅

### MariaDB 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker compose --profile mariadb logs mariadb

# 포트 충돌 확인
sudo lsof -i :3306

# 컨테이너 상태 확인
docker compose ps
```

### 접속 오류: "Connection refused"

```bash
# MariaDB가 실행 중인지 확인
docker compose ps | grep mariadb

# 네트워크 확인 (app 컨테이너에서)
docker compose exec app ping mariadb

# MariaDB가 포트 대기 중인지 확인
docker compose exec mariadb mysql -u wiki -p -h localhost -e "SELECT 1;"
```

### SQL 오류: "Syntax error near ..."

이 오류는 보통 PostgreSQL 전용 SQL 문법을 사용했을 때 발생한다.

```bash
# 금지 목록 확인
grep -r "JSONB\|ARRAY\|ILIKE" db/schema/

# compatibility matrix 검증
python scripts/check_sql_denylist.py db/schema/
```

자세한 호환성 규칙은 [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) 참고.

### 파일 권한 오류

호스트에서 `docker-compose.yml`의 `volumes`에 바인드 마운트하는 경우, 파일
권한이 컨테이너 내부 MariaDB 사용자와 맞아야 한다:

```bash
# 스키마 파일 권한 확인
ls -la db/schema/

# MariaDB가 읽을 수 있도록 권한 설정 (필요 시)
chmod 644 db/schema/*.sql
```

## 관련 문서

- [README.md](../README.md) — 기본 로컬 환경 부트스트랩 (PostgreSQL).
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) —
  PostgreSQL과 MariaDB의 타입, 인덱스, 트랜잭션, collation 차이.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) —
  MariaDB 이식을 위해 금지되는 SQL 기능 목록.
- [Portable Schema Naming Policy](portable-schema-naming-policy.md) —
  두 DB에 모두 호환되는 스키마 이름 규칙.
- [Portable Timestamp Column Policy](portable-timestamp-column-policy.md) —
  타임존 처리 정책.
- [Portable Text Collation Policy](portable-text-collation-policy.md) —
  문자열 비교/정렬 정책.
- [MariaDB Migration Smoke Plan](mariadb-migration-smoke-plan.md) —
  MariaDB 서버에 대한 smoke 테스트 계획 및 실행 조건.
- [MariaDB 헬스 체크](mariadb-health-check.md) —
  MariaDB 연결 상태를 확인하는 방법 (헬스 엔드포인트, CLI, smoke 테스트).
- [0481 Add optional MariaDB test script](php-db-ui-micro-job-prompts-0351-0670.md) —
  실제 smoke 테스트 스크립트 구현 (이 문서의 자동 smoke 절 참고).
- [0502 Add MariaDB compose profile](php-db-ui-micro-job-prompts-0351-0670.md) —
  `docker-compose.yml`의 실제 MariaDB 프로필 구현.
- [db/README.md](../db/README.md) — portable 스키마 및 마이그레이션 디렉토리.
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) —
  Phase C 잡 목록 전체.

## 역사 및 버전

이 문서는 Phase C (0441-0520)에서:
- **0441**: 요구사항 정의
- **0442**: MariaDB 최소 지원 버전 확정 (10.6 LTS)
- **0501**: 이 문서 작성
- **0502**: `docker-compose.yml`에 MariaDB 프로필 구현
- **0481**: smoke 테스트 스크립트 구현

를 거쳐 개발된다.
