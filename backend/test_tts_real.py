"""
实际测试阿里云 Qwen TTS Realtime

验证流程：
1. 连接阿里云 WebSocket
2. 配置会话
3. 发送文本
4. 接收流式音频
5. 保存为 PCM 文件（可用于播放验证）
"""
import asyncio
import json
import base64
import os
import websockets


# 阿里云配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


async def test_tts_realtime():
    """测试 Qwen TTS Realtime"""

    print("="*60)
    print("测试阿里云 Qwen TTS Realtime")
    print("="*60)

    # 检查 API Key
    if not DASHSCOPE_API_KEY:
        print("❌ 错误: DASHSCOPE_API_KEY 环境变量未设置")
        print("   请设置: export DASHSCOPE_API_KEY='your-key'")
        return

    print(f"\n[1/6] API Key: {DASHSCOPE_API_KEY[:20]}...")

    # 要合成的文本
    text = "你好，我是朱鑫烨"
    voice = "Cherry"

    print(f"[2/6] 合成文本: '{text}'")
    print(f"      音色: {voice}")

    # 构建 WebSocket URL
    url = f"{QWEN_TTS_WS_URL}?model=qwen3-tts-flash-realtime"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "X-DashScope-DataInspection": "enable"
    }

    print(f"[3/6] 连接: {url}")

    # 收集的音频数据
    audio_chunks = []
    total_bytes = 0

    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("✅ WebSocket 已连接")

            # ===== 步骤1: session.update =====
            print("\n[4/6] 配置会话...")

            session_update = {
                "type": "session.update",
                "session": {
                    "voice": voice,
                    "response_format": "pcm",
                    "mode": "server_commit"
                }
            }
            await ws.send(json.dumps(session_update))
            print(f"   发送: session.update")

            # 等待 session.created
            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") == "session.created":
                print("   ✅ session.created")
            else:
                print(f"   ❌ 意外响应: {data.get('type')}")
                return

            # 等待 session.updated
            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") == "session.updated":
                print("   ✅ session.updated")
            else:
                print(f"   ❌ 意外响应: {data.get('type')}")

            # ===== 步骤2: 发送文本 =====
            print("\n[5/6] 发送文本...")

            text_append = {
                "type": "input_text_buffer.append",
                "text": text
            }
            await ws.send(json.dumps(text_append))
            print(f"   发送: input_text_buffer.append")

            # 短暂延迟后发送 finish
            await asyncio.sleep(0.1)

            finish = {"type": "session.finish"}
            await ws.send(json.dumps(finish))
            print(f"   发送: session.finish")

            # ===== 步骤3: 接收流式音频 =====
            print("\n[6/6] 接收流式音频...")

            chunk_count = 0
            finished = False

            while not finished:
                response = await ws.recv()

                if isinstance(response, str):
                    data = json.loads(response)
                    event_type = data.get("type")

                    if event_type == "input_text_buffer.committed":
                        print(f"   ✅ input_text_buffer.committed")

                    elif event_type == "response.audio.delta":
                        # base64 编码的音频数据
                        delta = data.get("delta", "")
                        audio_data = base64.b64decode(delta)
                        audio_chunks.append(audio_data)
                        total_bytes += len(audio_data)
                        chunk_count += 1

                        # 显示进度
                        print(f"   📦 音频块 #{chunk_count}: {len(audio_data)} bytes (总计: {total_bytes})")

                    elif event_type == "response.audio.done":
                        print(f"   ✅ response.audio.done")

                    elif event_type == "response.done":
                        print(f"   ✅ response.done")

                    elif event_type == "session.finished":
                        print(f"   ✅ session.finished")
                        finished = True

                    elif event_type == "error":
                        error_msg = data.get("message", "未知错误")
                        print(f"   ❌ 错误: {error_msg}")
                        return

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket 连接关闭: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return

    # ===== 步骤4: 保存音频文件 =====
    if audio_chunks:
        print("\n" + "="*60)
        print("合成完成！")
        print("="*60)
        print(f"   总音频块: {chunk_count}")
        print(f"   总字节数: {total_bytes}")
        print(f"   预计时长: ~{total_bytes / 48000:.2f} 秒 @ 24kHz")

        # 合并音频块
        full_audio = b"".join(audio_chunks)

        # 保存为 PCM 文件
        output_file = "output_tts.pcm"
        with open(output_file, "wb") as f:
            f.write(full_audio)

        print(f"\n✅ 已保存: {output_file}")
        print(f"   文件大小: {len(full_audio)} bytes")
        print(f"   格式: PCM, 24kHz, 单声道, 16bit")

        # 也可以保存为 WAV（添加头部）
        import struct
        wav_file = "output_tts.wav"
        with open(wav_file, "wb") as f:
            # WAV 头部
            f.write(b"RIFF")
            f.write(struct.pack('<I', 36 + len(full_audio)))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))  # PCM
            f.write(struct.pack('<H', 1))  # 单声道
            f.write(struct.pack('<I', 24000))  # 采样率
            f.write(struct.pack('<I', 24000 * 2))  # 字节率
            f.write(struct.pack('<H', 2))  # 块对齐
            f.write(struct.pack('<H', 16))  # 位深
            f.write(b"data")
            f.write(struct.pack('<I', len(full_audio)))
            f.write(full_audio)

        print(f"✅ 已保存: {wav_file}")

        print("\n播放方式:")
        print(f"  Mac/Linux: afplay {wav_file}")
        print(f"  或者: ffplay -f s16le -ar 24000 -ac 1 {output_file}")

    else:
        print("\n❌ 没有接收到音频数据")


if __name__ == "__main__":
    asyncio.run(test_tts_realtime())
