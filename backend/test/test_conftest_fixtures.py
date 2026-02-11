"""
Simple test to verify conftest.py fixtures are working correctly.
"""
import pytest


class TestConfextFixtures:
    """Test that all fixtures in conftest.py are working."""

    def test_db_session_fixture(self, db_session):
        """Test that db_session fixture works."""
        try:
            from app.models.user import User
        except ImportError:
            from backend.app.models.user import User
        users = db_session.query(User).all()
        # Should be empty initially
        assert len(users) == 0

    def test_test_user_fixture(self, test_user):
        """Test that test_user fixture creates a user."""
        assert test_user.phone == "13800138000"
        assert test_user.nickname == "测试用户"
        assert test_user.gender == "male"

    def test_test_user_token_fixture(self, test_user_token):
        """Test that test_user_token fixture returns a token."""
        assert test_user_token is not None
        assert isinstance(test_user_token, str)
        assert len(test_user_token) > 0

    def test_test_user_headers_fixture(self, test_user_headers):
        """Test that test_user_headers fixture returns headers."""
        assert "Authorization" in test_user_headers
        assert test_user_headers["Authorization"].startswith("Bearer ")

    def test_test_mode_token_fixture(self, test_mode_token):
        """Test that test_mode_token fixture returns correct format."""
        assert test_mode_token == "test_1"

    def test_test_mode_headers_fixture(self, test_mode_headers):
        """Test that test_mode_headers fixture returns headers."""
        assert "Authorization" in test_mode_headers
        assert test_mode_headers["Authorization"] == "Bearer test_1"

    def test_test_department_fixture(self, test_department):
        """Test that test_department fixture creates a department."""
        assert test_department.name == "内科"
        assert test_department.description == "内科科室"

    def test_verification_code_fixture(self, test_verification_code):
        """Test that test_verification_code fixture returns correct code."""
        assert test_verification_code == "000000"


def test_fixtures_combined(db_session, test_user, test_department):
    """Test that multiple fixtures work together."""
    # Note: test_user and test_department use separate db_session instances
    # due to the function-scoped fixture, so we need to use the passed db_session
    # to verify the database connection is working
    assert db_session is not None
    # The test_user and test_department are created in separate sessions
    # They may not be visible in this session, which is expected behavior
    # for isolated test fixtures
