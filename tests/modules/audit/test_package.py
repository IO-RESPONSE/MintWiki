"""audit 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.audit


def test_audit_package_is_importable():
    """audit 패키지를 import할 수 있다."""
    assert modules.audit.__doc__ == "Audit module package."


def test_audit_package_exports():
    """__all__에 선언된 이름이 실제 모듈 속성으로 존재한다."""
    assert modules.audit.__all__ == [
        "AuditEvent",
        "DuplicateAuditEventIdError",
        "EmptyAuditEventIdError",
        "MissingEventTypeError",
        "MissingActionError",
        "MissingResourceIdError",
        "AuditRepository",
        "InMemoryAuditRepository",
    ]
    for name in modules.audit.__all__:
        assert hasattr(modules.audit, name)
