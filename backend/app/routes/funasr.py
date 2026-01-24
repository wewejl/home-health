"""
FunASR 语音识别 WebSocket 路由
iOS 客户端通过此 WebSocket 发送音频，接收识别结果
"""
import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Set
import logging

from app.services.funasr_service import (
    FunASRService,
    FunASRConfig,
    get_funasr_service,
    close_funasr_service
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/funasr", tags=["funasr"])

# 连接管理
_active_connections: Set[WebSocket] = set()


@router.websocket("/ws")
async def funasr_websocket(
    websocket: WebSocket,
    api_key: str = Query(..., description="阿里云 API Key"),
    sample_rate: int = Query(16000, description="采样率"),
    format: str = Query("pcm", description="音频格式")
):
    """
    FunASR 实时语音识别 WebSocket 接口

    连接 URL 示例:
    ws://localhost:8000/funasr/ws?api_key=sk-xxx&sample_rate=16000&format=pcm

    消息格式:
    客户端 → 服务端: 二进制音频数据
    服务端 → 客户端: JSON 格式的识别结果
    """
    # 设置全局 API Key（可选，也可以用环境变量）
    import os
    if api_key:
        os.environ["DASHSCOPE_API_KEY"] = api_key

    await websocket.accept()
    _active_connections.add(websocket)

    session_id = str(uuid.uuid4())
    logger.info(f"[FunASR] 新连接: {session_id}")

    # 创建配置
    config = FunASRConfig(
        format=format,
        sample_rate=sample_rate,
        semantic_punctuation=False,  # VAD 断句
        max_sentence_silence=1300
    )

    service: FunASRService = None
    task_started = False

    try:
        # 创建并启动 FunASR 服务
        service = await get_funasr_service(session_id, config)

        # 连接到阿里云
        if not await service.connect():
            await websocket.send_json({"error": "连接阿里云服务失败"})
            return

        # 启动识别任务
        if not await service.start_task():
            await websocket.send_json({"error": "启动识别任务失败"})
            return

        task_started = True
        await websocket.send_json({"event": "task_started", "session_id": session_id})

        # 同时接收客户端音频和阿里云识别结果
        async def receive_audio():
            """接收客户端音频"""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await service.send_audio(data)
            except WebSocketDisconnect:
                logger.info(f"[FunASR] 客户端断开: {session_id}")
            except Exception as e:
                logger.error(f"[FunASR] 接收音频错误: {e}")

        async def send_results():
            """发送识别结果给客户端"""
            try:
                async for result in service.receive_results():
                    await websocket.send_json({
                        "event": "result",
                        "text": result["text"],
                        "begin_time": result["begin_time"],
                        "end_time": result["end_time"],
                        "sentence_end": result["sentence_end"]
                    })

                    if result["sentence_end"]:
                        # 句子结束，发送最终结果事件
                        await websocket.send_json({
                            "event": "sentence_end",
                            "text": result["text"]
                        })
            except Exception as e:
                logger.error(f"[FunASR] 发送结果错误: {e}")

        # 并发运行
        await asyncio.gather(
            receive_audio(),
            send_results(),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"[FunASR] WebSocket 断开: {session_id}")
    except Exception as e:
        logger.error(f"[FunASR] 错误: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        # 清理
        if task_started and service:
            await service.finish_task()
            await service.disconnect()

        await close_funasr_service(session_id)
        _active_connections.remove(websocket)
        logger.info(f"[FunASR] 连接关闭: {session_id}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "funasr"}


@router.get("/config")
async def get_config():
    """获取配置说明"""
    return {
        "websocket_url": "ws://localhost:8000/funasr/ws",
        "parameters": {
            "api_key": "阿里云 DashScope API Key",
            "sample_rate": "采样率 (默认 16000)",
            "format": "音频格式 (pcm, wav, mp3 等)"
        },
        "audio_format": "16kHz, 单声道, PCM 格式",
        "note": "需要在 URL 参数中提供 api_key"
    }
