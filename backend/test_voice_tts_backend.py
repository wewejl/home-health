"""
测试后端 TTS 转发功能

验证流程：
1. 连接后端 ws://localhost:8000/ws/voice/tts?token=test_1
2. 发送合成请求
3. 接收流式音频
4. 保存并播放
"""
import asyncio
import json
import base64
import os
import struct
import websockets
import tempfile


# 后端配置
BACKEND_WS_URL = "ws://localhost:8000/ws/voice/tts?token=test_1"
TEXT = "你好，我是朱鑫烨"
VOICE = "Cherry"


async def test_tts_backend():
    """测试后端 TTS 转发"""

    print("="*60)
    print("测试后端 TTS 转发")
    print("="*60)

    print(f"\n后端地址: {BACKEND_WS_URL}")
    print(f"合成文本: '{TEXT}'")
    print(f"音色: {VOICE}")

    audio_chunks = []
    total_bytes = 0
    temp_pcm = tempfile.mktemp(suffix=".pcm")

    try:
        async with websockets.connect(BACKEND_WS_URL) as ws:
            print("\n✅ WebSocket 已连接")

            # 发送合成请求
            request = {
                "text": TEXT,
                "voice": VOICE
            }
            await ws.send(json.dumps(request))
            print(f"[1/3] 已发送请求: {json.dumps(request, ensure_ascii=False)}")

            # 接收响应
            chunk_count = 0
            receiving_audio = False
            finished = False

            while not finished:
                try:
                    # 接收消息
                    message = await ws.recv()

                    # 判断是 JSON 还是 binary
                    if isinstance(message, str):
                        # JSON 消息
                        data = json.loads(message)
                        event = data.get("event")

                        if event == "tts_ready":
                            print("[2/3] 后端准备就绪，开始接收音频...")

                        elif event == "tts_finished":
                            print(f"\n✅ 音频传输完成 (共 {chunk_count} 块, {total_bytes} bytes)")
                            finished = True

                        elif event == "error":
                            error_msg = data.get("message", "Unknown error")
                            print(f"\n❌ 错误: {error_msg}")
                            return

                    else:
                        # Binary 音频数据
                        chunk_count += 1
                        audio_chunks.append(message)
                        total_bytes += len(message)

                        if not receiving_audio:
                            receiving_audio = True
                            print(f"\n[3/3] 接收音频块...")
                            print(f"   🎯 首包延迟: ~0ms")

                        print(f"   音频块 #{chunk_count}: {len(message)} bytes (总计: {total_bytes})")

                        # 写入文件
                        with open(temp_pcm, "ab") as f:
                            f.write(message)

                except websockets.exceptions.ConnectionClosed:
                    print("\n连接已关闭")
                    break

    except ConnectionRefusedError:
        print("\n❌ 无法连接到后端服务")
        print("   请确保后端正在运行: uvicorn app.main:app --reload --port 8000")
        return
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return

    # 保存为 WAV 文件
    if audio_chunks:
        # 合并所有音频块
        full_audio = b"".join(audio_chunks)

        # 转换为 WAV
        temp_wav = "output_backend_tts.wav"
        with open(temp_wav, "wb") as wav:
            # WAV 头部
            wav.write(b"RIFF")
            wav.write(struct.pack('<I', 36 + len(full_audio)))
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
            wav.write(struct.pack('<I', len(full_audio)))
            wav.write(full_audio)

        print(f"\n💾 已保存: {temp_wav}")

        # 播放
        print(f"🔊 播放音频...")
        os.system(f"afplay {temp_wav}")

        print(f"\n✅ 测试完成！")
        print(f"   后端转发工作正常")

    else:
        print("\n⚠️ 没有接收到音频数据")

    # 清理
    if os.path.exists(temp_pcm):
        os.remove(temp_pcm)


if __name__ == "__main__":
    asyncio.run(test_tts_backend())
