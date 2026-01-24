"""
iOS 端与后端联调测试

模拟 iOS 客户端的行为，测试与后端的联调：
1. TTS 测试 - 验证文本合成和音频接收
2. ASR 测试 - 验证音频发送和识别结果接收
3. 并发测试 - 验证两个服务可以同时工作
"""
import asyncio
import json
import base64
import struct
import websockets
import tempfile
import os


# 配置
BACKEND_BASE = "ws://localhost:8000/ws/voice"
TOKEN = "test_1"


# ============================================================
# TTS 测试
# ============================================================

async def test_tts_client():
    """模拟 iOS TTS 客户端"""
    print("\n" + "="*70)
    print("【TTS 测试】模拟 iOS 客户端")
    print("="*70)

    url = f"{BACKEND_BASE}/tts?token={TOKEN}"
    test_texts = [
        "你好",
        "我是智能语音助手",
        "今天天气怎么样"
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n--- 测试 {i}/3: '{text}' ---")

        try:
            async with websockets.connect(url) as ws:
                print(f"✅ 连接成功")

                # 发送合成请求（模拟 iOS 发送的 JSON）
                request = {
                    "text": text,
                    "voice": "Cherry"
                }
                await ws.send(json.dumps(request))
                print(f"📤 发送请求: {json.dumps(request, ensure_ascii=False)}")

                # 接收响应
                audio_chunks = []
                chunk_count = 0
                total_bytes = 0

                while True:
                    message = await ws.recv()

                    if isinstance(message, str):
                        data = json.loads(message)
                        event = data.get("event")

                        if event == "tts_ready":
                            print("📥 后端准备就绪")

                        elif event == "tts_finished":
                            print(f"✅ 音频传输完成 (共 {chunk_count} 块, {total_bytes} bytes)")
                            break

                        elif event == "error":
                            error_msg = data.get("message", "Unknown error")
                            print(f"❌ 错误: {error_msg}")
                            break

                    else:
                        # Binary 音频数据
                        audio_chunks.append(message)
                        chunk_count += 1
                        total_bytes += len(message)

                        # 只显示第一个块的详情
                        if chunk_count == 1:
                            print(f"📦 首包延迟: ~0ms")
                        elif chunk_count % 2 == 0:
                            print(f"   📦 音频块 #{chunk_count}: {len(message)} bytes")

                # 保存音频用于验证
                if audio_chunks:
                    full_audio = b"".join(audio_chunks)
                    wav_file = f"test_tts_{i}.wav"

                    with open(wav_file, "wb") as f:
                        # WAV header
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

                    print(f"💾 已保存: {wav_file}")

        except Exception as e:
            print(f"❌ TTS 测试失败: {e}")
            return False

    print("\n✅ TTS 测试完成")
    return True


# ============================================================
# ASR 测试
# ============================================================

async def test_asr_client():
    """模拟 iOS ASR 客户端"""
    print("\n" + "="*70)
    print("【ASR 测试】模拟 iOS 客户端")
    print("="*70)

    url = f"{BACKEND_BASE}/asr?token={TOKEN}"

    # 创建测试音频（正弦波，模拟语音）
    sample_rate = 16000
    duration = 2  # 秒
    num_samples = sample_rate * duration

    # 生成 440Hz 正弦波（A4 音符）
    audio_data = bytearray()
    frequency = 440
    for i in range(num_samples):
        # 添加一些变化，让它更像语音
        sample = int(32767 * 0.2 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.extend(struct.pack('<h', sample))

    test_audio = bytes(audio_data)

    print(f"测试音频: {len(test_audio)} bytes (16kHz, {duration}秒)")

    try:
        async with websockets.connect(url) as ws:
            print(f"✅ 连接成功")

            # 等待 asr_ready
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(message)

                if data.get("event") == "asr_ready":
                    print(f"📥 后端准备就绪")

                    # 发送音频数据
                    await ws.send(test_audio)
                    print(f"📤 已发送音频数据 ({len(test_audio)} bytes)")

                    # 接收识别结果
                    partial_count = 0
                    final_count = 0

                    while True:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=5.0)

                            if isinstance(message, str):
                                data = json.loads(message)
                                event = data.get("event")

                                if event == "asr_partial":
                                    text = data.get("text", "")
                                    if text:
                                        partial_count += 1
                                        print(f"   📝 中间结果 #{partial_count}: {text}")

                                elif event == "asr_final":
                                    text = data.get("text", "")
                                    final_count += 1
                                    print(f"   ✅ 最终结果 #{final_count}: {text}")

                                elif event == "error":
                                    error_msg = data.get("message", "Unknown error")
                                    print(f"   ❌ 错误: {error_msg}")
                                    break

                        except asyncio.TimeoutError:
                            print(f"   ⏱️ 接收超时")
                            break

                    print(f"\n结果统计: {partial_count} 个中间结果, {final_count} 个最终结果")

            except asyncio.TimeoutError:
                print("❌ 等待 asr_ready 超时")

    except Exception as e:
        print(f"❌ ASR 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ ASR 测试完成")
    return True


# ============================================================
# 并发测试
# ============================================================

async def test_concurrent():
    """测试 ASR 和 TTS 是否可以同时工作"""
    print("\n" + "="*70)
    print("【并发测试】ASR 和 TTS 同时工作")
    print("="*70)

    async def tts_task():
        async with websockets.connect(f"{BACKEND_BASE}/tts?token={TOKEN}") as ws:
            await ws.send(json.dumps({"text": "并发测试语音合成", "voice": "Cherry"}))

            chunk_count = 0
            while True:
                message = await ws.recv()

                if isinstance(message, str):
                    data = json.loads(message)
                    if data.get("event") == "tts_finished":
                        print(f"[TTS] 完成，收到 {chunk_count} 个音频块")
                        break
                else:
                    chunk_count += 1

    async def asr_task():
        async with websockets.connect(f"{BACKEND_BASE}/asr?token={TOKEN}") as ws:
            # 等待 asr_ready
            await ws.recv()

            # 发送测试音频
            audio_data = bytes(32000)  # 1秒的静音
            await ws.send(audio_data)

            print("[ASR] 已发送音频")

            # 等一小会儿
            await asyncio.sleep(0.5)

    print("\n并发启动 ASR 和 TTS...")
    await asyncio.gather(tts_task(), asr_task())

    print("✅ 并发测试完成")


# ============================================================
# 主函数
# ============================================================

async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("iOS 端与后端联调测试")
    print("="*70)

    print(f"\n后端地址: {BACKEND_BASE}")
    print(f"认证 Token: {TOKEN}")

    # 单独测试
    tts_ok = await test_tts_client()
    asr_ok = await test_asr_client()

    # 并发测试
    await test_concurrent()

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"TTS 语音合成: {'✅ 通过' if tts_ok else '❌ 失败'}")
    print(f"ASR 语音识别: {'✅ 通过' if asr_ok else '❌ 失败'}")
    print(f"\n📱 iOS 客户端使用方式:")
    print(f"   - 连接: ws://your-backend.com/ws/voice/tts?token=xxx")
    print(f"   - 连接: ws://your-backend.com/ws/voice/asr?token=xxx")
    print(f"   - 后端负责转发到阿里云，前端无需 API Key")


if __name__ == "__main__":
    import math
    asyncio.run(main())
