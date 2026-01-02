from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.orm import Session
from ..models.user import User
from ..config import get_settings

settings = get_settings()


class AuthService:
    @staticmethod
    def verify_code(phone: str, code: str) -> bool:
        if settings.TEST_MODE:
            return code == "000000"
        return False

    @staticmethod
    def get_or_create_user(db: Session, phone: str) -> User:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(phone=phone, nickname=f"用户{phone[-4:]}")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def create_token(user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "exp": expire
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> int | None:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return int(payload.get("sub"))
        except Exception:
            return None
