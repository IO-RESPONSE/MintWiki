"""acl 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.acl
from modules.acl.rule import Rule


def test_acl_package_is_importable():
    assert modules.acl.__doc__ == "ACL module package."


def test_acl_package_exports_permission():
    # 0152에서 Permission 열거형이 추가되었으므로 export에 포함되어야 한다.
    assert "Permission" in modules.acl.__all__


def test_acl_package_exports_rule():
    # 0153에서 Rule 모델이 추가되었으므로 export에 포함되어야 한다.
    assert modules.acl.__all__ == [
        "Permission",
        "Rule",
        "SubjectType",
        "Effect",
        "EmptyRuleIdError",
        "MissingSubjectIdError",
        "NamespaceAclDefaults",
        "DEFAULT_NAMESPACE",
        "DocumentAcl",
        "EmptyDocumentIdError",
        "Decision",
        "AclService",
        "PUBLIC_READ_RULE_ID",
        "default_rules",
        "build_default_namespace_acl_defaults",
        "LOGGED_IN_EDIT_RULE_ID",
        "DOCUMENT_EDIT_RESTRICTION_RULE_ID",
        "restrict_document_edit",
        "DOCUMENT_READ_RESTRICTION_RULE_ID",
        "restrict_document_read",
        "DOCUMENT_DISCUSS_RESTRICTION_RULE_ID",
        "restrict_document_discuss",
        "DOCUMENT_MOVE_RESTRICTION_RULE_ID",
        "restrict_document_move",
        "DOCUMENT_DELETE_RESTRICTION_RULE_ID",
        "restrict_document_delete",
        "DOCUMENT_ADMIN_RESTRICTION_RULE_ID",
        "restrict_document_admin",
        "AclAuditAction",
        "AclAuditEvent",
        "EmptyAclAuditEventIdError",
        "MissingRuleIdError",
        "AclAuditRecorder",
    ]
    assert modules.acl.Rule is Rule


def test_acl_package_exports_namespace_defaults():
    # 0154에서 NamespaceAclDefaults가 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.namespace_defaults import NamespaceAclDefaults

    assert "NamespaceAclDefaults" in modules.acl.__all__
    assert modules.acl.NamespaceAclDefaults is NamespaceAclDefaults


def test_acl_package_exports_document_acl():
    # 0155에서 DocumentAcl 모델이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_acl import DocumentAcl, EmptyDocumentIdError

    assert "DocumentAcl" in modules.acl.__all__
    assert "EmptyDocumentIdError" in modules.acl.__all__
    assert modules.acl.DocumentAcl is DocumentAcl
    assert modules.acl.EmptyDocumentIdError is EmptyDocumentIdError


def test_acl_package_exports_decision():
    # 0156에서 Decision 모델이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.decision import Decision

    assert "Decision" in modules.acl.__all__
    assert modules.acl.Decision is Decision


def test_acl_package_exports_acl_service():
    # 0157에서 AclService 골격이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.service import AclService

    assert "AclService" in modules.acl.__all__
    assert modules.acl.AclService is AclService


def test_acl_package_exports_default_policy():
    # 0158에서 공개 읽기 허용 기본 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.default_policy import (
        PUBLIC_READ_RULE_ID,
        build_default_namespace_acl_defaults,
        default_rules,
    )

    assert "PUBLIC_READ_RULE_ID" in modules.acl.__all__
    assert "default_rules" in modules.acl.__all__
    assert "build_default_namespace_acl_defaults" in modules.acl.__all__
    assert modules.acl.PUBLIC_READ_RULE_ID is PUBLIC_READ_RULE_ID
    assert modules.acl.default_rules is default_rules
    assert (
        modules.acl.build_default_namespace_acl_defaults
        is build_default_namespace_acl_defaults
    )


def test_acl_package_exports_logged_in_edit_rule_id():
    # 0159에서 로그인 편집 허용 기본 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.default_policy import LOGGED_IN_EDIT_RULE_ID

    assert "LOGGED_IN_EDIT_RULE_ID" in modules.acl.__all__
    assert modules.acl.LOGGED_IN_EDIT_RULE_ID is LOGGED_IN_EDIT_RULE_ID


def test_acl_package_exports_document_edit_restriction():
    # 0161에서 문서 단위 편집 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_EDIT_RESTRICTION_RULE_ID,
        restrict_document_edit,
    )

    assert "DOCUMENT_EDIT_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_edit" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_EDIT_RESTRICTION_RULE_ID
        is DOCUMENT_EDIT_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_edit is restrict_document_edit


def test_acl_package_exports_document_read_restriction():
    # 0162에서 문서 단위 읽기 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_READ_RESTRICTION_RULE_ID,
        restrict_document_read,
    )

    assert "DOCUMENT_READ_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_read" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_READ_RESTRICTION_RULE_ID
        is DOCUMENT_READ_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_read is restrict_document_read


def test_acl_package_exports_document_discuss_restriction():
    # 0163에서 문서 단위 토론 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_DISCUSS_RESTRICTION_RULE_ID,
        restrict_document_discuss,
    )

    assert "DOCUMENT_DISCUSS_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_discuss" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_DISCUSS_RESTRICTION_RULE_ID
        is DOCUMENT_DISCUSS_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_discuss is restrict_document_discuss


def test_acl_package_exports_document_move_restriction():
    # 0164에서 문서 단위 이동 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_MOVE_RESTRICTION_RULE_ID,
        restrict_document_move,
    )

    assert "DOCUMENT_MOVE_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_move" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_MOVE_RESTRICTION_RULE_ID
        is DOCUMENT_MOVE_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_move is restrict_document_move


def test_acl_package_exports_document_delete_restriction():
    # 0165에서 문서 단위 삭제 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_DELETE_RESTRICTION_RULE_ID,
        restrict_document_delete,
    )

    assert "DOCUMENT_DELETE_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_delete" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_DELETE_RESTRICTION_RULE_ID
        is DOCUMENT_DELETE_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_delete is restrict_document_delete


def test_acl_package_exports_document_admin_restriction():
    # 0166에서 문서 단위 관리자 권한 제한 정책이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.document_policy import (
        DOCUMENT_ADMIN_RESTRICTION_RULE_ID,
        restrict_document_admin,
    )

    assert "DOCUMENT_ADMIN_RESTRICTION_RULE_ID" in modules.acl.__all__
    assert "restrict_document_admin" in modules.acl.__all__
    assert (
        modules.acl.DOCUMENT_ADMIN_RESTRICTION_RULE_ID
        is DOCUMENT_ADMIN_RESTRICTION_RULE_ID
    )
    assert modules.acl.restrict_document_admin is restrict_document_admin


def test_acl_package_exports_audit_event():
    # 0171에서 AclAuditEvent 모델이 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.audit_event import (
        AclAuditAction,
        AclAuditEvent,
        EmptyAclAuditEventIdError,
        MissingRuleIdError,
    )

    assert "AclAuditAction" in modules.acl.__all__
    assert "AclAuditEvent" in modules.acl.__all__
    assert "EmptyAclAuditEventIdError" in modules.acl.__all__
    assert "MissingRuleIdError" in modules.acl.__all__
    assert modules.acl.AclAuditAction is AclAuditAction
    assert modules.acl.AclAuditEvent is AclAuditEvent
    assert modules.acl.EmptyAclAuditEventIdError is EmptyAclAuditEventIdError
    assert modules.acl.MissingRuleIdError is MissingRuleIdError


def test_acl_package_exports_audit_recorder():
    # 0172에서 AclAuditRecorder 서비스가 추가되었으므로 export에 포함되어야 한다.
    from modules.acl.audit_recorder import AclAuditRecorder

    assert "AclAuditRecorder" in modules.acl.__all__
    assert modules.acl.AclAuditRecorder is AclAuditRecorder
