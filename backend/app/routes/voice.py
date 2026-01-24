"""
语音服务 WebSocket 路由

提供 ASR (语音识别) 和 TTS (语音合成) 的转发服务：
- /ws/voice/asr: 语音识别，前端发送 PCM 音频，返回识别结果
- /ws/voice/tts: 语音合成，前端发送文本，返回流式 PCM 音频

API Key 保存在后端，前端通过 token 认证即可
"""
import asyncio
import json
import base64
import os
import logging
from typing import Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws/voice", tags=["voice"])

# 阿里云配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
FUNASR_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

# 活跃连接管理
_active_asr_connections: Set[WebSocket] = set()
_active_tts_connections: Set[WebSocket] = set()


# ============================================================
# 认证依赖
# ============================================================

async def verify_websocket_token(websocket: WebSocket, token: str = Query(...)):
    """验证 WebSocket token"""
    # TODO: 实现 JWT token 验证
    # 目前先简单检查 token 不为空
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        raise ValueError("Missing token")

    # 测试模式：test_ 开头的 token 直接通过
    if token.startswith("test_"):
        return {"user_id": token.split("_")[1], "is_test": True}

    # 正式模式：验证 JWT token
    # from ..services.auth import verify_token
    # payload = verify_token(token)
    # return payload

    return {"user_id": "unknown"}


# ============================================================
# ASR 语音识别端点
# ============================================================

