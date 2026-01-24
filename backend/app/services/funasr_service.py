"""
阿里云 FunASR 实时语音识别服务
文档: https://help.aliyun.com/zh/model-studio/fun-asr-realtime-websocket-api
"""
import asyncio
import json
import uuid
from typing import Optional
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import os

# 阿里云 FunASR 配置
FUNASR_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
FUNASR_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")


class FunASRConfig(BaseModel):
    """FunASR 配置"""
    format: str = "pcm"           # 音频格式: pcm, wav, mp3, opus, speex, aac, amr
    sample_rate: int = 16000     # 采样率
    vocabulary_id: Optional[str] = None  # 热词ID
    semantic_punctuation: bool = False    # 语义断句(False=VAD断句, 低延迟)
    max_sentence_silence: int = 1300     # VAD静音阈值(毫秒)


class FunASRMessage(BaseModel):
    """FunASR 消息"""
    header: dict
    payload: dict


class FunASRService:
    """阿里云 FunASR 实时语音识别服务"""

    def __init__(self, config: FunASRConfig):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.task_id: Optional[str] = None
        self.is_connected = False

    async def connect(self) -> bool:
        """连接到 FunASR WebSocket 服务"""
        if self.is_connected:
            return True

        headers = {
            "Authorization": f"Bearer {FUNASR_API_KEY}"
        }

        try:
            self.ws = await websockets.connect(
                FUNASR_WS_URL,
                additional_headers=headers  # websockets >= 16.0 使用 additional_headers
            )
            self.is_connected = True
            print("[FunASR] WebSocket 已连接")
            return True
        except Exception as e:
            print(f"[FunASR] 连接失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
        self.is_connected = False
        print("[FunASR] 已断开连接")

    async def start_task(self) -> bool:
        """启动识别任务"""
        if not self.is_connected:
            await self.connect()

        # 生成任务 ID
        self.task_id = uuid.uuid4().hex[:32]

        # 构造 run-task 指令
        message = {
            "header": {
                "action": "run-task",
                "task_id": self.task_id,
                "streaming": "duplex"
            },
            "payload": {
                "task_group": "audio",
                "task": "asr",
                "function": "recognition",
                "model": "fun-asr-realtime",
                "parameters": {
                    "format": self.config.format,
                    "sample_rate": self.config.sample_rate,
                    "semantic_punctuation_enabled": self.config.semantic_punctuation,
                    "max_sentence_silence": self.config.max_sentence_silence
                },
                "input": {}
            }
        }

        if self.config.vocabulary_id:
            message["payload"]["parameters"]["vocabulary_id"] = self.config.vocabulary_id

        await self.ws.send(json.dumps(message))
        print(f"[FunASR] 已发送 run-task 指令, task_id: {self.task_id}")

        # 等待 task-started 事件
        return await self._wait_for_task_started()

    async def _wait_for_task_started(self, timeout: int = 10) -> bool:
        """等待任务启动"""
        try:
            async with asyncio.timeout(timeout):
                while True:
                    response = await self.ws.recv()
                    data = json.loads(response)
                    event = data.get("header", {}).get("event")

                    if event == "task-started":
                        print("[FunASR] 任务已启动")
                        return True
                    elif event == "task-failed":
                        error_msg = data.get("header", {}).get("error_message", "未知错误")
                        print(f"[FunASR] 任务启动失败: {error_msg}")
                        return False
        except asyncio.TimeoutError:
            print("[FunASR] 等待任务启动超时")
            return False

    async def send_audio(self, audio_data: bytes):
        """发送音频数据"""
        if not self.is_connected:
            return

        await self.ws.send(audio_data)

    async def finish_task(self):
        """结束识别任务"""
        if not self.is_connected or not self.task_id:
            return

        message = {
            "header": {
                "action": "finish-task",
                "task_id": self.task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {}
            }
        }

        await self.ws.send(json.dumps(message))
        print("[FunASR] 已发送 finish-task 指令")

    async def receive_results(self):
        """接收识别结果（生成器）"""
        if not self.is_connected:
            return

        try:
            while True:
                response = await self.ws.recv()
                data = json.loads(response)
                event = data.get("header", {}).get("event")

                if event == "result-generated":
                    output = data.get("payload", {}).get("output", {})
                    sentence = output.get("sentence", {})

                    result = {
                        "text": sentence.get("text", ""),
                        "begin_time": sentence.get("begin_time"),
                        "end_time": sentence.get("end_time"),
                        "sentence_end": sentence.get("sentence_end", False),
                        "words": sentence.get("words", [])
                    }

                    yield result

                    if result["sentence_end"]:
                        print(f"[FunASR] 最终结果: {result['text']}")

                elif event == "task-finished":
                    print("[FunASR] 任务完成")
                    break

                elif event == "task-failed":
                    error_msg = data.get("header", {}).get("error_message", "未知错误")
                    print(f"[FunASR] 任务失败: {error_msg}")
                    break

        except websockets.exceptions.ConnectionClosed:
            print("[FunASR] 连接已关闭")
        except Exception as e:
            print(f"[FunASR] 接收结果错误: {e}")


# 全局服务实例（用于管理连接）
_active_services: dict[str, FunASRService] = {}


async def get_funasr_service(session_id: str, config: FunASRConfig) -> FunASRService:
    """获取或创建 FunASR 服务实例"""
    if session_id not in _active_services:
        service = FunASRService(config)
        _active_services[session_id] = service
    return _active_services[session_id]


async def close_funasr_service(session_id: str):
    """关闭 FunASR 服务实例"""
    if session_id in _active_services:
        await _active_services[session_id].disconnect()
        del _active_services[session_id]
