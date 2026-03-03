"""home-health-ai FastAPI entrypoint."""

from __future__ import annotations

from fastapi import Depends, FastAPI

from .agent import ConsultAgentService
from .auth import require_internal_token
from .config import get_settings
from .models import ChatRespondRequest, ChatRespondResponse

settings = get_settings()
app = FastAPI(title="home-health-ai", version="0.1.0")
service = ConsultAgentService()


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy", "service": settings.APP_NAME}


@app.post(
    "/v1/chat/respond",
    response_model=ChatRespondResponse,
    dependencies=[Depends(require_internal_token)],
)
async def respond(payload: ChatRespondRequest) -> ChatRespondResponse:
    return await service.respond(payload)
