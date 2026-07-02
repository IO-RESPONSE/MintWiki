-- acl_rule: 문서 범위 ACL 규칙 테이블.
-- 스펙 원출처: src/modules/acl/rule.py의 Rule,
-- src/modules/acl/document_acl.py의 DocumentAcl,
-- docs/acl-portable-repository-plan.md §3.
--
-- 테이블 이름: Rule 도메인 모델은 문서 범위(DocumentAcl)와 네임스페이스
-- 기본값 범위(NamespaceAclDefaults) 두 컨텍스트에 쓰인다 —
-- acl-portable-repository-plan.md §2가 이 구분을 이름 공간 충돌 없이
-- 남기기 위해 `rule` 단독 대신 모듈 접두어를 붙인 `acl_rule`(이 파일,
-- 문서 범위)과 `acl_namespace_rule.sql`(0465, 네임스페이스 기본값 범위)로
-- 나누기로 확정했다 — 이 파일이 그중 문서 범위를 옮긴다.
--
-- document_id (FK): DocumentAcl이 document_id 하나에 규칙을 순서 있는
-- 리스트로 묶는다. document.sql(0461)이 만든 document 테이블을 참조한다.
--
-- subject_type/permission/effect: Rule.__init__이 받는 SubjectType/
-- Permission/Effect enum 값을 고정된 소문자 문자열로 저장한다 —
-- account.sql(0463)의 id 컬럼과 동일한 근거로 애플리케이션이 고정된
-- 값만 쓰므로 대소문자 비교 이슈가 없다([Portable Text Collation
-- Policy §2/§3]).
--
-- subject_id (다형 참조, FK 없음): Rule.__init__은 subject_type이
-- USER/GROUP일 때만 subject_id를 필수로 요구한다(MissingSubjectIdError).
-- USER일 때는 미래 account.id, GROUP일 때는 미래 user_group.id를
-- 가리키지만, 컬럼 하나가 두 참조 대상 중 하나로 갈리는 다형 참조라
-- document.current_revision_id와 동일한 이유로 FK 제약을 걸지 않고
-- 서비스 계층 검증에 맡긴다([Persistence Boundaries]).
--
-- sort_order (규칙 우선순위 재현): AclService.check()는 등록 순서대로
-- 스캔해 첫 매칭 규칙이 승리하는 first-match-wins 방식이다. SQL 테이블은
-- ORDER BY 없이 행 반환 순서를 보장하지 않으므로, created_at 같은
-- 타임스탬프가 아니라 전용 정수 컬럼으로 순서를 저장한다 —
-- acl-portable-repository-plan.md §5가 확정한 대로, 같은 트랜잭션 안에서
-- 여러 규칙이 연속으로 추가될 수 있어 타임스탬프 해상도로는 순서를
-- 구분하지 못할 수 있기 때문이다. 값은 애플리케이션이 "해당 document_id의
-- 가장 큰 sort_order + 1"로 채운다.
--
-- UNIQUE(document_id, sort_order): 같은 문서 안에서 두 규칙이 같은
-- 순번을 가질 수 없게 해 "이 문서의 규칙 순서"가 항상 하나로 결정되게
-- 한다. 정렬 키(sort_order)가 포함된 인덱스이므로 "document_id의 규칙을
-- sort_order 오름차순으로 전부 가져오기" 조회에도 그대로 쓰인다 —
-- 별도 인덱스를 중복으로 두지 않는다(acl-portable-repository-plan.md §5).
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / document_id / subject_id: [Portable ID Column Policy]에 따라
--   애플리케이션이 생성한 UUID 문자열(VARCHAR(255))만 저장한다. 두 DB
--   모두 SERIAL/AUTO_INCREMENT/UUID() 생성 함수를 쓰지 않으므로 DDL이
--   동일하다.
-- - expires_at: [Portable Timestamp Column Policy]에 따라 애플리케이션이
--   UTC로 정규화한 값을 INSERT 이전에 채워 넣는다(값이 없으면 영구
--   규칙). PostgreSQL TIMESTAMP와 MariaDB TIMESTAMP 모두 그 값을 그대로
--   저장하며, MariaDB가 지원하지 않는 WITH TIME ZONE은 쓰지 않는다
--   (document.sql/revision.sql/user_session.sql과 동일 판단).
-- - subject_type / permission / effect: [Portable Text Collation
--   Policy]에 따라 고정된 소문자 enum 문자열만 저장해 대소문자 비교
--   이슈가 없다 — 컬럼 정의에 별도 COLLATE 지정이 필요 없다.
CREATE TABLE acl_rule (
    id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    subject_type VARCHAR(20) NOT NULL,
    subject_id VARCHAR(255) NULL,
    permission VARCHAR(20) NOT NULL,
    effect VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NULL,
    sort_order INTEGER NOT NULL,
    CONSTRAINT pk_acl_rule PRIMARY KEY (id),
    CONSTRAINT fk_acl_rule_document_id FOREIGN KEY (document_id) REFERENCES document (id),
    CONSTRAINT uq_acl_rule_document_id_sort_order UNIQUE (document_id, sort_order)
);
