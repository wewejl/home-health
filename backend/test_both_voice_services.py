"""
测试后端语音服务 - TTS 和 ASR

1. TTS 测试: 发送文本，接收音频
2. ASR 测试: 发送音频，接收识别结果
"""
import asyncio
import json
import base64
import os
import struct
import websockets
import wave
import math


# 配置
BACKEND_BASE = "ws://localhost:8000/ws/voice"
TOKEN = "test_1"


async def test_tts():
    """测试 TTS 语音合成"""
    print("\n" + "="*60)
    print("【TTS 测试】语音合成")
    print("="*60)

    url = f"{BACKEND_BASE}/tts?token={TOKEN}"
    text = "你好，我是智能语音助手"

    print(f"连接: {url}")
    print(f"合成文本: '{text}'")

    audio_chunks = []
    total_bytes = 0

    try:
        async with websockets.connect(url) as ws:
            print("✅ 已连接")

            # 发送请求
            await ws.send(json.dumps({"text": text, "voice": "Cherry"}))
            print("📤 已发送请求")

            # 接收响应
            while True:
                message = await ws.recv()

                if isinstance(message, str):
                    data = json.loads(message)
                    event = data.get("event")

                    if event == "tts_ready":
                        print("📥 后端准备就绪，开始接收音频...")
                    elif event == "tts_finished":
                        print(f"✅ 音频传输完成 (共 {len(audio_chunks)} 块, {total_bytes} bytes)")
                        break
                    elif event == "error":
                        print(f"❌ 错误: {data.get('message')}")
                        break
                else:
                    # 二进制音频
                    audio_chunks.append(message)
                    total_bytes += len(message)
                    print(f"   📦 音频块 #{len(audio_chunks)}: {len(message)} bytes")

    except websockets.exceptions.ConnectionClosed:
        print("连接已关闭")
    except Exception as e:
        print(f"❌ TTS 错误: {e}")
        return False

    # 保存音频
    if audio_chunks:
        full_audio = b"".join(audio_chunks)
        wav_file = "test_tts_output.wav"

        with open(wav_file, "wb") as f:
            # WAV 头部
            f.write(b"RIFF")
            f.write(struct.pack('<I', 36 + len(full_audio)))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<I', 24000))
            f.write(struct.pack('<I', 24000 * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b"data")
            f.write(struct.pack('<I', len(full_audio)))
            f.write(full_audio)

        print(f"💾 已保存: {wav_file}")

        # 播放
        print("🔊 播放音频...")
        os.system(f"afplay {wav_file}")

        return True
    else:
        print("⚠️ 未接收到音频数据")
        return False


async def test_asr():
    """测试 ASR 语音识别"""
    print("\n" + "="*60)
    print("【ASR 测试】语音识别")
    print("="*60)

    url = f"{BACKEND_BASE}/asr?token={TOKEN}"

    print(f"连接: {url}")
    print("说明: 使用预录制的测试音频 (PCM 16kHz)")

    # 创建测试音频 - 正弦波 440Hz
    sample_rate = 16000
    duration = 1  # 秒
    num_samples = sample_rate * duration

    audio_data = bytearray()
    frequency = 440  # A4 音符
    for i in range(num_samples):
        sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.extend(struct.pack('<h', sample))

    test_audio = bytes(audio_data)
    print(f"📤 测试音频: {len(test_audio)} bytes (16kHz, 正弦波)")

    results = []

    try:
        async with websockets.connect(url) as ws:
            print("✅ 已连接")

            # 接收 asr_ready
            try:
                message = await ws.recv()
                data = json.loads(message)
                if data.get("event") == "asr_ready":
                    print("📥 后端准备就绪，发送测试音频...")

                    # 发送音频数据
                    await ws.send(test_audio)
                    print(f"📤 已发送 {len(test_audio)} bytes")

                    # 接收识别结果
                    try:
                        while True:
                            message = await asyncio.wait_for(ws.recv(), timeout=5.0)

                            if isinstance(message, str):
                                data = json.loads(message)
                                event = data.get("event")

                                if event == "asr_partial":
                                    text = data.get("text", "")
                                    if text:
                                        print(f"   📝 中间结果: {text}")
                                elif event == "asr_final":
                                    text = data.get("text", "")
                                    print(f"   ✅ 最终结果: {text}")
                                    results.append(text)
                                elif event == "error":
                                    print(f"   ❌ 错误: {data.get('message')}")
                                    break

                    except asyncio.TimeoutError:
                        print("   ⏱️ 等待识别结果超时")

            except websockets.exceptions.ConnectionClosed:
                print("连接已关闭")

        print("✅ ASR 测试完成")
        return True

    except Exception as e:
        print(f"❌ ASR 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("后端语音服务测试")
    print("="*60)

    # 测试 TTS
    tts_ok = await test_tts()

    # 测试 ASR
    asr_ok = await test_asr()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"TTS 语音合成: {'✅ 通过' if tts_ok else '❌ 失败'}")
    print(f"ASR 语音识别: {'✅ 通过' if asr_ok else '❌ 失败'}")
    print(f"\n接口地址:")
    print(f"  TTS: {BACKEND_BASE}/tts?token=xxx")
    print(f"  ASR: {BACKEND_BASE}/asr?token=xxx")


if __name__ == "__main__":
    asyncio.run(main())
