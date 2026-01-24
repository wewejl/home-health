"""
真正的流式 TTS - 边接收边播放

使用 ffplay 实现实时播放，收到音频块立即送入播放器
"""
import asyncio
import json
import base64
import os
import subprocess
import websockets


# 阿里云配置
DASHSCOPE_API_KEY = "sk-61e2b328d6614408867ac61240423740"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


class StreamPlayer:
    """流式音频播放器 - 使用 ffplay"""

    def __init__(self, sample_rate=24000, channels=1, bits_per_sample=16):
        self.sample_rate = sample_rate
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.process = None
        self.total_written = 0

    def start(self):
        """启动播放器"""
        cmd = [
            "ffplay",
            "-f", "s16le",           # PCM 16-bit little-endian
            "-ar", str(self.sample_rate),  # 采样率
            "-ac", str(self.channels),      # 声道数
            "-nodisp",               # 不显示视频窗口
            "-loglevel", "quiet",    # 安静模式
            "-"                      # 从 stdin 读取
        ]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[Player] 播放器已启动 (format: s16le, {self.sample_rate}Hz, {self.channels}ch)")

    def write(self, audio_data: bytes):
        """写入音频数据 - 立即播放"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(audio_data)
                self.process.stdin.flush()
                self.total_written += len(audio_data)
                return True
            except BrokenPipeError:
                print("[Player] 播放器管道断开")
                return False
        return False

    def stop(self):
        """停止播放器"""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=1)
            except:
                self.process.terminate()
            self.process = None
            print(f"[Player] 播放器已停止 (共写入 {self.total_written} bytes)")


async def test_streaming_tts():
    """测试流式 TTS - 边接收边播放"""

    print("="*60)
    print("流式 TTS 测试 - 边接收边播放")
    print("="*60)

    text = "你好，我是朱鑫烨"
    voice = "Cherry"

    print(f"\n合成文本: '{text}'")
    print(f"音色: {voice}")

    # 创建播放器
    player = StreamPlayer(sample_rate=24000, channels=1)

    # 构建 WebSocket URL
    url = f"{QWEN_TTS_WS_URL}?model=qwen3-tts-flash-realtime"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "X-DashScope-DataInspection": "enable"
    }

    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("\n✅ WebSocket 已连接")

            # 配置会话
            session_update = {
                "type": "session.update",
                "session": {
                    "voice": voice,
                    "response_format": "pcm",
                    "mode": "server_commit"
                }
            }
            await ws.send(json.dumps(session_update))
            print("[1/4] 配置会话...")

            # 等待 session.created
            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") != "session.created":
                print(f"❌ 意外响应: {data.get('type')}")
                return

            print("✅ 会话已创建")

            # 等待 session.updated
            await ws.recv()
            print("✅ 会话已配置")

            # 发送文本
            print(f"\n[2/4] 发送文本: '{text}'")

            text_append = {
                "type": "input_text_buffer.append",
                "text": text
            }
            await ws.send(json.dumps(text_append))

            await asyncio.sleep(0.1)

            finish = {"type": "session.finish"}
            await ws.send(json.dumps(finish))
            print("✅ 文本已发送")

            # 等待 committed
            response = await ws.recv()
            data = json.loads(response)
            if data.get("type") == "input_text_buffer.committed":
                print("✅ 文本已确认")

            # 接收流式音频并立即播放
            print(f"\n[3/4] 流式接收并播放...")

            chunk_count = 0
            first_chunk_time = None
            player_started = False
            finished = False

            while not finished:
                response = await ws.recv()
                data = json.loads(response)
                event_type = data.get("type")

                if event_type == "response.audio.delta":
                    # 收到音频块 - 立即播放
                    delta = data.get("delta", "")
                    audio_data = base64.b64decode(delta)
                    chunk_count += 1

                    # 首次收到音频时启动播放器
                    if not player_started:
                        player.start()
                        player_started = True
                        first_chunk_time = asyncio.get_event_loop().time()
                        print(f"\n[4/4] 播放中...")
                        print(f"   音频块 #1: {len(audio_data)} bytes → 开始播放")

                    # 立即写入播放器
                    player.write(audio_data)

                    if chunk_count > 1:
                        elapsed = asyncio.get_event_loop().time() - first_chunk_time
                        print(f"   音频块 #{chunk_count}: {len(audio_data)} bytes (已播放 {elapsed:.2f}s)")

                elif event_type == "response.audio.done":
                    print(f"\n✅ 音频传输完成 (共 {chunk_count} 块)")

                elif event_type == "session.finished":
                    finished = True

                elif event_type == "error":
                    error_msg = data.get("message", "未知错误")
                    print(f"❌ 错误: {error_msg}")
                    break

            # 关闭播放器
            player.stop()

            print(f"\n✅ 流式播放完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        player.stop()


if __name__ == "__main__":
    asyncio.run(test_streaming_tts())
