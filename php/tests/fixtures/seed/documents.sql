-- documents.sql - 기본 문서 데이터
-- Portable seed 픽스처: PostgreSQL, MariaDB 양쪽에서 동일하게 실행됨

-- 문서 1: 홈페이지
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-00001-0000-0000-0000-000000000000',
    'Home',
    'Home',
    'rev-00001-0000-0000-0000-000000000000',
    '2026-01-01T00:00:00Z',
    '2026-01-02T12:00:00Z'
);

-- 문서 2: 문서
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-00002-0000-0000-0000-000000000000',
    'Documentation',
    'Documentation',
    'rev-00002-0000-0000-0000-000000000000',
    '2026-01-01T01:00:00Z',
    '2026-01-02T13:00:00Z'
);

-- 문서 3: 테스트
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-00003-0000-0000-0000-000000000000',
    'Test Page',
    'Test Page',
    NULL,
    '2026-01-01T02:00:00Z',
    '2026-01-01T02:00:00Z'
);
