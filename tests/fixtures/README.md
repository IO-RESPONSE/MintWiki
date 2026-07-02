# tests/fixtures — 테스트 픽스처

**Phase C: ANSI SQL and MariaDB Portable DB Layer (0441-0520)** 테스트 픽스처.

## 목적

PostgreSQL/MariaDB 양쪽 데이터베이스에서 동일하게 실행할 수 있는 portable seed 픽스처를 저장한다.

## 디렉토리 구조

```
tests/fixtures/
├── README.md       # 이 문서
└── seed/           # Portable seed 픽스처 데이터
    ├── README.md   # Seed 픽스처 작성 규칙
    ├── documents.sql  # 기본 문서 데이터
    ├── revisions.sql  # 기본 리비전 데이터
    └── collation_korean_titles.sql  # MariaDB collation fixture: 한글 제목 테스트 데이터
```

## 특징

- 모든 seed 파일은 [ANSI SQL Persistence Policy](../../docs/ansi-sql-persistence-policy.md)를 따르는 portable SQL만 사용한다.
- INSERT 문은 PostgreSQL/MariaDB 모두에서 동일하게 실행된다.
- UUID 값과 timestamp는 고정 문자열로 결정론적으로 생성되며, 테스트 재현성을 보장한다.

## 관련 작업

- **0490**: Portable seed fixture 추가 (이 디렉토리)
- **0491**: Python seed loader 추가 (`src/persistence/` 경유)
- **0492**: PHP seed loader 추가 (`php/tests/` 경유)
- **0511**: MariaDB collation fixture 테스트 추가 (`test_mariadb_collation_fixture.py`, `collation_korean_titles.sql`)
