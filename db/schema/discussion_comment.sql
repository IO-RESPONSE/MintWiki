-- discussion_comment: 토론 스레드에 달린 댓글 테이블.
-- 스펙 원출처: src/modules/discussion/comment.py의 DiscussionComment,
-- docs/discussion-portable-repository-plan.md §4.
--
-- 테이블 이름: discussion_thread.sql(0466)과 동일하게 모듈 접두어를 남긴다
-- (discussion-portable-repository-plan.md §2).
--
-- thread_id (FK): DiscussionComment.thread_id가 가리키는
-- discussion_thread는 이 파일과 같은 태스크(0466)가 만든 테이블이라 FK를
-- 건다.
--
-- created_by (FK 없음): discussion_thread.created_by와 동일 근거 — account
-- 테이블이 아직 DB 테이블이 아니므로 FK를 걸 대상이 없다.
--
-- body (TEXT): 댓글 본문은 길이 상한이 없는 자유 텍스트라
-- document/revision의 본문 컬럼과 동일하게 TEXT를 쓴다
-- (discussion-portable-repository-plan.md §4).
--
-- is_hidden/hidden_at: to_public_view()/to_moderator_view()(comment.py)의
-- body 마스킹은 조회 이후 애플리케이션 계층 책임이라 DB는 항상 실제
-- body를 저장한다 — is_hidden은 그 마스킹 여부를 결정하는 플래그일 뿐이다.
--
-- 인덱스: list_comments_by_thread_id(repository.py)가 thread_id로
-- 필터링한 뒤 limit/offset으로 여러 번에 걸쳐 잘라 호출한다.
-- discussion_thread.sql과 동일한 이유로 id를 2차 정렬 키로 쓰는
-- (thread_id, created_at, id) 복합 인덱스를 둔다
-- (discussion-portable-repository-plan.md §5).
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / thread_id: [Portable ID Column Policy]에 따라 애플리케이션이
--   생성한 UUID 문자열(VARCHAR(255))만 저장한다. 두 DB 모두
--   SERIAL/AUTO_INCREMENT/UUID() 생성 함수를 쓰지 않으므로 DDL이 동일하다.
-- - created_at / hidden_at: [Portable Timestamp Column Policy]에 따라
--   애플리케이션이 UTC로 정규화한 값을 INSERT/UPDATE 이전에 채워 넣는다.
--   PostgreSQL TIMESTAMP와 MariaDB TIMESTAMP 모두 그 값을 그대로 저장하며,
--   MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지 않는다
--   (discussion_thread.sql과 동일 판단).
-- - is_hidden: 두 DB 모두 표준 BOOLEAN을 지원한다(MariaDB는 TINYINT(1)의
--   별칭으로 처리) — 네이티브 방언 전용 타입이 아니므로 DDL이 동일하다.
CREATE TABLE discussion_comment (
    id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    hidden_at TIMESTAMP NULL,
    CONSTRAINT pk_discussion_comment PRIMARY KEY (id),
    CONSTRAINT fk_discussion_comment_thread_id FOREIGN KEY (thread_id) REFERENCES discussion_thread (id)
);

CREATE INDEX ix_discussion_comment_thread_id_created_at_id
    ON discussion_comment (thread_id, created_at, id);
