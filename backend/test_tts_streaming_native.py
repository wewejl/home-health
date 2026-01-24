"""
真正的流式 TTS - 使用 macOS native 播放

验证流式性：边接收边写入文件，同时用 afplay 播放
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


async def test_streaming_tts_native():
    """测试流式 TTS - 边接收边写入文件"""

    print("="*60)
    print("流式 TTS 测试 - 边收边写文件")
    print("="*60)

    text = "你好，我是朱鑫烨"
    voice = "Cherry"

    print(f"\n合成文本: '{text}'")
    print(f"音色: {voice}")

    # 创建临时 PCM 文件
    temp_pcm = tempfile.mktemp(suffix=".pcm")
    temp_wav = tempfile.mktemp(suffix=".wav")

    total_bytes = 0

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
            print("[1/3] 配置会话...")

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
            print(f"\n[2/3] 发送文本: '{text}'")

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

            # 打开文件准备写入
            with open(temp_pcm, "wb") as f:
                print(f"\n[3/3] 流式接收并写入文件...")

                chunk_count = 0
                start_time = None
                first_chunk_time = None
                finished = False

                while not finished:
                    response = await ws.recv()
                    data = json.loads(response)
                    event_type = data.get("type")

                    if event_type == "response.audio.delta":
                        # 收到音频块 - 立即写入文件
                        delta = data.get("delta", "")
                        audio_data = base64.b64decode(delta)
                        chunk_count += 1

                        # 记录时间
                        if start_time is None:
                            start_time = time.time()
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                            first_packet_latency = (first_chunk_time - start_time) * 1000
                            print(f"\n   🎯 首包延迟: {first_packet_latency:.0f}ms")

                        latency = (time.time() - start_time) * 1000

                        # 立即写入文件
                        f.write(audio_data)
                        total_bytes += len(audio_data)

                        print(f"   音频块 #{chunk_count}: {len(audio_data)} bytes (T+{latency:.0f}ms) → 已写入")

                    elif event_type == "response.audio.done":
                        total_latency = (time.time() - start_time) * 1000 if start_time else 0
                        print(f"\n✅ 音频传输完成 (共 {chunk_count} 块, 总耗时 {total_latency:.0f}ms)")

                    elif event_type == "session.finished":
                        finished = True

                    elif event_type == "error":
                        error_msg = data.get("message", "未知错误")
                        print(f"❌ 错误: {error_msg}")
                        break

            print(f"\n✅ 文件写入完成: {total_bytes} bytes")

            # 转换为 WAV 格式
            print(f"\n转换 PCM → WAV...")
            import struct

            with open(temp_wav, "wb") as wav:
                # WAV 头部
                wav.write(b"RIFF")
                wav.write(struct.pack('<I', 36 + total_bytes))
                wav.write(b"WAVE")
                wav.write(b"fmt ")
                wav.write(struct.pack('<I', 16))
                wav.write(struct.pack('<H', 1))  # PCM
                wav.write(struct.pack('<H', 1))  # 单声道
                wav.write(struct.pack('<I', 24000))  # 采样率
                wav.write(struct.pack('<I', 24000 * 2))  # 字节率
                wav.write(struct.pack('<H', 2))  # 块对齐
                wav.write(struct.pack('<H', 16))  # 位深
                wav.write(b"data")
                wav.write(struct.pack('<I', total_bytes))

                # 写入音频数据
                with open(temp_pcm, "rb") as pcm:
                    wav.write(pcm.read())

            print(f"✅ WAV 文件: {temp_wav}")

            # 播放音频
            print(f"\n🔊 播放音频...")
            subprocess.run(["afplay", temp_wav])
            print(f"✅ 播放完成!")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理临时文件
        if os.path.exists(temp_pcm):
            os.remove(temp_pcm)
        if os.path.exists(temp_wav):
            # 保留 WAV 供用户播放
            final_wav = "output_streaming.wav"
            subprocess.run(["mv", temp_wav, final_wav])
            print(f"\n💾 音频已保存: {final_wav}")


if __name__ == "__main__":
    asyncio.run(test_streaming_tts_native())
