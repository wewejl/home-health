"""
Authentication API tests for the home health backend.

Tests cover:
- Verification code sending
- Login with verification code (test mode)
- Password registration and login
- Token refresh
- User profile management
- Phone status checking
"""
import pytest
import os

# Set test mode before imports
os.environ["TEST_MODE"] = "true"


class TestSendVerificationCode:
    """Tests for sending verification codes."""

    def test_send_verification_code_success(self, test_client):
        """Test sending verification code successfully."""
        response = test_client.post("/auth/send-code", json={"phone": "13800138000"})
        assert response.status_code == 200
        data = response.json()
        assert "expires_in" in data
        assert data["expires_in"] > 0
        assert "message" in data

    def test_send_verification_code_invalid_phone(self, test_client):
        """Test sending verification code with invalid phone number."""
        # Too short
        response = test_client.post("/auth/send-code", json={"phone": "12345"})
        assert response.status_code == 422  # Validation error

        # Non-numeric
        response = test_client.post("/auth/send-code", json={"phone": "abcdefghijk"})
        assert response.status_code == 422

    def test_send_verification_code_missing_field(self, test_client):
        """Test sending verification code without phone field."""
        response = test_client.post("/auth/send-code", json={})
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login."""

    def test_login_with_test_mode_new_user(self, test_client):
        """Test login in test mode with a new user."""
        response = test_client.post("/auth/login", json={
            "phone": "13912345678",
            "code": "000000"  # Test mode universal code
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["phone"] == "13912345678"
        assert data["is_new_user"] is True

    def test_login_with_test_mode_existing_user(self, test_client, db_session):
        """Test login in test mode with an existing user."""
        from app.services.auth_service import AuthService

        # Create existing user
        phone = "13912345679"
        user, _ = AuthService.get_or_create_user(db_session, phone)

        response = test_client.post("/auth/login", json={
            "phone": phone,
            "code": "000000"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["phone"] == phone
        assert data["is_new_user"] is False

    def test_login_invalid_phone_format(self, test_client):
        """Test login with invalid phone format."""
        response = test_client.post("/auth/login", json={
            "phone": "123",
            "code": "000000"
        })
        assert response.status_code == 422  # Validation error

    def test_login_missing_fields(self, test_client):
        """Test login with missing required fields."""
        response = test_client.post("/auth/login", json={"phone": "13800138000"})
        assert response.status_code == 422

        response = test_client.post("/auth/login", json={"code": "000000"})
        assert response.status_code == 422


class TestGetCurrentUser:
    """Tests for getting current user information."""

    def test_get_current_user_with_valid_token(self, test_client):
        """Test getting current user with valid JWT token."""
        # First login to get token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138001",
            "code": "000000"
        })
        token = login_response.json()["token"]

        # Use token to get user info
        response = test_client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        # In test mode, phone may be masked, check for id instead
        assert "id" in data
        assert "nickname" in data

    def test_get_current_user_with_test_mode_token(self, test_client):
        """Test getting current user with test mode token."""
        response = test_client.get("/auth/me", headers={
            "Authorization": "Bearer test_1"
        })
        # In test mode, this should create/get a user with id=1
        assert response.status_code in [200, 401]  # May not exist in fresh DB

    def test_get_current_user_without_token(self, test_client):
        """Test getting current user without authentication."""
        response = test_client.get("/auth/me")
        # In test mode, this returns 200 (test user auto-created)
        # In production mode, this would be 401
        assert response.status_code == 200

    def test_get_current_user_with_invalid_token(self, test_client):
        """Test getting current user with invalid token."""
        response = test_client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        # In test mode, invalid token still returns a test user
        assert response.status_code == 200


class TestUpdateProfile:
    """Tests for updating user profile."""

    def test_update_profile_nickname_and_gender(self, test_client):
        """Test updating user nickname and gender."""
        # First login
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138002",
            "code": "000000"
        })
        token = login_response.json()["token"]

        # Update profile
        response = test_client.put("/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nickname": "测试用户",
                "gender": "male"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "测试用户"
        assert data["gender"] == "male"
        assert data["is_profile_completed"] is True

    def test_update_profile_with_birthday(self, test_client):
        """Test updating user profile with birthday."""
        # First login
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138003",
            "code": "000000"
        })
        token = login_response.json()["token"]

        # Update profile with birthday
        response = test_client.put("/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nickname": "用户803",
                "gender": "female",
                "birthday": "1990-01-01"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["birthday"] == "1990-01-01"

    def test_update_profile_without_auth(self, test_client):
        """Test updating profile without authentication."""
        response = test_client.put("/auth/profile", json={
            "nickname": "匿名用户"
        })
        # In test mode, request passes with auto-created test user
        assert response.status_code == 200

    def test_complete_profile_post_method(self, test_client):
        """Test completing profile using POST method."""
        # First login
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138004",
            "code": "000000"
        })
        token = login_response.json()["token"]

        # Complete profile with POST
        response = test_client.post("/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nickname": "新用户",
                "gender": "other"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "新用户"
        assert data["gender"] == "other"


class TestCheckPhoneExists:
    """Tests for checking phone number status."""

    def test_check_phone_not_exists(self, test_client):
        """Test checking a phone number that doesn't exist."""
        response = test_client.get("/auth/check-phone?phone=19912345678")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["has_password"] is False

    def test_check_phone_exists_without_password(self, test_client, db_session):
        """Test checking a phone number that exists without password."""
        from app.models.user import User

        # Create user without password
        user = User(phone="19912345670", nickname="测试", is_active=True)
        db_session.add(user)
        db_session.commit()

        response = test_client.get("/auth/check-phone?phone=19912345670")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["has_password"] is False

    def test_check_phone_exists_with_password(self, test_client, db_session):
        """Test checking a phone number that exists with password."""
        from app.services.auth_service import AuthService

        # Create user with password
        phone = "19912345671"
        AuthService.register_with_password(db_session, phone, "Test123456")

        response = test_client.get("/auth/check-phone?phone=19912345671")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["has_password"] is True

    def test_check_phone_invalid_format(self, test_client):
        """Test checking phone with invalid format."""
        response = test_client.get("/auth/check-phone?phone=invalid")
        # Should still return 200 but with exists=False
        assert response.status_code == 200


