"""ACL module package."""
from modules.acl.decision import Decision
from modules.acl.default_policy import (
    LOGGED_IN_EDIT_RULE_ID,
    PUBLIC_READ_RULE_ID,
    build_default_namespace_acl_defaults,
    default_rules,
)
from modules.acl.document_acl import DocumentAcl, EmptyDocumentIdError
from modules.acl.document_policy import (
    DOCUMENT_DISCUSS_RESTRICTION_RULE_ID,
    DOCUMENT_EDIT_RESTRICTION_RULE_ID,
    DOCUMENT_READ_RESTRICTION_RULE_ID,
    restrict_document_discuss,
    restrict_document_edit,
    restrict_document_read,
)
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import (
    Effect,
    EmptyRuleIdError,
    MissingSubjectIdError,
    Rule,
    SubjectType,
)
from modules.acl.service import AclService

__all__ = [
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
]
