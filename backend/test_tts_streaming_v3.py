"""
真正的流式 TTS - 边接收边播放 (使用 FIFO)

使用命名管道 + ffplay，更可靠
"""
import asyncio
import json
import base64
import os
import subprocess
import websockets
import time
import tempfile


# 阿里云配置
DASHSCOPE_API_KEY = "sk-61e2b328d6614408867ac61240423740"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


class FIFOPlayer:
    """使用 FIFO 的流式播放器"""

    def __init__(self, sample_rate=24000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.fifo_path = None
        self.writer_fd = None
        self.process = None
        self.total_written = 0

    def start(self):
        """启动播放器"""
        # 创建临时 FIFO
        temp_dir = tempfile.gettempdir()
        self.fifo_path = os.path.join(temp_dir, "tts_stream.fifo")

        # 删除已存在的 FIFO
        if os.path.exists(self.fifo_path):
            os.remove(self.fifo_path)

        # 创建 FIFO
        os.mkfifo(self.fifo_path)
        print(f"[Player] FIFO 创建: {self.fifo_path}")

        # 启动 ffplay 读取 FIFO
        cmd = [
            "ffplay",
            "-f", "s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "-nodisp",
            "-loglevel", "quiet",
            self.fifo_path
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 打开 FIFO 用于写入 (非阻塞)
        # 需要先打开读取端，所以等一小会儿
        time.sleep(0.1)

        self.writer_fd = os.open(self.fifo_path, os.O_WRONLY | os.O_NONBLOCK)
        print(f"[Player] 播放器已启动 ({self.sample_rate}Hz, {self.channels}ch)")

    def write(self, audio_data: bytes):
        """写入音频数据"""
        if self.writer_fd is not None:
            try:
                os.write(self.writer_fd, audio_data)
                self.total_written += len(audio_data)
                return True
            except BlockingIOError:
                # FIFO 缓冲区满，稍后重试
                return False
            except OSError as e:
                print(f"[Player] 写入错误: {e}")
                return False
        return False

    def stop(self):
        """停止播放器"""
        if self.writer_fd is not None:
            try:
                os.close(self.writer_fd)
            except:
                pass
            self.writer_fd = None

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()
            self.process = None

        # 清理 FIFO
        if self.fifo_path and os.path.exists(self.fifo_path):
            try:
                os.remove(self.fifo_path)
            except:
                pass

        print(f"[Player] 播放器已停止 (共写入 {self.total_written} bytes)")


async def test_streaming_tts_v3():
    """测试流式 TTS - 使用 FIFO"""

    print("="*60)
    print("流式 TTS 测试 v3 - FIFO 方式")
    print("="*60)

    text = "你好，我是朱鑫烨"
    voice = "Cherry"

    print(f"\n合成文本: '{text}'")
    print(f"音色: {voice}")

    # 创建播放器
    player = FIFOPlayer(sample_rate=24000, channels=1)

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

                    # 首次收到音频时启动播放器
                    if not player_started:
                        player.start()
                        player_started = True
                        first_packet_latency = (time.time() - start_time) * 1000
                        print(f"\n[4/4] 播放中...")
                        print(f"   🎯 首包延迟: {first_packet_latency:.0f}ms")
                        print(f"   音频块 #{chunk_count}: {len(audio_data)} bytes")
                    else:
                        latency = (time.time() - start_time) * 1000
                        print(f"   音频块 #{chunk_count}: {len(audio_data)} bytes (T+{latency:.0f}ms)")

                    # 立即写入 FIFO
                    success = player.write(audio_data)
                    if not success:
                        print(f"   [警告] 写入 FIFO 失败")

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
    asyncio.run(test_streaming_tts_v3())
