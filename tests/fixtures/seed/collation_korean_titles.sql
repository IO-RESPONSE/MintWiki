-- collation_korean_titles.sql - MariaDB collation fixture: 한글 제목 테스트 데이터
-- Portable seed 픽스처: PostgreSQL, MariaDB 양쪽에서 동일하게 실행됨
--
-- 목적:
-- Portable Text Collation Policy (docs/portable-text-collation-policy.md) §4의
-- 한글 정렬 목표 검증을 위한 fixture 데이터다.
--
-- 검증 항목:
-- 1. utf8mb4_bin collation에서 한글의 코드포인트 정렬이 일정한가
-- 2. 대소문자 다른 제목이 UNIQUE 제약으로 구분되는가
-- 3. 한글 제목 중복이 올바르게 감지되는가
--
-- 사전: 한글을 포함한 정렬은 "완전한 로케일 사전순 일치"가 아니라
-- "유니코드 코드포인트 기준의 안정적 정렬"을 목표로 한다.

-- 한글 제목: 가나다 순서 (코드포인트 순서)
-- NOTE: collation 테스트는 현재_리비전을 요구하지 않으므로 NULL 사용
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10001-0000-0000-0000-000000000000',
    '가나다',
    '가나다',
    NULL,
    '2026-02-01T00:00:00Z',
    '2026-02-01T00:00:00Z'
);

-- 한글 제목: 나다라 (코드포인트 순서)
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10002-0000-0000-0000-000000000000',
    '나다라',
    '나다라',
    NULL,
    '2026-02-02T00:00:00Z',
    '2026-02-02T00:00:00Z'
);

-- 한글 제목: 다라마 (코드포인트 순서)
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10003-0000-0000-0000-000000000000',
    '다라마',
    '다라마',
    NULL,
    '2026-02-03T00:00:00Z',
    '2026-02-03T00:00:00Z'
);

-- 대소문자 테스트 1: 영문 제목 대소문자 구분
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10004-0000-0000-0000-000000000000',
    'TestTitle',
    'TestTitle',
    NULL,
    '2026-02-04T00:00:00Z',
    '2026-02-04T00:00:00Z'
);

-- 대소문자 테스트 2: 같은 제목, 다른 케이스 (UNIQUE 제약으로 구분되어야 함)
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10005-0000-0000-0000-000000000000',
    'testtitle',
    'testtitle',
    NULL,
    '2026-02-05T00:00:00Z',
    '2026-02-05T00:00:00Z'
);

-- 혼합 제목: 한글 + 영문
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10006-0000-0000-0000-000000000000',
    '한글제목',
    '한글제목',
    NULL,
    '2026-02-06T00:00:00Z',
    '2026-02-06T00:00:00Z'
);

-- 혼합 제목: 영문 + 한글
INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at)
VALUES (
    'doc-10007-0000-0000-0000-000000000000',
    'Korean문서',
    'Korean문서',
    NULL,
    '2026-02-07T00:00:00Z',
    '2026-02-07T00:00:00Z'
);
