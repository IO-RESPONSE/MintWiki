"""문서 단위 읽기/편집/토론/이동/삭제 제한 정책 정의."""
from typing import Optional

from modules.acl.document_acl import DocumentAcl
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType

DOCUMENT_EDIT_RESTRICTION_RULE_ID = "document-edit-restricted"
DOCUMENT_READ_RESTRICTION_RULE_ID = "document-read-restricted"
DOCUMENT_DISCUSS_RESTRICTION_RULE_ID = "document-discuss-restricted"
DOCUMENT_MOVE_RESTRICTION_RULE_ID = "document-move-restricted"
DOCUMENT_DELETE_RESTRICTION_RULE_ID = "document-delete-restricted"


def restrict_document_edit(
    document_id: str,
    subject_type: SubjectType,
    subject_id: Optional[str] = None,
) -> DocumentAcl:
    """
    지정한 대상만 편집을 허용하도록 제한된 문서 ACL을 생성한다.

    문서 ACL에는 지정한 대상에 대한 편집 허용 규칙 하나만 등록된다. 다른
    대상은 이 문서 ACL 안에서 일치하는 규칙이 없으므로 AclService에 의해
    기본적으로 편집이 거부된다. 문서 ACL이 존재하면 네임스페이스 기본
    편집 정책(로그인 사용자 허용)보다 우선 적용되므로, 지정한 대상 외에는
    로그인 여부와 무관하게 편집이 거부된다.

    Args:
        document_id: 편집을 제한할 문서의 고유 식별자
        subject_type: 편집이 허용되는 대상의 종류
        subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)

    Returns:
        편집 허용 규칙 하나만 담긴 DocumentAcl
    """
    rule = Rule(
        id=DOCUMENT_EDIT_RESTRICTION_RULE_ID,
        subject_type=subject_type,
        permission=Permission.EDIT,
        effect=Effect.ALLOW,
        subject_id=subject_id,
    )
    return DocumentAcl(document_id=document_id, rules=[rule])


def restrict_document_read(
    document_id: str,
    subject_type: SubjectType,
    subject_id: Optional[str] = None,
) -> DocumentAcl:
    """
    지정한 대상만 읽기를 허용하도록 제한된 문서 ACL을 생성한다.

    문서 ACL에는 지정한 대상에 대한 읽기 허용 규칙 하나만 등록된다. 다른
    대상은 이 문서 ACL 안에서 일치하는 규칙이 없으므로 AclService에 의해
    기본적으로 읽기가 거부된다. 문서 ACL이 존재하면 네임스페이스 기본
    읽기 정책(전체 공개 허용)보다 우선 적용되므로, 지정한 대상 외에는
    익명 사용자를 포함해 누구든 읽기가 거부된다.

    Args:
        document_id: 읽기를 제한할 문서의 고유 식별자
        subject_type: 읽기가 허용되는 대상의 종류
        subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)

    Returns:
        읽기 허용 규칙 하나만 담긴 DocumentAcl
    """
    rule = Rule(
        id=DOCUMENT_READ_RESTRICTION_RULE_ID,
        subject_type=subject_type,
        permission=Permission.READ,
        effect=Effect.ALLOW,
        subject_id=subject_id,
    )
    return DocumentAcl(document_id=document_id, rules=[rule])


def restrict_document_discuss(
    document_id: str,
    subject_type: SubjectType,
    subject_id: Optional[str] = None,
) -> DocumentAcl:
    """
    지정한 대상만 토론을 허용하도록 제한된 문서 ACL을 생성한다.

    문서 ACL에는 지정한 대상에 대한 토론 허용 규칙 하나만 등록된다. 다른
    대상은 이 문서 ACL 안에서 일치하는 규칙이 없으므로 AclService에 의해
    기본적으로 토론이 거부된다. 기본 정책(default_policy)에는 토론에 대한
    규칙이 없어 문서 ACL이 없는 문서는 누구도 토론할 수 없으므로, 이
    함수는 특정 대상에게 토론 권한을 부여하는 유일한 수단이다.

    Args:
        document_id: 토론을 제한할 문서의 고유 식별자
        subject_type: 토론이 허용되는 대상의 종류
        subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)

    Returns:
        토론 허용 규칙 하나만 담긴 DocumentAcl
    """
    rule = Rule(
        id=DOCUMENT_DISCUSS_RESTRICTION_RULE_ID,
        subject_type=subject_type,
        permission=Permission.DISCUSS,
        effect=Effect.ALLOW,
        subject_id=subject_id,
    )
    return DocumentAcl(document_id=document_id, rules=[rule])


def restrict_document_move(
    document_id: str,
    subject_type: SubjectType,
    subject_id: Optional[str] = None,
) -> DocumentAcl:
    """
    지정한 대상만 이동을 허용하도록 제한된 문서 ACL을 생성한다.

    문서 ACL에는 지정한 대상에 대한 이동 허용 규칙 하나만 등록된다. 다른
    대상은 이 문서 ACL 안에서 일치하는 규칙이 없으므로 AclService에 의해
    기본적으로 이동이 거부된다. 기본 정책(default_policy)에는 이동에 대한
    규칙이 없어 문서 ACL이 없는 문서는 누구도 이동할 수 없으므로, 이
    함수는 특정 대상에게 이동 권한을 부여하는 유일한 수단이다.

    Args:
        document_id: 이동을 제한할 문서의 고유 식별자
        subject_type: 이동이 허용되는 대상의 종류
        subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)

    Returns:
        이동 허용 규칙 하나만 담긴 DocumentAcl
    """
    rule = Rule(
        id=DOCUMENT_MOVE_RESTRICTION_RULE_ID,
        subject_type=subject_type,
        permission=Permission.MOVE,
        effect=Effect.ALLOW,
        subject_id=subject_id,
    )
    return DocumentAcl(document_id=document_id, rules=[rule])


def restrict_document_delete(
    document_id: str,
    subject_type: SubjectType,
    subject_id: Optional[str] = None,
) -> DocumentAcl:
    """
    지정한 대상만 삭제를 허용하도록 제한된 문서 ACL을 생성한다.

    문서 ACL에는 지정한 대상에 대한 삭제 허용 규칙 하나만 등록된다. 다른
    대상은 이 문서 ACL 안에서 일치하는 규칙이 없으므로 AclService에 의해
    기본적으로 삭제가 거부된다. 기본 정책(default_policy)에는 삭제에 대한
    규칙이 없어 문서 ACL이 없는 문서는 누구도 삭제할 수 없으므로, 이
    함수는 특정 대상에게 삭제 권한을 부여하는 유일한 수단이다.

    Args:
        document_id: 삭제를 제한할 문서의 고유 식별자
        subject_type: 삭제가 허용되는 대상의 종류
        subject_id: 대상이 사용자 또는 그룹일 때의 id (선택사항)

    Returns:
        삭제 허용 규칙 하나만 담긴 DocumentAcl
    """
    rule = Rule(
        id=DOCUMENT_DELETE_RESTRICTION_RULE_ID,
        subject_type=subject_type,
        permission=Permission.DELETE,
        effect=Effect.ALLOW,
        subject_id=subject_id,
    )
    return DocumentAcl(document_id=document_id, rules=[rule])
