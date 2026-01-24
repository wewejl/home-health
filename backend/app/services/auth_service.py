import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..models.user import User
from ..config import get_settings
from .sms_service import sms_service
from .password_service import hash_password, verify_password, validate_password_strength

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""
    
    @staticmethod
    async def send_verification_code(phone: str, client_ip: str = "0.0.0.0") -> Tuple[bool, str, int]:
        """
        发送验证码

        Args:
            phone: 手机号
            client_ip: 客户端IP

        Returns:
            (是否成功, 消息, 过期时间秒数)
        """
        return await sms_service.send_verification_code(phone, client_ip)
    
    @staticmethod
    def verify_code(phone: str, code: str) -> Tuple[bool, str]:
        """
        验证验证码

        Args:
            phone: 手机号
            code: 验证码

        Returns:
            (是否验证成功, 错误消息)

        验证规则:
        - 测试模式 (TEST_MODE=true): 000000 为万能验证码
        - 生产模式: 必须使用真实发送的验证码
        """
        return sms_service.verify_code(phone, code)

    @staticmethod
    def get_or_create_user(db: Session, phone: str) -> Tuple[User, bool]:
        """
        获取或创建用户
        
        Returns:
            (用户对象, 是否新用户)
        """
        user = db.query(User).filter(User.phone == phone).first()
        is_new = False
        
        if not user:
            user = User(
                phone=phone, 
                nickname=f"用户{phone[-4:]}",
                is_profile_completed=False,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new = True
            logger.info(f"[AUTH] 新用户注册: user_id={user.id}, phone={phone[-4:]}")
        else:
            logger.info(f"[AUTH] 用户登录: user_id={user.id}, phone={phone[-4:]}")
        
        return user, is_new

    @staticmethod
    def create_token(user_id: int, token_type: str = "access") -> str:
        """
        创建JWT Token
        
        Args:
            user_id: 用户ID
            token_type: Token类型 (access/refresh)
        
        Returns:
            JWT Token字符串
        """
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": token_type,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_tokens(user_id: int) -> Tuple[str, str]:
        """
        创建访问Token和刷新Token
        
        Returns:
            (access_token, refresh_token)
        """
        access_token = AuthService.create_token(user_id, "access")
        refresh_token = AuthService.create_token(user_id, "refresh")
        return access_token, refresh_token

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[int]:
        """
        验证JWT Token

        Args:
            token: JWT Token 或测试令牌 (test_N 格式)
            token_type: 期望的Token类型

        Returns:
            用户ID 或 None
        """
        # 测试模式：支持 test_N 格式的测试令牌
        if settings.TEST_MODE and token.startswith("test_"):
            try:
                user_id = int(token.split("_")[1])
                logger.info(f"[AUTH] 测试模式认证: user_id={user_id}")
                return user_id
            except (ValueError, IndexError):
                logger.warning(f"[AUTH] 无效的测试令牌格式: {token}")
                return None

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # 检查Token类型
            if payload.get("type", "access") != token_type:
                logger.warning(f"[AUTH] Token类型不匹配: expected={token_type}, got={payload.get('type')}")
                return None

            user_id = payload.get("sub")
            if user_id is None:
                return None

            return int(user_id)
        except JWTError as e:
            logger.warning(f"[AUTH] Token验证失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[AUTH] Token验证异常: {str(e)}")
            return None

    @staticmethod
    def refresh_tokens(refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        使用刷新Token获取新的Token对
        
        Args:
            refresh_token: 刷新Token
        
        Returns:
            (new_access_token, new_refresh_token) 或 None
        """
        user_id = AuthService.verify_token(refresh_token, token_type="refresh")
        if user_id is None:
            return None
        
        return AuthService.create_tokens(user_id)

    @staticmethod
    def update_user_profile(db: Session, user: User, profile_data: dict) -> User:
        """
        更新用户资料
        
        Args:
            db: 数据库会话
            user: 用户对象
            profile_data: 要更新的资料字典
        
        Returns:
            更新后的用户对象
        """
        update_fields = [
            'nickname', 'avatar_url', 'gender', 'birthday',
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relation'
        ]
        
        for field in update_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(user, field, profile_data[field])
        
        # 检查是否完善了必要信息
        if user.nickname and user.gender:
            user.is_profile_completed = True
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"[AUTH] 用户资料更新: user_id={user.id}")
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()

    @staticmethod
    def log_auth_event(event_type: str, user_id: Optional[int] = None, extra: dict = None):
        """
        记录认证事件（用于埋点）
        
        TODO: 接入正式埋点系统
        """
        data = {"event": event_type, "user_id": user_id}
        if extra:
            data.update(extra)
        logger.info(f"[AUTH_EVENT] {data}")
    
    # ===== 密码认证相关方法 =====
    
    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return db.query(User).filter(User.phone == phone, User.is_active == True).first()
    
    @staticmethod
    def check_phone_status(db: Session, phone: str) -> Tuple[bool, bool]:
        """
        检查手机号状态
        
        Returns:
            (用户是否存在, 是否设置了密码)
        """
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return False, False
        return True, user.has_password
    
    @staticmethod
    def register_with_password(db: Session, phone: str, password: str) -> Tuple[User, bool]:
        """
        使用密码注册新用户或为老用户设置密码
        
        Args:
            db: 数据库会话
            phone: 手机号
            password: 明文密码
            
        Returns:
            (用户对象, 是否新用户)
        """
        user = db.query(User).filter(User.phone == phone).first()
        is_new = False
        
        if not user:
            # 新用户注册
            user = User(
                phone=phone,
                password_hash=hash_password(password),
                nickname=f"用户{phone[-4:]}",
                is_profile_completed=False,
                is_active=True
            )
            db.add(user)
            is_new = True
            logger.info(f"[AUTH] 新用户密码注册: phone={phone[-4:]}")
        else:
            # 老用户设置密码
            user.password_hash = hash_password(password)
            logger.info(f"[AUTH] 老用户设置密码: user_id={user.id}, phone={phone[-4:]}")
        
        db.commit()
        db.refresh(user)
        return user, is_new
    
    @staticmethod
    def login_with_password(db: Session, phone: str, password: str) -> Tuple[Optional[User], str]:
        """
        使用密码登录
        
        Args:
            db: 数据库会话
            phone: 手机号
            password: 明文密码
            
        Returns:
            (用户对象或None, 错误消息)
        """
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            logger.warning(f"[AUTH] 密码登录失败-用户不存在: phone={phone[-4:]}")
            return None, "手机号或密码错误"
        
        if not user.is_active:
            logger.warning(f"[AUTH] 密码登录失败-账号已禁用: user_id={user.id}")
            return None, "账号已被禁用"
        
        if not user.password_hash:
            logger.warning(f"[AUTH] 密码登录失败-未设置密码: user_id={user.id}")
            return None, "该账号未设置密码，请使用验证码登录"
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"[AUTH] 密码登录失败-密码错误: user_id={user.id}")
            return None, "手机号或密码错误"
        
        logger.info(f"[AUTH] 密码登录成功: user_id={user.id}")
        return user, ""
    
    @staticmethod
    def set_user_password(db: Session, user: User, new_password: str) -> bool:
        """
        设置或更新用户密码
        
        Args:
            db: 数据库会话
            user: 用户对象
            new_password: 新密码
            
        Returns:
            是否成功
        """
        try:
            user.password_hash = hash_password(new_password)
            db.commit()
            db.refresh(user)
            logger.info(f"[AUTH] 密码更新成功: user_id={user.id}")
            return True
        except Exception as e:
            logger.error(f"[AUTH] 密码更新失败: user_id={user.id}, error={str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def reset_password(db: Session, phone: str, new_password: str) -> Tuple[bool, str]:
        """
        重置密码（通过验证码验证后调用）
        
        Args:
            db: 数据库会话
            phone: 手机号
            new_password: 新密码
            
        Returns:
            (是否成功, 错误消息)
        """
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            return False, "用户不存在"
        
        if not user.is_active:
            return False, "账号已被禁用"
        
        try:
            user.password_hash = hash_password(new_password)
            db.commit()
            logger.info(f"[AUTH] 密码重置成功: user_id={user.id}")
            return True, ""
        except Exception as e:
            logger.error(f"[AUTH] 密码重置失败: phone={phone[-4:]}, error={str(e)}")
            db.rollback()
            return False, "密码重置失败，请重试"
