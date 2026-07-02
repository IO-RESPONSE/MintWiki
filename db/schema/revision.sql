-- revision: 문서 리비전 테이블.
-- 스펙 원출처: src/persistence/models.py의 RevisionORM,
-- migrations/versions/0003_add_revision_table.py.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / document_id / parent_revision_id: [Portable ID Column Policy]에
--   따라 애플리케이션이 생성한 UUID 문자열(VARCHAR(255))만 저장한다.
--   PostgreSQL SERIAL/gen_random_uuid(), MariaDB AUTO_INCREMENT/UUID() 어느
--   쪽도 쓰지 않으므로 두 DB에서 DDL이 동일하다. parent_revision_id는
--   RevisionORM과 0003 마이그레이션 모두 FK 제약이 없어(자기 참조를
--   강제하지 않음) 이 파일도 동일하게 FK 없이 둔다.
-- - created_at: [Portable Timestamp Column Policy]에 따라 애플리케이션이
--   UTC로 정규화한 값을 INSERT 이전에 채워 넣는다. PostgreSQL TIMESTAMP는
--   그 값을 그대로 저장하지만, MariaDB TIMESTAMP는 세션 time_zone 설정에
--   따라 저장되는 실제 시각이 달라질 수 있다 — 두 DB 모두 애플리케이션이
--   이미 UTC 값을 넘기므로 DDL 자체는 동일한 TIMESTAMP로 둔다(MariaDB가
--   지원하지 않는 WITH TIME ZONE은 쓰지 않는다).
-- - source: 리비전 원문. RevisionORM은 표준 TEXT 타입을 쓰고, PostgreSQL과
--   MariaDB 모두 TEXT를 동일하게 지원해 DDL이 동일하다.
CREATE TABLE revision (
    id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    source TEXT NOT NULL,
    author_id VARCHAR(255) NOT NULL,
    summary VARCHAR(500) NOT NULL,
    parent_revision_id VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_revision PRIMARY KEY (id),
    CONSTRAINT fk_revision_document_id FOREIGN KEY (document_id) REFERENCES document (id)
);
