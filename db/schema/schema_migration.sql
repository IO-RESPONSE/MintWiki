-- schema_migration: portable 마이그레이션 러너의 적용 이력 테이블.
-- 스펙 원출처: db/README.md "적용 이력 테이블" 절.
-- ANSI SQL 초안 — PostgreSQL/MariaDB 모두 동일하게 실행된다.
CREATE TABLE schema_migration (
    version VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_schema_migration PRIMARY KEY (version)
);
