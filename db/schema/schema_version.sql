-- schema_version: 배포된 스키마 버전을 추적하는 테이블.
-- 목적: PHP 웹호스팅 installer가 참조할 현재 스키마 버전 정보.
-- [schema_migration]과 다른 점: schema_migration은 각 마이그레이션
-- 적용 이력을 모두 기록하지만, schema_version은 현재 배포된 버전을
-- 단순하게 조회하기 위한 전용 테이블이다.
-- ANSI SQL 초안 — PostgreSQL/MariaDB 모두 동일하게 실행된다.
CREATE TABLE schema_version (
    version VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_schema_version PRIMARY KEY (version)
);
