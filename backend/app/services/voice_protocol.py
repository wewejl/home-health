"""
语音服务协议定义

定义前后端 WebSocket 通信的事件类型和常量
确保 iOS 和 Android 客户端使用统一的协议

注: TTS (Text-to-Speech) 功能已移除，仅保留 ASR (Automatic Speech Recognition)
"""

from enum import Enum


class VoiceEvents(str, Enum):
    """语音服务事件类型"""
    # ASR 事件
    ASR_READY = "asr_ready"
    ASR_PARTIAL = "asr_partial"
    ASR_FINAL = "asr_final"
    ASR_ROUND_COMPLETE = "asr_round_complete"
    ASR_ROUND_READY = "asr_round_ready"

    # 通用事件
    ERROR = "error"

    # TTS 事件已移除 (TTS_READY, TTS_FINISHED 已废弃)


class VoiceConfig:
    """语音服务配置常量"""

    # 心跳配置
    HEARTBEAT_INTERVAL_MS = 100  # 静音帧发送间隔 (毫秒)
    SILENT_PCM_SIZE = 3200  # 静音帧大小 (字节) = 1600 samples * 2 bytes (100ms @ 16kHz)

    # 超时配置
    REQUEST_TIMEOUT_SECONDS = 300  # 请求超时时间 (秒)

    # 音频格式
    ASR_SAMPLE_RATE = 16000  # ASR 采样率 (Hz)
    ASR_CHANNELS = 1  # ASR 声道数
    ASR_FORMAT = "pcm"  # ASR 音频格式

    # TTS 配置已移除 (TTS_SAMPLE_RATE, TTS_CHANNELS, TTS_FORMAT, TTS_DEFAULT_VOICE 已废弃)

    # VAD 配置
    MAX_SENTENCE_SILENCE_MS = 1300  # 最大静音时间 (毫秒)


def create_error_response(message: str) -> dict:
    """创建错误响应"""
    return {
        "event": VoiceEvents.ERROR.value,
        "message": message
    }


def create_asr_ready_response(task_id: str) -> dict:
    """创建 ASR 就绪响应"""
    return {
        "event": VoiceEvents.ASR_READY.value,
        "task_id": task_id
    }


def create_asr_partial_response(text: str) -> dict:
    """创建 ASR 中间结果响应"""
    return {
        "event": VoiceEvents.ASR_PARTIAL.value,
        "text": text
    }


def create_asr_final_response(text: str) -> dict:
    """创建 ASR 最终结果响应"""
    return {
        "event": VoiceEvents.ASR_FINAL.value,
        "text": text
    }


def create_asr_round_complete_response() -> dict:
    """创建 ASR 一轮完成响应"""
    return {
        "event": VoiceEvents.ASR_ROUND_COMPLETE.value
    }
