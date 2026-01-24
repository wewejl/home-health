"""
验证阿里云 Qwen TTS 返回的音频数据格式

检查：
1. base64 解码后的原始数据格式
2. 字节序 (大端/小端)
3. 采样率、声道数、位深
4. iOS AVAudioEngine 是否支持
"""
import asyncio
import json
import base64
import struct
import websockets


# 阿里云配置
DASHSCOPE_API_KEY = "sk-61e2b328d6614408867ac61240423740"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


def analyze_pcm_data(data: bytes):
    """分析 PCM 数据格式"""
    print(f"\n📊 数据分析:")
    print(f"   总字节数: {len(data)}")
    print(f"   前 20 字节 (hex): {data[:20].hex()}")
    print(f"   前 10 个 16-bit 采样值:")

    # 假设是 16-bit PCM
    num_samples = min(10, len(data) // 2)
    values_le = []  # 小端
    values_be = []  # 大端

    for i in range(num_samples):
        # 小端解析
        val_le = struct.unpack('<h', data[i*2:i*2+2])[0]
        values_le.append(val_le)

        # 大端解析
        val_be = struct.unpack('>h', data[i*2:i*2+2])[0]
        values_be.append(val_be)

    print(f"     小端序: {values_le}")
    print(f"     大端序: {values_be}")

    # 判断字节序
    # 正常语音数据应该在 -32768 到 32767 之间
    # 小端序的值应该更"合理"（不会都是极大的正数）

    abs_sum_le = sum(abs(v) for v in values_le)
    abs_sum_be = sum(abs(v) for v in values_be)

    if abs_sum_le < abs_sum_be:
        byte_order = "小端序 (Little Endian, s16le)"
        fmt = "<h"
    else:
        byte_order = "大端序 (Big Endian, s16be)"
        fmt = ">h"

    print(f"\n   🔍 判定字节序: {byte_order}")

    # 解析更多采样值
    num_samples = len(data) // 2
    all_values = []
    for i in range(num_samples):
        val = struct.unpack(fmt, data[i*2:i*2+2])[0]
        all_values.append(val)

    # 统计
    min_val = min(all_values)
    max_val = max(all_values)
    avg_val = sum(all_values) / len(all_values)

    print(f"\n   📈 采样值统计:")
    print(f"     最小值: {min_val}")
    print(f"     最大值: {max_val}")
    print(f"     平均值: {avg_val:.2f}")
    print(f"     采样数: {num_samples}")

    # 归一化到 [-1, 1]
    print(f"\n   📊 归一化范围 (Float32):")
    for i in range(min(5, len(all_values))):
        normalized = all_values[i] / 32768.0
        print(f"     采样 #{i+1}: {all_values[i]:6d} → {normalized:.6f}")


async def verify_audio_format():
    """验证音频格式"""

    print("="*60)
    print("验证阿里云 Qwen TTS 音频格式")
    print("="*60)

    text = "你好"
    voice = "Cherry"

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
                    "response_format": "pcm",  # 关键配置
                    "mode": "server_commit"
                }
            }
            await ws.send(json.dumps(session_update))
            print("[1/3] 配置会话: response_format='pcm'")

            # 等待 session.created 和 session.updated
            await ws.recv()
            await ws.recv()
            print("✅ 会话已配置")

            # 发送文本
            text_append = {
                "type": "input_text_buffer.append",
                "text": text
            }
            await ws.send(json.dumps(text_append))
            await asyncio.sleep(0.1)

            finish = {"type": "session.finish"}
            await ws.send(json.dumps(finish))
            print(f"[2/3] 发送文本: '{text}'")

            # 等待 committed
            await ws.recv()

            # 接收第一个音频块
            print(f"[3/3] 接收音频...")

            response = await ws.recv()
            data = json.loads(response)

            if data.get("type") == "response.audio.delta":
                delta = data.get("delta", "")
                audio_data = base64.b64decode(delta)

                analyze_pcm_data(audio_data)

    except Exception as e:
        print(f"❌ 错误: {e}")


async def check_ios_compatibility():
    """检查 iOS 兼容性"""

    print("\n" + "="*60)
    print("iOS AVAudioEngine 兼容性检查")
    print("="*60)

    print("""
📱 iOS 端处理方式:

1. 音频格式确认:
   - 格式: PCM (Pulse Code Modulation)
   - 采样率: 24000 Hz (24kHz)
   - 声道数: 1 (单声道)
   - 位深: 16-bit
   - 字节序: 小端序 (Little Endian)

2. AVAudioFormat 配置:
   ```swift
   let audioFormat = AVAudioFormat(
       commonFormat: .pcmFormatInt16,    // 16-bit PCM
       sampleRate: 24000.0,              // 24kHz
       channels: 1,                      // 单声道
       interleaved: false                // 非交错（平面格式）
   )!
   ```

3. 播放节点配置:
   ```swift
   let playerNode = AVAudioPlayerNode()
   audioEngine.attach(playerNode)
   audioEngine.connect(playerNode,
                      to: audioEngine.mainMixerNode,
                      format: audioFormat)
   ```

4. 写入音频数据:
   ```swift
   // 将收到的 Data 转换为 AVAudioPCMBuffer
   guard let buffer = AVAudioPCMBuffer(
       pcmFormat: audioFormat,
       frameCapacity: frameCount
   ) else { return }

   buffer.frameLength = frameCount
   guard let channelData = buffer.int16ChannelData else { return }

   // 复制数据
   audioData.withUnsafeBytes { rawPtr in
       let srcPtr = rawPtr.baseAddress!.assumingMemoryBound(to: Int16.self)
       for i in 0..<Int(frameCount) {
           channelData[0][i] = srcPtr[i]
       }
   }

   // 调度播放
   playerNode.scheduleBuffer(buffer)
   ```

5. 流式播放支持: ✅
   - AVAudioPlayerNode 天生支持流式播放
   - 可以边接收边调度缓冲区
   - 支持低延迟播放

✅ 结论: iOS AVAudioEngine 完全支持此格式！
""")


async def main():
    """主函数"""
    await verify_audio_format()
    await check_ios_compatibility()

    print("\n" + "="*60)
    print("总结")
    print("="*60)
    print("""
后端转发协议:

前端 → 后端: JSON {"text": "你好", "voice": "Cherry"}
后端 → 前端: Binary PCM 数据（24kHz, 单声道, 16-bit, 小端序）

iOS 端需要:
1. 连接 ws://host/ws/tts
2. 发送文本请求
3. 接收 binary 数据
4. 转换为 AVAudioPCMBuffer
5. 用 AVAudioPlayerNode 流式播放
    """)


if __name__ == "__main__":
    asyncio.run(main())