@router.websocket("/asr")
async def asr_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证 token")
):
    """
    ASR 语音识别 WebSocket 端点

    连接 URL: ws://host/ws/voice/asr?token=xxx

    协议:
    - 前端 → 后端: 二进制 PCM 音频数据 (16kHz, 单声道, 16-bit)
    - 后端 → 前端: JSON 消息
        {"event": "asr_ready", "task_id": "xxx"}
        {"event": "asr_partial", "text": "中间结果"}
        {"event": "asr_final", "text": "最终结果"}
        {"event": "error", "message": "错误信息"}
    """
    await websocket.accept()
    _active_asr_connections.add(websocket)

    user_id = f"ws_{id(websocket)}"
    logger.info(f"[ASR] 新连接: {user_id}")

    funasr_ws = None
    task_id = None

    try:
        # 验证 token
        if not token:
            await websocket.send_json({"event": "error", "message": "Missing token"})
            await websocket.close()
            return

        # 连接阿里云 FunASR
        headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
        funasr_ws = await ws_connect(FUNASR_WS_URL, additional_headers=headers)
        logger.info(f"[ASR] 已连接阿里云 FunASR: {user_id}")

        # 发送 run-task 指令
        import uuid
        task_id = uuid.uuid4().hex[:32]
        run_task = {
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "asr",
                "function": "recognition",
                "model": "fun-asr-realtime",
                "parameters": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "semantic_punctuation_enabled": False,
                    "max_sentence_silence": 1300
                },
                "input": {}
            }
        }
        await funasr_ws.send(json.dumps(run_task))
        logger.info(f"[ASR] 发送 run-task: {task_id}")

        # 等待 task-started
        response = await funasr_ws.recv()
        data = json.loads(response)

        if data.get("header", {}).get("event") != "task-started":
            error_msg = data.get("header", {}).get("error_message", "Unknown error")
            await websocket.send_json({"event": "error", "message": f"FunASR task failed: {error_msg}"})
            return

        logger.info(f"[ASR] FunASR 任务已启动: {task_id}")
        await websocket.send_json({"event": "asr_ready", "task_id": task_id})

        # 双向转发
        async def forward_audio_to_funasr():
            """接收前端音频，转发到阿里云"""
            try:
                while True:
                    audio_data = await websocket.receive_bytes()
                    await funasr_ws.send(audio_data)
            except WebSocketDisconnect:
                logger.info(f"[ASR] 前端断开: {user_id}")
            except Exception as e:
                logger.error(f"[ASR] 转发音频错误: {e}")

        async def forward_results_to_frontend():
            """接收阿里云结果，转发到前端"""
            try:
                while True:
                    response = await funasr_ws.recv()
                    if isinstance(response, str):
                        data = json.loads(response)
                        event = data.get("header", {}).get("event")

                        if event == "result-generated":
                            output = data.get("payload", {}).get("output", {})
                            sentence = output.get("sentence", {})
                            text = sentence.get("text", "")
                            is_final = sentence.get("sentence_end", False)

                            await websocket.send_json({
                                "event": "asr_final" if is_final else "asr_partial",
                                "text": text
                            })

                            if is_final:
                                logger.info(f"[ASR] 识别结果: {text}")

                        elif event == "task-finished":
                            logger.info(f"[ASR] 任务完成: {task_id}")
                            break

                        elif event == "task-failed":
                            error_msg = data.get("header", {}).get("error_message", "Unknown error")
                            await websocket.send_json({"event": "error", "message": error_msg})
                            break

            except ConnectionClosed:
                logger.info(f"[ASR] 阿里云连接关闭: {user_id}")
            except Exception as e:
                logger.error(f"[ASR] 转发结果错误: {e}")

        # 并发运行
        await asyncio.gather(
            forward_audio_to_funasr(),
            forward_results_to_frontend(),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"[ASR] WebSocket 断开: {user_id}")
    except Exception as e:
        logger.error(f"[ASR] 错误: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except:
            pass
    finally:
        if funasr_ws:
            try:
                await funasr_ws.close()
            except:
                pass
        _active_asr_connections.discard(websocket)
        logger.info(f"[ASR] 连接关闭: {user_id}")


# ============================================================
# TTS 语音合成端点
# ============================================================

@router.websocket("/tts")
async def tts_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证 token")
):
    """
    TTS 语音合成 WebSocket 端点 (长连接模式)

    连接 URL: ws://host/ws/voice/tts?token=xxx

    长连接协议:
    - 连接建立后立即配置会话，等待多次合成请求
    - 前端 → 后端: JSON {"action": "speak", "text": "要合成的文本", "voice": "Cherry"}
    - 后端 → 前端:
        {"event": "tts_ready"} - 连接建立完成
        {"event": "tts_finished"} - 单次合成完成
        二进制 PCM 音频数据 (24kHz, 单声道, 16-bit)
    """
    await websocket.accept()
    _active_tts_connections.add(websocket)

    user_id = f"ws_{id(websocket)}"
    logger.info(f"[TTS] 新连接 (长连接模式): {user_id}")

    tts_ws = None
    default_voice = "Cherry"

    try:
        # 验证 token
        if not token:
            await websocket.send_json({"event": "error", "message": "Missing token"})
            await websocket.close()
            return

        # 连接阿里云 Qwen Realtime (长连接)
        url = f"{QWEN_TTS_WS_URL}?model=qwen3-tts-flash-realtime"
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable"
        }

        tts_ws = await ws_connect(url, additional_headers=headers)
        logger.info(f"[TTS] 已连接阿里云 Qwen Realtime: {user_id}")

        # 配置会话
        session_update = {
            "type": "session.update",
            "session": {
                "voice": default_voice,
                "response_format": "pcm",
                "mode": "server_commit"
            }
        }
        await tts_ws.send(json.dumps(session_update))

        # 等待 session.created
        response = await tts_ws.recv()
        data = json.loads(response)

        if data.get("type") != "session.created":
            await websocket.send_json({"event": "error", "message": f"Failed to create session: {data.get('type')}"})
            return

        logger.info(f"[TTS] 会话已创建: {user_id}")

        # 等待 session.updated
        await tts_ws.recv()
        logger.info(f"[TTS] 会话已配置: {user_id}")

        # 通知前端准备就绪
        await websocket.send_json({"event": "tts_ready"})

        # 长连接循环：等待多次合成请求
        while True:
            try:
                # 接收合成请求
                msg = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=300.0  # 5分钟无请求则超时
                )
            except asyncio.TimeoutError:
                # 超时不断开，继续等待
                continue

            action = msg.get("action", "")

            if action != "speak":
                # 忽略非 speak 请求
                continue

            text = msg.get("text", "")
            voice = msg.get("voice", default_voice)

            if not text:
                await websocket.send_json({"event": "error", "message": "Missing text"})
                continue

            logger.info(f"[TTS] 合成请求: '{text[:30]}...', voice: {voice}")

            # 如果语音改变了，重新配置会话
            if voice != default_voice:
                default_voice = voice
                session_update = {
                    "type": "session.update",
                    "session": {
                        "voice": default_voice,
                        "response_format": "pcm",
                        "mode": "server_commit"
                    }
                }
                await tts_ws.send(json.dumps(session_update))
                await tts_ws.recv()  # session.updated
                logger.info(f"[TTS] 语音已更新: {default_voice}")

            # 发送文本
            text_append = {
                "type": "input_text_buffer.append",
                "text": text
            }
            await tts_ws.send(json.dumps(text_append))

            await asyncio.sleep(0.05)

            # 发送 finish
            finish = {"type": "session.finish"}
            await tts_ws.send(json.dumps(finish))
            logger.info(f"[TTS] 文本已发送: {user_id}")

            # 转发音频数据
            chunk_count = 0
            while True:
                response = await tts_ws.recv()

                if isinstance(response, str):
                    data = json.loads(response)
                    event_type = data.get("type")

                    if event_type == "input_text_buffer.committed":
                        logger.info(f"[TTS] 文本已确认: {user_id}")

                    elif event_type == "response.audio.delta":
                        # base64 编码的音频 - 解码后转发
                        delta = data.get("delta", "")
                        audio_data = base64.b64decode(delta)
                        chunk_count += 1

                        # 立即转发二进制音频
                        await websocket.send_bytes(audio_data)
                        logger.debug(f"[TTS] 转发音频块 #{chunk_count}: {len(audio_data)} bytes")

                    elif event_type == "response.audio.done":
                        logger.info(f"[TTS] 音频传输完成 (共 {chunk_count} 块): {user_id}")

                    elif event_type == "session.finished":
                        await websocket.send_json({"event": "tts_finished"})
                        logger.info(f"[TTS] 合成完成: {user_id}")
                        break

                    elif event_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        await websocket.send_json({"event": "error", "message": error_msg})
                        logger.error(f"[TTS] 错误: {error_msg}")
                        break

    except WebSocketDisconnect:
        logger.info(f"[TTS] 前端断开: {user_id}")
    except Exception as e:
        logger.error(f"[TTS] 错误: {e}")
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except:
            pass
    finally:
        if tts_ws:
            try:
                await tts_ws.close()
            except:
                pass
        _active_tts_connections.discard(websocket)
        logger.info(f"[TTS] 连接关闭: {user_id}")


# ============================================================
# 状态查询端点
# ============================================================

@router.get("/status")
async def voice_status():
    """获取语音服务状态"""
    return {
        "service": "voice",
        "asr_connections": len(_active_asr_connections),
        "tts_connections": len(_active_tts_connections),
        "dashscope_configured": bool(DASHSCOPE_API_KEY),
        "endpoints": {
            "asr": "/ws/voice/asr",
            "tts": "/ws/voice/tts"
        }
    }
