"""
测试阿里云 Qwen TTS Realtime API
使用正确的模型和协议
"""
import os
import base64
import threading
import time
import dashscope
from dashscope.audio.qwen_tts_realtime import *

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-61e2b328d6614408867ac61240423740")
TEXT = "你好你好"

class MyCallback(QwenTtsRealtimeCallback):
    def __init__(self):
        self.complete_event = threading.Event()
        self.audio_chunks = 0
        self.first_audio_time = None
        self.start_time = None

    def on_open(self) -> None:
        print('✓ WebSocket 已打开')
        self.start_time = time.time()

    def on_close(self, close_status_code, close_msg) -> None:
        print(f'✓ 连接已关闭: code={close_status_code}, msg={close_msg}')

    def on_event(self, response) -> None:
        try:
            event_type = response['type']

            if event_type == 'session.created':
                print(f"✓ session.created")

            elif event_type == 'session.updated':
                print(f"✓ session.updated")

            elif event_type == 'input_text_buffer.committed':
                print(f"✓ input_text_buffer.committed")

            elif event_type == 'response.audio.delta':
                if self.first_audio_time is None:
                    self.first_audio_time = time.time()
                    delay = (self.first_audio_time - self.start_time) * 1000
                    print(f"✓ 首包延迟: {delay:.0f}ms")

                recv_audio_b64 = response['delta']
                audio_data = base64.b64decode(recv_audio_b64)
                self.audio_chunks += 1
                print(f"  音频块: {len(audio_data)} bytes")

            elif event_type == 'response.audio.done':
                print(f"✓ response.audio.done")

            elif event_type == 'response.done':
                print(f"✓ response.done")

            elif event_type == 'session.finished':
                print(f"✓ session.finished")
                self.complete_event.set()

            elif event_type == 'error':
                print(f"✗ Error: {response}")

        except Exception as e:
            print(f'✗ Error: {e}')

    def wait_for_finished(self):
        self.complete_event.wait()


def test_qwen_tts_realtime():
    dashscope.api_key = API_KEY
    print(f"API Key: {API_KEY[:20]}...")
    print(f"测试文本: '{TEXT}'")

    callback = MyCallback()

    # 尝试不同的模型名称
    models = [
        'qwen3-tts-flash-realtime',
        'qwen3-tts-flash-realtime-2025-11-27',
        'qwen-tts-realtime',
        'cosyvoice-v1',
        'cosyvoice-v1-realtime',
    ]

    for model in models:
        print(f"\n{'='*50}")
        print(f"测试模型: {model}")
        print('='*50)

        try:
            qwen_tts = QwenTtsRealtime(
                model=model,
                callback=callback,
                url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
            )

            qwen_tts.connect()
            qwen_tts.update_session(
                voice='Cherry',
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode='server_commit'
            )

            qwen_tts.append_text(TEXT)
            time.sleep(0.1)
            qwen_tts.finish()

            # 等待完成或超时
            if callback.complete_event.wait(timeout=10):
                print(f"✅ 模型 {model} 成功!")
                print(f"音频块数: {callback.audio_chunks}")
                if callback.first_audio_time:
                    delay = (callback.first_audio_time - callback.start_time) * 1000
                    print(f"首包延迟: {delay:.0f}ms")
                return model
            else:
                print(f"❌ 模型 {model} 超时")

        except Exception as e:
            print(f"❌ 模型 {model} 失败: {e}")

    return None


if __name__ == '__main__':
    print("=" * 50)
    print("Qwen TTS Realtime 模型测试")
    print("=" * 50)

    working_model = test_qwen_tts_realtime()

    print("\n" + "=" * 50)
    if working_model:
        print(f"✅ 可用模型: {working_model}")
    else:
        print("❌ 没有找到可用模型")
    print("=" * 50)