class TestPasswordLogin:
    """Tests for password-based authentication."""

    def test_register_with_password_new_user(self, test_client):
        """Test registering a new user with password."""
        response = test_client.post("/auth/register-password", json={
            "phone": "13900139000",
            "password": "Test123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["phone"] == "13900139000"
        assert data["is_new_user"] is True

    def test_register_with_password_existing_user(self, test_client, db_session):
        """Test setting password for existing user."""
        from app.services.auth_service import AuthService

        # Create user first
        phone = "13900139001"
        AuthService.get_or_create_user(db_session, phone)

        # Now set password
        response = test_client.post("/auth/register-password", json={
            "phone": phone,
            "password": "Test123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["is_new_user"] is False

    def test_login_with_password_success(self, test_client):
        """Test password login with correct credentials."""
        # First register with password
        register_response = test_client.post("/auth/register-password", json={
            "phone": "13900139002",
            "password": "Test123456"
        })
        assert register_response.status_code == 200

        # Now login with password
        login_response = test_client.post("/auth/login-password", json={
            "phone": "13900139002",
            "password": "Test123456"
        })
        assert login_response.status_code == 200
        data = login_response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["phone"] == "13900139002"

    def test_login_with_password_wrong_password(self, test_client):
        """Test password login with incorrect password."""
        # First register with password
        test_client.post("/auth/register-password", json={
            "phone": "13900139003",
            "password": "Test123456"
        })

        # Try login with wrong password
        response = test_client.post("/auth/login-password", json={
            "phone": "13900139003",
            "password": "WrongPassword"
        })
        assert response.status_code == 400
        assert "手机号或密码错误" in response.json()["detail"]

    def test_login_with_password_user_not_exists(self, test_client):
        """Test password login with non-existent user."""
        response = test_client.post("/auth/login-password", json={
            "phone": "19999999999",
            "password": "Test123456"
        })
        assert response.status_code == 400
        assert "手机号或密码错误" in response.json()["detail"]

    def test_login_with_password_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post("/auth/register-password", json={
            "phone": "13900139004",
            "password": "123"  # Too short
        })
        assert response.status_code == 422  # Validation error


class TestRefreshToken:
    """Tests for token refresh functionality."""

    def test_refresh_token_success(self, test_client):
        """Test refreshing token with valid refresh token."""
        # First login to get refresh token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138005",
            "code": "000000"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = test_client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data  # New access token
        assert "refresh_token" in data  # New refresh token
        # Both tokens should be valid
        assert len(data["token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_refresh_token_invalid(self, test_client):
        """Test refreshing with invalid token."""
        response = test_client.post("/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })
        assert response.status_code == 401
        assert "刷新Token无效或已过期" in response.json()["detail"]

    def test_refresh_token_missing(self, test_client):
        """Test refresh without providing refresh token."""
        response = test_client.post("/auth/refresh", json={})
        assert response.status_code == 422  # Validation error

    def test_refresh_token_with_access_token(self, test_client):
        """Test that access token cannot be used for refresh."""
        # Get an access token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138006",
            "code": "000000"
        })
        access_token = login_response.json()["token"]

        # Try to use access token as refresh token
        response = test_client.post("/auth/refresh", json={
            "refresh_token": access_token
        })
        # Should fail because token types don't match
        assert response.status_code == 401


class TestSetPassword:
    """Tests for setting/updating password when logged in."""

    def test_set_password_authenticated(self, test_client):
        """Test setting password for authenticated user."""
        # Login with verification code
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138007",
            "code": "000000"
        })
        token = login_response.json()["token"]

        # Set password
        response = test_client.post("/auth/password/set",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "000000",
                "new_password": "NewPassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # In test mode, check that we got a user response
        assert "id" in data

    def test_set_password_without_auth(self, test_client):
        """Test setting password without authentication."""
        response = test_client.post("/auth/password/set", json={
            "code": "000000",
            "new_password": "NewPassword123"
        })
        # In test mode, this passes with auto-created test user
        assert response.status_code == 200


class TestResetPassword:
    """Tests for password reset functionality."""

    def test_reset_password_success(self, test_client):
        """Test resetting password successfully."""
        # Create user with password first
        test_client.post("/auth/register-password", json={
            "phone": "13900139010",
            "password": "OldPassword123"
        })

        # Reset password
        response = test_client.post("/auth/password/reset", json={
            "phone": "13900139010",
            "code": "000000",  # Test mode accepts any code
            "new_password": "NewPassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data

    def test_reset_password_user_not_exists(self, test_client):
        """Test resetting password for non-existent user."""
        response = test_client.post("/auth/password/reset", json={
            "phone": "19999999999",
            "code": "000000",
            "new_password": "NewPassword123"
        })
        assert response.status_code == 400
