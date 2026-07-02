-- audit_event: acl/discussion 등 여러 모듈의 감사 이벤트를 한데 모으는
-- append-only 테이블.
-- 스펙 원출처: src/modules/acl/audit_event.py의 AclAuditEvent,
-- src/modules/discussion/audit_event.py의 DiscussionAuditEvent,
-- docs/audit-portable-repository-plan.md §3.
--
-- 테이블 이름: acl_audit_event/discussion_audit_event처럼 모듈 접두어로
-- 나누지 않고 audit 모듈이 소유하는 단일 audit_event 테이블로 통합한다
-- (audit-portable-repository-plan.md §2). 감사 로그의 소유자는 acl/
-- discussion이 아니라 audit 모듈이라는 modules.md의 아키텍처 목표를
-- 그대로 따른 결정이고, 카테고리가 늘어도(§목적) 테이블을 새로 만들
-- 필요가 없다.
--
-- category: 이벤트가 어느 소스에서 왔는지 구분하는 판별 컬럼. 지금은
-- "acl"/"discussion" 두 값만 실재하며, 앞으로 추가될 document/admin/
-- auth/job 카테고리를 위한 여지를 남겨 둔다(audit-portable-repository-plan.md §3).
--
-- action: AclAuditAction(rule_added/rule_removed)과
-- DiscussionAuditAction(thread_created/thread_closed/thread_reopened/
-- thread_paused/comment_added/comment_hidden) enum 값을 문자열로 저장한다.
-- category가 이미 네임스페이스를 분리하므로 같은 컬럼을 공유해도 값
-- 충돌은 없다.
--
-- entity_id (다형 참조, FK 없음): category="acl"일 때 AclAuditEvent.rule_id,
-- category="discussion"일 때 DiscussionAuditEvent.thread_id를 담는 필수
-- 참조다. 컬럼 하나가 카테고리에 따라 다른 테이블(acl_rule/
-- discussion_thread)을 가리키는 다형 참조라 acl_rule.subject_id와 동일한
-- 근거로 FK를 걸지 않는다(audit-portable-repository-plan.md §4).
--
-- related_entity_id (다형 참조, FK 없음): category="acl"일 때
-- AclAuditEvent.document_id, category="discussion"일 때
-- DiscussionAuditEvent.comment_id를 담는 선택 참조다. entity_id와 동일한
-- 이유로 FK를 걸지 않는다. 감사 로그는 참조 대상 행이 나중에 삭제되더라도
-- "무슨 일이 있었는지"의 기록 자체는 남아야 하므로, FK의 ON DELETE 정책을
-- 강제로 정할 필요가 없다는 점도 근거다(audit-portable-repository-plan.md §4).
--
-- actor_id (FK 없음): revision.author_id와 동일한 근거 — account 테이블이
-- 아직 없어 지금은 FK를 걸 대상이 없다.
--
-- updated_at을 두지 않는다: 감사 이벤트는 생성된 뒤 내용이 바뀔 이유가
-- 없다. ANSI SQL만으로 UPDATE/DELETE 자체를 금지할 수는 없지만
-- (audit-portable-repository-plan.md §5), 스키마에 update 경로가 필요할
-- 컬럼을 아예 두지 않는 것으로 append-only 의도를 표현한다.
--
-- 인덱스: audit-portable-repository-plan.md §7이 확인한 대로 지금은 확립된
-- 조회 패턴이 없다 — AclAuditRecorder.events()/
-- DiscussionAuditRecorder.events()는 필터 없이 전체를 반환할 뿐이다.
-- category/entity_id 기준 인덱스는 후보로만 남겨 두고, 실제 저장소
-- 인터페이스가 정해지는 이후 태스크에서 다시 판단한다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / entity_id / related_entity_id / actor_id: [Portable ID Column
--   Policy]에 따라 애플리케이션이 생성한 UUID 문자열(VARCHAR(255))만
--   저장한다. 두 DB 모두 SERIAL/AUTO_INCREMENT/UUID() 생성 함수를 쓰지
--   않으므로 DDL이 동일하다.
-- - occurred_at: [Portable Timestamp Column Policy]에 따라 애플리케이션이
--   UTC로 정규화한 값을 INSERT 이전에 채워 넣는다. PostgreSQL TIMESTAMP와
--   MariaDB TIMESTAMP 모두 그 값을 그대로 저장하며, MariaDB가 지원하지
--   않는 WITH TIME ZONE은 쓰지 않는다(다른 schema 파일과 동일 판단).
-- - category / action: [Portable Text Collation Policy]에 따라 고정된
--   소문자 문자열만 저장해 대소문자 비교 이슈가 없다 — 컬럼 정의에 별도
--   COLLATE 지정이 필요 없다(acl_rule.subject_type과 동일 근거).
CREATE TABLE audit_event (
    id VARCHAR(255) NOT NULL,
    category VARCHAR(20) NOT NULL,
    action VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    related_entity_id VARCHAR(255) NULL,
    actor_id VARCHAR(255) NULL,
    occurred_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_audit_event PRIMARY KEY (id)
);
