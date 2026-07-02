-- revisions.sql - 기본 리비전 데이터
-- Portable seed 픽스처: PostgreSQL, MariaDB 양쪽에서 동일하게 실행됨

-- 리비전 1: Home 문서의 첫 번째 버전
INSERT INTO revision (id, document_id, source, author_id, summary, parent_revision_id, created_at)
VALUES (
    'rev-00001-0000-0000-0000-000000000000',
    'doc-00001-0000-0000-0000-000000000000',
    'Welcome to the wiki engine database test.',
    'user-00001-0000-0000-0000-000000000000',
    'Initial home page content',
    NULL,
    '2026-01-02T00:00:00Z'
);

-- 리비전 2: Documentation 문서의 첫 번째 버전
INSERT INTO revision (id, document_id, source, author_id, summary, parent_revision_id, created_at)
VALUES (
    'rev-00002-0000-0000-0000-000000000000',
    'doc-00002-0000-0000-0000-000000000000',
    'This is the documentation page. It contains important information about the wiki engine.',
    'user-00001-0000-0000-0000-000000000000',
    'Initial documentation content',
    NULL,
    '2026-01-02T01:00:00Z'
);

-- 리비전 3: Home 문서의 두 번째 버전 (업데이트)
INSERT INTO revision (id, document_id, source, author_id, summary, parent_revision_id, created_at)
VALUES (
    'rev-00003-0000-0000-0000-000000000000',
    'doc-00001-0000-0000-0000-000000000000',
    'Welcome to the wiki engine database test. Updated with more information.',
    'user-00002-0000-0000-0000-000000000000',
    'Updated home page with more details',
    'rev-00001-0000-0000-0000-000000000000',
    '2026-01-02T12:00:00Z'
);

-- 리비전 4: Documentation 문서의 두 번째 버전 (업데이트)
INSERT INTO revision (id, document_id, source, author_id, summary, parent_revision_id, created_at)
VALUES (
    'rev-00004-0000-0000-0000-000000000000',
    'doc-00002-0000-0000-0000-000000000000',
    'This is the documentation page. It contains important information about the wiki engine. See also: [[Home]].',
    'user-00002-0000-0000-0000-000000000000',
    'Added cross-reference to Home',
    'rev-00002-0000-0000-0000-000000000000',
    '2026-01-02T13:00:00Z'
);
