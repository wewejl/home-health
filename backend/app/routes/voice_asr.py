"""
语音识别 WebSocket 路由 (GLM-ASR)

使用 GLM-ASR HTTP API 实现语音识别 WebSocket 服务：
- /ws/voice/asr: 语音识别，前端发送 PCM 音频，返回识别结果
- 使用更可靠的 HTTP API 而不是 WebSocket 转发
- 支持语言自动检测
"""
import asyncio
import json
import base64
import io
import logging
import uuid
from typing import Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from websockets.exceptions import ConnectionClosed

from ..services.auth_service import AuthService
from ..services.ai.transcription_service import get_transcription_service, TranscriptionStatus
from ..services.voice_protocol import (
    VoiceEvents,
    VoiceConfig,
    create_error_response,
    create_asr_ready_response,
    create_asr_partial_response,
    create_asr_final_response,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws/voice", tags=["voice"])

# 活跃连接管理
_active_asr_connections: Set[WebSocket] = set()

# 音频缓冲配置
BUFFER_DURATION = 2.0  # 缓冲2秒音频
MIN_BUFFER_SIZE = 16000  # 最小缓冲 1 秒 (16kHz * 1s * 2 bytes)


# ============================================================
# 工具函数
# ============================================================

async def safe_send_json(websocket: WebSocket, data: dict) -> bool:
    """安全发送 JSON 消息"""
    try:
        await websocket.send_json(data)
        return True
    except (WebSocketDisconnect, RuntimeError):
        logger.warning("[Voice] 尝试发送消息时连接已断开")
        return False


async def safe_close(websocket: WebSocket, code: int = 1000, reason: str = "") -> None:
    """安全关闭 WebSocket"""
    try:
        await websocket.close(code=code, reason=reason)
    except RuntimeError:
        pass


def convert_m4a_to_pcm(m4a_data: bytes) -> Optional[bytes]:
    """
    将 M4A (AAC) 音频转换为 PCM

    注意：这是一个简化版本。实际生产环境应该使用 ffmpeg
    """
    try:
        # 尝试使用 ffmpeg Python 库
        import ffmpeg

        # 读取 M4A
        input_stream = ffmpeg.input('pipe:', format='m4a')

        # 转换为 PCM (16kHz, 单声道, 16-bit)
        output_stream = ffmpeg.output(
            input_stream,
            'pipe:',
            format='s16le',
            acodec='pcm_s16le',
            ar=VoiceConfig.ASR_SAMPLE_RATE,
            ac=VoiceConfig.ASR_CHANNELS
        )

        out, _ = ffmpeg.run(output_stream, input=m4a_data, capture_stdout=True, capture_stderr=True)
        return out

    except ImportError:
        logger.warning("[Voice] ffmpeg 未安装，返回原始数据")
        return None
    except Exception as e:
        logger.error(f"[Voice] 音频转换失败: {e}")
        return None


def add_wav_header(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """
    为原始 PCM 数据添加 WAV 文件头

    Args:
        pcm_data: 原始 PCM 数据 (16-bit signed integer, little-endian)
        sample_rate: 采样率 (Hz)
        channels: 声道数
        bits_per_sample: 每个采样的位数

    Returns:
        带有 WAV 文件头的字节数据
    """
    import struct

    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_data)
    file_size = 36 + data_size  # RIFF header size (12) + fmt chunk (24) + data header (8) - 8

    # WAV 文件结构
    # RIFF header
    riff_header = b'RIFF' + struct.pack('<I', file_size) + b'WAVE'

    # fmt chunk
    fmt_chunk = (
        b'fmt ' +  # chunk ID
        struct.pack('<I', 16) +  # chunk size (16 for PCM)
        struct.pack('<H', 1) +  # audio format (1 = PCM)
        struct.pack('<H', channels) +  # channels
        struct.pack('<I', sample_rate) +  # sample rate
        struct.pack('<I', byte_rate) +  # byte rate
        struct.pack('<H', block_align) +  # block align
        struct.pack('<H', bits_per_sample)  # bits per sample
    )

    # data chunk
    data_chunk = b'data' + struct.pack('<I', data_size) + pcm_data

    return riff_header + fmt_chunk + data_chunk


# ============================================================
# 认证依赖
# ============================================================

async def verify_websocket_token(websocket: WebSocket, token: str = Query(...)):
    """验证 WebSocket token"""
    if not token:
        await safe_close(websocket, code=1008, reason="Missing token")
        raise ValueError("Missing token")

    user_id = AuthService.verify_token(token, token_type="access")

    if user_id is None:
        await safe_close(websocket, code=1008, reason="Invalid token")
        raise ValueError("Invalid token")

    return {"user_id": user_id}


# ============================================================
# ASR 语音识别端点 (GLM-ASR)
# ============================================================

@router.websocket("/asr")
async def asr_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证 token"),
    language: str = Query("auto", description="识别语言: auto, zh, en, yue, etc.")
):
    """
    ASR 语音识别 WebSocket 端点 (使用 GLM-ASR HTTP API)

    连接 URL: ws://host/ws/voice/asr?token=xxx&language=auto

    协议：
    - 前端 → 后端:
        - JSON {"action": "start", "format": "m4a"} - 开始识别
        - 二进制音频数据
        - JSON {"action": "finish"} - 完成发送
    - 后端 → 前端:
        {"event": "asr_ready", "task_id": "xxx"}
        {"event": "asr_partial", "text": "中间结果"}
        {"event": "asr_final", "text": "最终结果", "language": "zh"}
        {"event": "error", "message": "错误信息"}
    """
    await websocket.accept()
    _active_asr_connections.add(websocket)

    user_id = f"ws_{id(websocket)}"
    task_id = uuid.uuid4().hex[:16]

    logger.info(f"[GLM-ASR] 新连接: {user_id}, 语言: {language}")

    running = False
    audio_buffer = bytearray()
    current_format = "m4a"  # 默认格式

    try:
        # 验证 token
        if not token:
            await safe_send_json(websocket, create_error_response("Missing token"))
            await safe_close(websocket)
            return

        # 通知客户端准备就绪
        await safe_send_json(websocket, create_asr_ready_response(task_id))

        transcription_service = get_transcription_service()
        running = True

        # 主循环：接收音频数据
        while running:
            try:
                # 接收消息 (可能是 JSON 或二进制)
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=300.0  # 5分钟超时
                )

                # 处理 JSON 消息 (控制命令)
                if "text" in message:
                    data = json.loads(message["text"])
                    action = data.get("action", "")

                    if action == "start":
                        current_format = data.get("format", "m4a")
                        logger.info(f"[GLM-ASR] 开始识别, 格式: {current_format}")
                        audio_buffer.clear()

                    elif action == "finish":
                        # 完成音频发送，开始转写
                        logger.info(f"[GLM-ASR] 音频接收完成, 大小: {len(audio_buffer)} bytes, 格式: {current_format}")

                        if len(audio_buffer) > MIN_BUFFER_SIZE:
                            # 执行转写
                            await safe_send_json(websocket, {
                                "event": "asr_partial",
                                "text": "正在识别..."
                            })

                            # 如果是 PCM 格式，需要添加 WAV 文件头
                            audio_data = bytes(audio_buffer)
                            if current_format == "pcm":
                                logger.info(f"[GLM-ASR] 添加 WAV 文件头到 PCM 数据")
                                audio_data = add_wav_header(
                                    audio_data,
                                    sample_rate=VoiceConfig.ASR_SAMPLE_RATE,
                                    channels=VoiceConfig.ASR_CHANNELS,
                                    bits_per_sample=16
                                )

                            # 将音频转为 base64 (GLM-ASR 需要)
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                            # 调用 GLM-ASR
                            result = await transcription_service.transcribe(
                                audio_base64=audio_base64,
                                language=language,
                                extract_symptoms=True
                            )

                            if result.status == TranscriptionStatus.COMPLETED:
                                await safe_send_json(websocket, {
                                    "event": VoiceEvents.ASR_FINAL.value,
                                    "text": result.text,
                                    "language": result.language,
                                    "confidence": result.confidence,
                                    "symptoms": result.extracted_symptoms
                                })
                                logger.info(f"[GLM-ASR] 识别成功: {result.text[:50]}...")
                            else:
                                await safe_send_json(websocket, create_error_response(
                                    result.error_message or "转写失败"
                                ))
                        else:
                            await safe_send_json(websocket, create_error_response(
                                f"音频太短，至少需要 {MIN_BUFFER_SIZE // 2} 秒"
                            ))

                        audio_buffer.clear()

                    elif action == "cancel":
                        logger.info(f"[GLM-ASR] 取消识别")
                        audio_buffer.clear()

                    elif action == "ping":
                        await safe_send_json(websocket, {"event": "pong"})

                # 处理二进制消息 (音频数据)
                elif "bytes" in message:
                    audio_data = message["bytes"]
                    audio_buffer.extend(audio_data)
                    logger.debug(f"[GLM-ASR] 缓冲音频: {len(audio_buffer)} bytes")

            except asyncio.TimeoutError:
                logger.info(f"[GLM-ASR] 连接超时: {user_id}")
                running = False
            except WebSocketDisconnect:
                logger.info(f"[GLM-ASR] 前端断开: {user_id}")
                running = False
            except Exception as e:
                logger.error(f"[GLM-ASR] 处理消息错误: {e}", exc_info=True)
                await safe_send_json(websocket, create_error_response(f"处理错误: {str(e)}"))
                running = False

    except WebSocketDisconnect:
        logger.info(f"[GLM-ASR] WebSocket 断开: {user_id}")
    except Exception as e:
        logger.error(f"[GLM-ASR] 未捕获的异常: {e}", exc_info=True)
        await safe_send_json(websocket, create_error_response(f"内部错误: {str(e)}"))
    finally:
        running = False
        _active_asr_connections.discard(websocket)
        logger.info(f"[GLM-ASR] 连接关闭: {user_id}")


# ============================================================
# 状态查询端点
# ============================================================

@router.get("/status")
async def voice_status():
    """获取语音服务状态"""
    from ..config import get_settings
    settings = get_settings()

    return {
        "service": "voice_asr",
        "provider": "dashscope",  # 使用阿里云 DashScope ASR
        "asr_connections": len(_active_asr_connections),
        "asr_configured": bool(settings.DASHSCOPE_API_KEY),
        "endpoints": {
            "asr": "/ws/voice/asr"
        },
        "config": {
            "asr_sample_rate": VoiceConfig.ASR_SAMPLE_RATE,
            "asr_format": "pcm",
            "supported_languages": ["auto", "zh", "en", "yue", "sichuanese", "ja", "ko"]
        }
    }
