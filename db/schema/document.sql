-- document: 문서(위키 페이지) 테이블.
-- 스펙 원출처: src/persistence/models.py의 DocumentORM,
-- migrations/versions/0002_add_document_table.py.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / current_revision_id: [Portable ID Column Policy]에 따라
--   애플리케이션이 생성한 UUID 문자열(VARCHAR(255))만 저장한다. PostgreSQL
--   SERIAL/gen_random_uuid(), MariaDB AUTO_INCREMENT/UUID() 어느 쪽도 쓰지
--   않으므로 두 DB에서 DDL이 동일하다. current_revision_id는 revision
--   테이블(0462)이 아직 이 디렉터리에 없어 FK 제약을 걸지 않는다 —
--   migrations/versions/0002_add_document_table.py도 동일하게 FK 없이 둔다.
-- - created_at / updated_at: [Portable Timestamp Column Policy]에 따라
--   애플리케이션이 UTC로 정규화한 값을 INSERT/UPDATE 이전에 채워 넣는다.
--   PostgreSQL TIMESTAMP는 그 값을 그대로 저장하지만, MariaDB TIMESTAMP는
--   세션 time_zone 설정에 따라 저장되는 실제 시각이 달라질 수 있다 — 두 DB
--   모두 애플리케이션이 이미 UTC 값을 넘기므로 DDL 자체는 동일한 TIMESTAMP로
--   둔다(MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지 않는다).
-- - title / normalized_title: [Portable Text Collation Policy]에 따라
--   대소문자를 구분해서 비교해야 한다. PostgreSQL은 기본 문자열 비교가
--   이미 바이트 단위 대소문자 구분이라 컬럼에 별도 지정이 필요 없지만,
--   MariaDB 기본 collation(utf8mb4_general_ci 등)은 대소문자를 구분하지
--   않는다 — 이 차이는 컬럼 정의가 아니라 MariaDB 쪽 서버/DB 문자셋 기본값을
--   utf8mb4_bin으로 맞추는 배포 설정으로 흡수한다(Migration Portability
--   Checklist §4가 컬럼 단위 강제를 이 문서의 범위 밖으로 남긴 것과 동일한
--   판단이며, 0512 이후 정해질 것이다).
CREATE TABLE document (
    id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    normalized_title VARCHAR(500) NOT NULL,
    current_revision_id VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_document PRIMARY KEY (id),
    CONSTRAINT uq_document_normalized_title UNIQUE (normalized_title)
);
