import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.auth import (
    SendCodeRequest, SendCodeResponse,
    LoginRequest, LoginResponse, 
    UserResponse, ProfileUpdateRequest,
    RefreshTokenRequest, RefreshTokenResponse,
    PasswordRegisterRequest, PasswordLoginRequest,
    SetPasswordRequest, PasswordResetRequest, CheckPhoneResponse
)
from ..services.auth_service import AuthService
from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@router.post("/send-code", response_model=SendCodeResponse)
async def send_verification_code(
    request_body: SendCodeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    发送验证码
    
    - **phone**: 11位手机号
    
    返回验证码有效期（秒）
    
    防刷策略：
    - 同一手机号60秒内只能发送一次
    - 同一手机号每小时最多10次
    - 同一IP每小时最多30次
    """
    client_ip = get_client_ip(request)
    
    success, message, expires_in = await AuthService.send_verification_code(
        request_body.phone, 
        client_ip
    )
    
    if not success:
        AuthService.log_auth_event("send_code_failed", extra={
            "phone": request_body.phone[-4:],
            "ip": client_ip,
            "error": message
        })
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
    
    AuthService.log_auth_event("send_code_success", extra={
        "phone": request_body.phone[-4:],
        "ip": client_ip
    })
    
    return SendCodeResponse(message=message, expires_in=expires_in)


@router.post("/login", response_model=LoginResponse)
def login(
    request_body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    验证码登录
    
    - **phone**: 11位手机号
    - **code**: 验证码（测试模式下 000000 始终有效）
    
    返回 JWT Token 和用户信息，is_new_user 表示是否为新注册用户
    """
    client_ip = get_client_ip(request)
    
    # 验证验证码
    success, error_msg = AuthService.verify_code(request_body.phone, request_body.code)
    if not success:
        AuthService.log_auth_event("login_failed", extra={
            "phone": request_body.phone[-4:],
            "ip": client_ip,
            "error": error_msg
        })
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # 获取或创建用户
    user, is_new_user = AuthService.get_or_create_user(db, request_body.phone)
    
    # 创建Token
    access_token, refresh_token = AuthService.create_tokens(user.id)
    
    AuthService.log_auth_event(
        "register_success" if is_new_user else "login_success",
        user_id=user.id,
        extra={"phone": request_body.phone[-4:], "ip": client_ip}
    )

    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(request_body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    刷新 Token
    
    使用 refresh_token 获取新的 access_token 和 refresh_token
    """
    result = AuthService.refresh_tokens(request_body.refresh_token)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新Token无效或已过期"
        )
    
    new_access_token, new_refresh_token = result
    
    return RefreshTokenResponse(
        token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    需要 Bearer Token 认证
    """
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    request_body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户资料
    
    - **nickname**: 昵称（最长50字）
    - **avatar_url**: 头像URL
    - **gender**: 性别 (male/female/other)
    - **birthday**: 生日 (YYYY-MM-DD)
    - **emergency_contact_name**: 紧急联系人姓名
    - **emergency_contact_phone**: 紧急联系人电话
    - **emergency_contact_relation**: 与紧急联系人关系
    
    当 nickname 和 gender 都填写后，is_profile_completed 会自动设为 true
    """
    profile_data = request_body.model_dump(exclude_unset=True)
    
    updated_user = AuthService.update_user_profile(db, current_user, profile_data)
    
    AuthService.log_auth_event("profile_updated", user_id=current_user.id)
    
    return UserResponse.model_validate(updated_user)


@router.post("/profile", response_model=UserResponse)
def complete_profile(
    request_body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    完善用户资料（首次注册后）
    
    与 PUT /profile 功能相同，提供 POST 方法便于客户端调用
    """
    profile_data = request_body.model_dump(exclude_unset=True)
    
    updated_user = AuthService.update_user_profile(db, current_user, profile_data)
    
    AuthService.log_auth_event("profile_completed", user_id=current_user.id)
    
    return UserResponse.model_validate(updated_user)


# ===== 密码认证相关接口 =====

@router.get("/check-phone", response_model=CheckPhoneResponse)
def check_phone(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    检查手机号状态
    
    - **phone**: 11位手机号
    
    返回用户是否存在以及是否设置了密码
    """
    exists, has_password = AuthService.check_phone_status(db, phone)
    return CheckPhoneResponse(exists=exists, has_password=has_password)


@router.post("/register-password", response_model=LoginResponse)
def register_with_password(
    request_body: PasswordRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    密码注册/设置密码
    
    - **phone**: 11位手机号
    - **code**: 验证码
    - **password**: 密码（6-32位）
    
    新用户注册或老用户设置密码，返回 JWT Token 和用户信息
    """
    client_ip = get_client_ip(request)
    
    # 验证验证码（若提供）
    if request_body.code:
        success, error_msg = AuthService.verify_code(request_body.phone, request_body.code)
        if not success:
            AuthService.log_auth_event("register_password_failed", extra={
                "phone": request_body.phone[-4:],
                "ip": client_ip,
                "error": "验证码错误"
            })
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    # 注册或设置密码
    user, is_new_user = AuthService.register_with_password(
        db, 
        request_body.phone, 
        request_body.password
    )
    
    # 创建Token
    access_token, refresh_token = AuthService.create_tokens(user.id)
    
    AuthService.log_auth_event(
        "register_password_success" if is_new_user else "set_password_success",
        user_id=user.id,
        extra={"phone": request_body.phone[-4:], "ip": client_ip}
    )
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user
    )


@router.post("/login-password", response_model=LoginResponse)
def login_with_password(
    request_body: PasswordLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    密码登录
    
    - **phone**: 11位手机号
    - **password**: 密码
    
    返回 JWT Token 和用户信息
    """
    client_ip = get_client_ip(request)
    
    # 密码登录
    user, error_msg = AuthService.login_with_password(
        db,
        request_body.phone,
        request_body.password
    )
    
    if not user:
        AuthService.log_auth_event("login_password_failed", extra={
            "phone": request_body.phone[-4:],
            "ip": client_ip,
            "error": error_msg
        })
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    # 创建Token
    access_token, refresh_token = AuthService.create_tokens(user.id)
    
    AuthService.log_auth_event("login_password_success", user_id=user.id, extra={
        "phone": request_body.phone[-4:],
        "ip": client_ip
    })
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=False
    )


@router.post("/password/set", response_model=UserResponse)
def set_password(
    request_body: SetPasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    设置/更新密码（已登录用户）
    
    - **code**: 验证码
    - **new_password**: 新密码（6-32位）
    
    需要 Bearer Token 认证
    """
    client_ip = get_client_ip(request)
    
    # 验证验证码
    success, error_msg = AuthService.verify_code(current_user.phone, request_body.code)
    if not success:
        AuthService.log_auth_event("set_password_failed", user_id=current_user.id, extra={
            "ip": client_ip,
            "error": "验证码错误"
        })
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    # 设置密码
    success = AuthService.set_user_password(db, current_user, request_body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码设置失败，请重试"
        )
    
    AuthService.log_auth_event("set_password_success", user_id=current_user.id, extra={
        "ip": client_ip
    })
    
    return UserResponse.model_validate(current_user)


@router.post("/password/reset", response_model=LoginResponse)
def reset_password(
    request_body: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    重置密码
    
    - **phone**: 11位手机号
    - **code**: 验证码
    - **new_password**: 新密码（6-32位）
    
    返回 JWT Token 和用户信息，可直接登录
    """
    client_ip = get_client_ip(request)
    
    # 验证验证码
    success, error_msg = AuthService.verify_code(request_body.phone, request_body.code)
    if not success:
        AuthService.log_auth_event("reset_password_failed", extra={
            "phone": request_body.phone[-4:],
            "ip": client_ip,
            "error": "验证码错误"
        })
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    # 重置密码
    success, error_msg = AuthService.reset_password(
        db,
        request_body.phone,
        request_body.new_password
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    
    # 获取用户并创建Token
    user = AuthService.get_user_by_phone(db, request_body.phone)
    access_token, refresh_token = AuthService.create_tokens(user.id)
    
    AuthService.log_auth_event("reset_password_success", user_id=user.id, extra={
        "phone": request_body.phone[-4:],
        "ip": client_ip
    })
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=False
    )
