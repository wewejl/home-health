"""
语音协议模块 - 为 voice_asr 路由提供协议定义

定义语音识别相关的消息格式、事件类型和配置
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VoiceEvents(str, Enum):
    """语音事件类型"""
    # 连接管理
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # ASR 事件
    ASR_READY = "asr_ready"
    ASR_PARTIAL = "asr_partial"
    ASR_FINAL = "asr_final"
    ASR_ERROR = "asr_error"

    # VAD 事件
    VAD_SPEECH_START = "vad_speech_start"
    VAD_SPEECH_END = "vad_speech_end"

    # 控制事件
    START = "start"
    STOP = "stop"
    CONFIG = "config"


@dataclass
class VoiceConfig:
    """语音配置"""
    sample_rate: int = 16000
    channels: int = 1
    bits_per_sample: int = 16
    language: str = "zh"
    enable_punctuation: bool = True
    enable_partial: bool = True
    enable_vad: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bits_per_sample": self.bits_per_sample,
            "language": self.language,
            "enable_punctuation": self.enable_punctuation,
            "enable_partial": self.enable_partial,
            "enable_vad": self.enable_vad,
        }


@dataclass
class VoiceMessage:
    """语音消息基类"""
    event: VoiceEvents
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.value,
            "data": self.data
        }


@dataclass
class ASRResponse:
    """ASR 响应"""
    text: str
    is_final: bool = False
    confidence: float = 0.0
    timestamp: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "text": self.text,
            "is_final": self.is_final,
        }
        if self.confidence > 0:
            result["confidence"] = self.confidence
        if self.timestamp:
            result["timestamp"] = self.timestamp
        return result


# ============================================================
# 响应创建函数
# ============================================================

def create_error_response(error_code: str, message: str, details: Optional[Dict] = None) -> Dict[str, Any]:
    """创建错误响应"""
    response = {
        "event": VoiceEvents.ERROR.value,
        "data": {
            "code": error_code,
            "message": message
        }
    }
    if details:
        response["data"]["details"] = details
    return response


def create_asr_ready_response(config: VoiceConfig) -> Dict[str, Any]:
    """创建 ASR 准备就绪响应"""
    return {
        "event": VoiceEvents.ASR_READY.value,
        "data": {
            "config": config.to_dict(),
            "message": "ASR service ready"
        }
    }


def create_asr_partial_response(text: str, confidence: float = 0.0) -> Dict[str, Any]:
    """创建 ASR 部分识别响应"""
    return {
        "event": VoiceEvents.ASR_PARTIAL.value,
        "data": {
            "text": text,
            "is_final": False
        }
    }


def create_asr_final_response(text: str, confidence: float = 0.0) -> Dict[str, Any]:
    """创建 ASR 最终识别响应"""
    return {
        "event": VoiceEvents.ASR_FINAL.value,
        "data": {
            "text": text,
            "is_final": True
        }
    }


def create_vad_speech_start_response() -> Dict[str, Any]:
    """创建 VAD 语音开始响应"""
    return {
        "event": VoiceEvents.VAD_SPEECH_START.value,
        "data": {}
    }


def create_vad_speech_end_response() -> Dict[str, Any]:
    """创建 VAD 语音结束响应"""
    return {
        "event": VoiceEvents.VAD_SPEECH_END.value,
        "data": {}
    }


# ============================================================
# 消息解析函数
# ============================================================

def parse_client_message(data: Dict[str, Any]) -> tuple[VoiceEvents, Dict[str, Any]]:
    """解析客户端消息"""
    event_str = data.get("event", "")
    try:
        event = VoiceEvents(event_str)
    except ValueError:
        event = VoiceEvents.ERROR

    message_data = data.get("data", {})
    return event, message_data


# ============================================================
# 导出
# ============================================================

__all__ = [
    "VoiceEvents",
    "VoiceConfig",
    "VoiceMessage",
    "ASRResponse",
    "create_error_response",
    "create_asr_ready_response",
    "create_asr_partial_response",
    "create_asr_final_response",
    "create_vad_speech_start_response",
    "create_vad_speech_end_response",
    "parse_client_message",
]
