-- acl_namespace_rule: 네임스페이스 기본값 범위 ACL 규칙 테이블.
-- 스펙 원출처: src/modules/acl/rule.py의 Rule,
-- src/modules/acl/namespace_defaults.py의 NamespaceAclDefaults,
-- docs/acl-portable-repository-plan.md §4.
--
-- acl_rule.sql(0465)과 분리하는 이유: NamespaceAclDefaults는
-- DocumentAcl과 다른 도메인 클래스이고, 키 컬럼의 성격도 다르다 —
-- document_id는 FK 필수, namespace는 FK 대상 테이블이 없는 자유
-- 문자열이다. acl-portable-repository-plan.md §4가 한 테이블에 두 키
-- 컬럼을 모두 두고 "정확히 하나만 채운다"를 CHECK 제약/애플리케이션
-- 검증으로 강제하는 대신, 테이블을 나눠 그 상태 자체가 존재할 수 없게
-- 하기로 확정했다.
--
-- namespace (FK 없음): NamespaceAclDefaults가 document_id 대신 문자열
-- namespace(예: DEFAULT_NAMESPACE = "*")를 키로 규칙 목록을 묶는다.
-- namespace는 별도 테이블이 없어 참조 무결성 검증 대상이 아니다 —
-- 등록되지 않은 네임스페이스는 빈 목록으로 처리된다(ACL README,
-- default_policy.py).
--
-- subject_type/subject_id/permission/effect/expires_at/sort_order:
-- acl_rule.sql(0465)과 동일한 근거를 그대로 따른다(같은 Rule 도메인
-- 모델, 같은 우선순위 재현 방식).
--
-- UNIQUE(namespace, sort_order): acl_rule의 UNIQUE(document_id,
-- sort_order)와 동일한 이유 — 같은 네임스페이스 안에서 두 규칙이 같은
-- 순번을 가질 수 없게 하고, "namespace의 규칙을 sort_order 오름차순으로
-- 전부 가져오기" 조회에 그대로 쓰인다.
--
-- PostgreSQL/MariaDB 차이 (주석으로 분리):
-- - id / subject_id: [Portable ID Column Policy]에 따라 애플리케이션이
--   생성한 UUID 문자열(VARCHAR(255))만 저장한다. 두 DB 모두
--   SERIAL/AUTO_INCREMENT/UUID() 생성 함수를 쓰지 않으므로 DDL이
--   동일하다.
-- - expires_at: [Portable Timestamp Column Policy]에 따라 애플리케이션이
--   UTC로 정규화한 값을 INSERT 이전에 채워 넣는다. PostgreSQL TIMESTAMP와
--   MariaDB TIMESTAMP 모두 그 값을 그대로 저장하며, MariaDB가 지원하지
--   않는 WITH TIME ZONE은 쓰지 않는다(acl_rule.sql과 동일 판단).
-- - namespace / subject_type / permission / effect: [Portable Text
--   Collation Policy]에 따라 고정된 값만 저장해 대소문자 비교 이슈가
--   없다 — 컬럼 정의에 별도 COLLATE 지정이 필요 없다.
CREATE TABLE acl_namespace_rule (
    id VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    subject_type VARCHAR(20) NOT NULL,
    subject_id VARCHAR(255) NULL,
    permission VARCHAR(20) NOT NULL,
    effect VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NULL,
    sort_order INTEGER NOT NULL,
    CONSTRAINT pk_acl_namespace_rule PRIMARY KEY (id),
    CONSTRAINT uq_acl_namespace_rule_namespace_sort_order UNIQUE (namespace, sort_order)
);
