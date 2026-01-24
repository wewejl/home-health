"""
真正的流式 TTS - 边接收边播放 (最终版)

策略: 先收集 2-3 个音频块作为缓冲，然后边收边播放
"""
import asyncio
import json
import base64
import os
import subprocess
import websockets
import time


# 阿里云配置
DASHSCOPE_API_KEY = "sk-61e2b328d6614408867ac61240423740"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


class PreBufferedPlayer:
    """预缓冲流式播放器"""

    def __init__(self, sample_rate=24000, channels=1, pre_buffer_chunks=2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.pre_buffer_chunks = pre_buffer_chunks
        self.buffer = []
        self.process = None
        self.total_written = 0
        self.started = False

    def write(self, audio_data: bytes) -> bool:
        """写入音频数据"""
        # 如果还没启动，先缓冲
        if not self.started:
            self.buffer.append(audio_data)
            print(f"[Player] 缓冲中... {len(self.buffer)}/{self.pre_buffer_chunks} 块")

            # 达到预缓冲数量，启动播放器
            if len(self.buffer) >= self.pre_buffer_chunks:
                return self._start_playing()
            return True
        else:
            # 已启动，直接写入
            return self._write_to_player(audio_data)

    def _start_playing(self) -> bool:
        """启动播放器并写入缓冲数据"""
        cmd = [
            "ffplay",
            "-f", "s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "-nodisp",
            "-loglevel", "quiet",
            "-"
        ]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self.started = True
        print(f"[Player] ▶️ 播放器已启动，写入缓冲的 {len(self.buffer)} 块...")

        # 写入缓冲数据
        for data in self.buffer:
            if not self._write_to_player(data):
                return False

        self.buffer = []
        return True

    def _write_to_player(self, audio_data: bytes) -> bool:
        """写入到播放器"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(audio_data)
                self.process.stdin.flush()
                self.total_written += len(audio_data)
                return True
            except BrokenPipeError:
                print("[Player] ❌ 管道断开")
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


async def test_streaming_tts_final():
    """测试流式 TTS - 预缓冲方式"""

    print("="*60)
    print("流式 TTS 测试 - 预缓冲方式")
    print("="*60)

    text = "你好，我是朱鑫烨"
    voice = "Cherry"

    print(f"\n合成文本: '{text}'")
    print(f"音色: {voice}")

    # 创建播放器 (预缓冲 2 块)
    player = PreBufferedPlayer(sample_rate=24000, channels=1, pre_buffer_chunks=2)

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
            start_time = None
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

                    # 记录首包延迟
                    if start_time is None:
                        start_time = time.time()

                    # 记录播放器启动时间
                    if not player_started and player.started:
                        player_started = True
                        first_play_latency = (time.time() - start_time) * 1000
                        print(f"\n[4/4] 🔊 开始播放!")
                        print(f"   🎯 首包延迟: {first_play_latency:.0f}ms")

                    latency = (time.time() - start_time) * 1000

                    # 立即写入播放器
                    player.write(audio_data)

                    if player_started:
                        print(f"   音频块 #{chunk_count}: {len(audio_data)} bytes (T+{latency:.0f}ms)")

                elif event_type == "response.audio.done":
                    total_latency = (time.time() - start_time) * 1000 if start_time else 0
                    print(f"\n✅ 音频传输完成 (共 {chunk_count} 块, 总耗时 {total_latency:.0f}ms)")

                elif event_type == "session.finished":
                    finished = True

                elif event_type == "error":
                    error_msg = data.get("message", "未知错误")
                    print(f"❌ 错误: {error_msg}")
                    break

            # 等待播放完成
            print(f"\n等待播放完成...")
            estimated_duration = player.total_written / 2 / 24000
            await asyncio.sleep(estimated_duration + 0.5)

            # 关闭播放器
            player.stop()

            print(f"\n✅ 流式播放完成！")
            print(f"   音频数据: {player.total_written} bytes")
            print(f"   预计时长: {estimated_duration:.2f} 秒")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        player.stop()


if __name__ == "__main__":
    asyncio.run(test_streaming_tts_final())
