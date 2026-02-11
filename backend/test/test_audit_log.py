"""
审计日志测试
"""
import pytest
try:
    from app.models.admin_user import AuditLog
    from app.routes.admin_auth import create_audit_log, validate_password_complexity
except ImportError:
    from backend.app.models.admin_user import AuditLog
    from backend.app.routes.admin_auth import create_audit_log, validate_password_complexity


class TestAuditLog:
    """审计日志测试"""

    def test_create_audit_log_basic(self, db_session):
        """测试创建基础审计日志"""
        create_audit_log(
            db=db_session,
            admin_user_id=1,
            action="test_action",
            resource_type="test_resource",
            resource_id="123",
            changes={"field": "value"},
            ip_address="127.0.0.1"
        )

        log = db_session.query(AuditLog).filter(AuditLog.action == "test_action").first()
        assert log is not None
        assert log.admin_user_id == 1
        assert log.resource_type == "test_resource"
        assert log.resource_id == "123"
        assert log.changes == {"field": "value"}
        assert log.ip_address == "127.0.0.1"

    def test_create_audit_log_minimal(self, db_session):
        """测试创建最小审计日志"""
        create_audit_log(
            db=db_session,
            admin_user_id=1,
            action="minimal_action"
        )

        log = db_session.query(AuditLog).filter(AuditLog.action == "minimal_action").first()
        assert log is not None
        assert log.admin_user_id == 1
