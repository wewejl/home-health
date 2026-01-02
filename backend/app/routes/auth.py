from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.auth import LoginRequest, LoginResponse, UserResponse
from ..services.auth_service import AuthService
from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if not AuthService.verify_code(request.phone, request.code):
        raise HTTPException(status_code=400, detail="验证码错误")

    user = AuthService.get_or_create_user(db, request.phone)
    token = AuthService.create_token(user.id)

    return LoginResponse(
        token=token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
