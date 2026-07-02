# PostgreSQL DSN Compatibility

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 문서.
[MariaDB DSN Config Placeholder](../src/app/config.py)(0470)가 추가한
`mariadb_dsn` 설정값과, 기존 개발 환경이 이미 쓰고 있는
`database_url`(PostgreSQL DSN)이 같은 애플리케이션 설정 계층
(`Settings`)에 공존한다. 이 문서는 새 정책을 만들지 않는다 — 지금
`.env.example`/`config.py`/`database.py`가 실제로 쓰는 PostgreSQL DSN
형식을 기준으로, 두 DSN이 어떤 부분에서 같은 규칙을 따르고 어떤 부분에서
달라지는지를 정리해 [MariaDB Compatibility
Matrix](mariadb-compatibility-matrix.md)와 [ANSI SQL Persistence
Policy](ansi-sql-persistence-policy.md)가 이미 확정한 DB 정책에 연결한다.

## 목적과 범위

- 대상: `WIKI_DATABASE_URL`(PostgreSQL, 현재 사용 중)과
  `WIKI_MARIADB_DSN`(MariaDB, 0470에서 추가한 placeholder) 두 환경 변수의
  DSN 문자열 형식.
- 이 문서는 드라이버 전환을 다루지 않는다. `database.py`는 여전히
  `database_url`만 읽어 엔진을 생성하며, `mariadb_dsn`은 값을 읽어 두기만
  할 뿐 어디에서도 소비되지 않는다([config.py](../src/app/config.py) 주석
  참고). 실제 전환 시점과 방식은 이 문서의 범위 밖이다.
- 목표는 **PHP/MariaDB 이식 시점에 DSN을 다루는 코드가 예상치 못한 형식
  차이로 깨지지 않도록**, 지금부터 두 DSN을 같은 필드 구조로 문서화해
  두는 것이다.

## 현재 PostgreSQL DSN

[.env.example](../.env.example)과 [config.py](../src/app/config.py)가
정의하는 기본값 기준:

```
WIKI_DATABASE_URL=postgresql://wiki:wiki@localhost:5432/wiki_engine
```

[database.py](../src/app/database.py)는 엔진 생성 시점에
`postgresql://` 스킴을 `postgresql+asyncpg://`로 치환해 SQLAlchemy 비동기
드라이버(asyncpg)를 지정한다. 즉 **설정값 자체는 드라이버 이름을 포함하지
않는 일반 스킴**을 쓰고, 드라이버 선택은 애플리케이션 코드가 담당한다.

## MariaDB DSN placeholder

[.env.example](../.env.example)이 주석 처리해 둔 예시:

```
WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine
```

PostgreSQL DSN과 달리 스킴에 드라이버 이름(`+pymysql`)을 이미 포함한다.
이는 0470 시점에 실제 드라이버를 아직 고르지 않았기 때문에, 나중에 다른
드라이버(`mysql+mysqldb`, `mysql+aiomysql` 등)로 바뀔 수 있는 **placeholder
표기**다 — PostgreSQL DSN처럼 "일반 스킴 + 코드에서 드라이버 부착" 방식으로
통일할지, 스킴에 드라이버를 명시하는 방식을 유지할지는 실제 드라이버 전환
잡의 결정 사항이며 이 문서가 지금 확정하지 않는다.

## 필드 단위 비교

| 필드 | PostgreSQL DSN | MariaDB DSN | 상태 |
|---|---|---|---|
| 스킴 | `postgresql://` (코드가 `+asyncpg` 부착) | `mysql+pymysql://` (스킴에 드라이버 포함) | 차이(주의) — 위 절 참고 |
| 사용자/비밀번호 | `user:password@` | `user:password@` | 공통 |
| 호스트 | `host` | `host` | 공통 |
| 기본 포트 | `5432` | `3306` | 차이(정보성) — DSN에 항상 명시한다 |
| 데이터베이스 이름 | 경로 마지막 세그먼트 (`/wiki_engine`) | 경로 마지막 세그먼트 (`/wiki_engine`) | 공통 |
| 쿼리 파라미터(옵션) | 미사용 (현재 기본값 기준) | 미사용 (현재 기본값 기준) | 공통 — 두 DSN 모두 지금은 접속 옵션을 쓰지 않는다 |

## 이 문서가 연결하는 정책

- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 지원
  버전(PostgreSQL: 현재 개발 환경, MariaDB: 10.6 LTS)과 타입/인덱스/
  트랜잭션/collation 차이를 확정한 문서. 이 DSN 비교는 그 문서가 전제하는
  "두 DB가 공존하는 개발 환경"의 접속 설정 쪽을 보완한다.
- [ANSI SQL Persistence Policy](ansi-sql-persistence-policy.md) — DSN
  형식 차이와 무관하게, 실행되는 SQL 자체는 이 정책의 금지 목록을 따라야
  한다.
- [config.py](../src/app/config.py) / [.env.example](../.env.example) —
  이 문서가 기술하는 실제 설정값의 출처. DSN 형식이 바뀌면 이 문서도
  함께 갱신한다.

## 이 문서 이후 단계

- 실제 드라이버 전환(0470 노트: "아직 드라이버 전환은 하지 않는다"가
  풀리는 시점)에서, 이 문서의 "필드 단위 비교" 표를 기준으로 두 DSN을
  같은 파싱 로직으로 다룰 수 있는지 재검토한다.
- [DB driver capability model](php-db-ui-micro-job-prompts-0351-0670.md)
  (0472)은 DSN 형식이 아니라 드라이버가 지원하는 기능(returning/json/
  fulltext)을 다루므로 이 문서와 범위가 겹치지 않는다.
