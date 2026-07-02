-- discussion_thread: 문서에 대한 토론 스레드 테이블.
-- 스펙 원출처: src/modules/discussion/thread.py의 DiscussionThread,
-- src/modules/discussion/state.py의 ThreadState,
-- docs/discussion-portable-repository-plan.md §3.
--
-- 테이블 이름: discussion 모듈은 thread/comment 두 도메인 모델을 갖는데,
-- account.sql(0463)/user_session.sql(0464)이 이미 확립한 "모듈 접두어를
-- 테이블 이름에 남긴다"는 관례를 그대로 따라 discussion_thread로 짓는다
-- (discussion-portable-repository-plan.md §2).
--
-- document_id (FK): DiscussionThread.document_id가 가리키는 document는
-- 이미 마이그레이션이 있는 실재 테이블이므로(revision.document_id와 동일
-- 근거), acl_rule.subject_id처럼 다형 참조가 아니라 FK를 그대로 건다.
--
-- created_by (FK 없음): revision.author_id(src/persistence/models.py)가
-- 이미 FK 없이 사용자 식별자를 저장하는 선례를 따른다 — account 테이블
-- 자체가 아직 DB 테이블이 아니므로 지금 FK를 걸 대상이 없다
-- (discussion-portable-repository-plan.md §3).
--
-- status (CHECK 제약 없음): ThreadState(state.py)는 open/closed/paused
-- 세 값을 정의하지만 DiscussionThread.__init__은 이 값을 검증하지 않는다
-- — 계획 문서 §6이 확정한 대로, 애플리케이션 계층이 아직 강제하지 않는
-- 규칙을 스키마에만 먼저 걸면 서비스 계층 통과 후 DB commit 시점에만
-- 실패하는 위치가 생긴다. 따라서 지금은 VARCHAR(20) 자유 문자열로 두고,
-- 기본값만 도메인 기본값("open")과 맞춘다. ThreadState 강제가 도메인
-- 계층에 먼저 들어오면 이 CHECK 여부를 다시 판단한다.
--
-- closed_at/paused_at (서로 독립적인 별도 컬럼): DiscussionThread.close()는
-- paused_at을 건드리지 않고 pause()도 closed_at을 건드리지 않으므로,
-- state_changed_at 하나로 합치지 않고 각각 별도 컬럼으로 둔다.
--
-- 인덱스: list_threads_by_document_id(repository.py)가 document_id로
-- 필터링한 뒤 limit/offset으로 여러 번에 걸쳐 잘라 호출한다.
-- ORDER BY created_at만으로는 동시각 행에서 페이지 경계가 흔들려 행이
-- 중복/누락될 수 있으므로(discussion-portable-repository-plan.md §5),
-- id를 2차 정렬 키로 쓰는 (document_id, created_at, id) 복합 인덱스를
-- 명시적으로 둔다 — revision과 달리 FK가 자동으로 만드는 인덱스만으로는
-- 정렬 키(created_at, id)가 포함되지 않는다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / document_id: [Portable ID Column Policy]에 따라 애플리케이션이
--   생성한 UUID 문자열(VARCHAR(255))만 저장한다. 두 DB 모두
--   SERIAL/AUTO_INCREMENT/UUID() 생성 함수를 쓰지 않으므로 DDL이 동일하다.
-- - created_at / closed_at / paused_at: [Portable Timestamp Column Policy]에
--   따라 애플리케이션이 UTC로 정규화한 값을 INSERT/UPDATE 이전에 채워
--   넣는다. PostgreSQL TIMESTAMP와 MariaDB TIMESTAMP 모두 그 값을 그대로
--   저장하며, MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지 않는다
--   (document.sql/revision.sql/user_session.sql/acl_rule.sql과 동일 판단).
-- - status: [Portable Text Collation Policy]에 따라 고정된 소문자 enum
--   문자열만 저장해 대소문자 비교 이슈가 없다 — 컬럼 정의에 별도 COLLATE
--   지정이 필요 없다(acl_rule.subject_type과 동일 근거).
CREATE TABLE discussion_thread (
    id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP NULL,
    paused_at TIMESTAMP NULL,
    CONSTRAINT pk_discussion_thread PRIMARY KEY (id),
    CONSTRAINT fk_discussion_thread_document_id FOREIGN KEY (document_id) REFERENCES document (id)
);

CREATE INDEX ix_discussion_thread_document_id_created_at_id
    ON discussion_thread (document_id, created_at, id);
