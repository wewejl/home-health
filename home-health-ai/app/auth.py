"""Internal service auth helpers."""

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_internal_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = (settings.INTERNAL_API_TOKEN or "").strip()

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    provided = authorization.split(" ", 1)[1].strip()
    if expected and provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid internal token",
        )
