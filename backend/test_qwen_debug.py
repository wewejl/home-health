"""
测试阿里云 Qwen TTS Realtime API
抓包查看实际协议格式
"""
import os
import base64
import json
import time
import threading
import dashscope
from dashscope.audio.qwen_tts_realtime import *

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-61e2b328d6614408867ac61240423740")
TEXT = "你好你好"

class DebugCallback(QwenTtsRealtimeCallback):
    def __init__(self):
        self.complete_event = threading.Event()
        self.messages = []

    def on_open(self) -> None:
        print('=== WebSocket 已打开 ===')

    def on_close(self, close_status_code, close_msg) -> None:
        print(f'=== 连接已关闭: code={close_status_code}, msg={close_msg} ===')

    def on_event(self, response) -> None:
        msg_type = response.get('type', 'unknown')
        print(f'\n[收到消息] type: {msg_type}')
        print(json.dumps(response, ensure_ascii=False, indent=2))
        self.messages.append(response)

        if msg_type == 'session.finished':
            self.complete_event.set()

    def wait_for_finished(self):
        self.complete_event.wait()


def test_with_debug():
    dashscope.api_key = API_KEY
    print(f"API Key: {API_KEY[:20]}...")
    print(f"测试文本: '{TEXT}'")

    callback = DebugCallback()

    print('\n=== 创建 QwenTtsRealtime 对象 ===')
    print('model: qwen3-tts-flash-realtime')
    print('url: wss://dashscope.aliyuncs.com/api-ws/v1/realtime')

    qwen_tts = QwenTtsRealtime(
        model='qwen3-tts-flash-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )

    print('\n=== 调用 connect() ===')
    qwen_tts.connect()
    time.sleep(0.5)

    print('\n=== 调用 update_session() ===')
    print('参数: voice=Cherry, response_format=PCM_24000HZ_MONO_16BIT, mode=server_commit')
    qwen_tts.update_session(
        voice='Cherry',
        response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
        mode='server_commit'
    )
    time.sleep(0.5)

    print('\n=== 调用 append_text() ===')
    print(f'文本: {TEXT}')
    qwen_tts.append_text(TEXT)
    time.sleep(0.2)

    print('\n=== 调用 finish() ===')
    qwen_tts.finish()

    print('\n=== 等待完成 ===')
    callback.wait_for_finished()

    # 统计
    audio_chunks = [m for m in callback.messages if m.get('type') == 'response.audio.delta']
    print(f'\n=== 结果 ===')
    print(f'音频块数: {len(audio_chunks)}')
    print(f'总消息数: {len(callback.messages)}')


if __name__ == '__main__':
    test_with_debug()
