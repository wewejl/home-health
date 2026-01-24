"""
测试阿里云 CosyVoice TTS API
使用正确的协议流程，完全模拟 iOS 的实现
"""
import asyncio
import websockets
import json
import os

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-61e2b328d6614408867ac61240423740")
URI = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
TEXT = "你好"

async def test_tts():
    print(f"API Key: {API_KEY[:20]}...")
    print(f"测试文本: '{TEXT}'")
    print(f"正在连接 {URI}...")

    # 正确的认证方式：通过 extra_headers 发送 Authorization
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-DashScope-DataInspection": "enable"
    }

    try:
        async with websockets.connect(URI, additional_headers=headers) as ws:
            print("✓ WebSocket 已连接")

            task_id = "test-tts-001"

            # 1. 发送 run-task
            run_task = {
                "header": {
                    "action": "run-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": "cosyvoice-v3-flash",
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": "longanyang",
                        "format": "mp3",
                        "sample_rate": 22050
                    },
                    "input": {}
                }
            }

            await ws.send(json.dumps(run_task))
            print("✓ run-task 已发送")

            # 2. 等待 task-started
            task_started = False
            for _ in range(50):
                msg = await asyncio.wait_for(ws.recv(), timeout=0.2)
                if isinstance(msg, str):
                    data = json.loads(msg)
                    event = data.get("header", {}).get("event", "")
                    if event == "task-started":
                        task_started = True
                        print("✓ task-started 收到")
                        break
                    elif event == "error":
                        print(f"✗ 错误: {data}")
                        return False

            if not task_started:
                print("✗ 未收到 task-started")
                return False

            # 3. 发送 continue-task（包含文本）
            continue_task = {
                "header": {
                    "action": "continue-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "input": {
                        "text": TEXT
                    }
                }
            }

            await ws.send(json.dumps(continue_task))
            print(f"✓ continue-task 已发送，文本: '{TEXT}'")

            # 4. 发送 finish-task
            await asyncio.sleep(0.1)  # 短暂延迟
            finish_task = {
                "header": {
                    "action": "finish-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "input": {}
                }
            }

            await ws.send(json.dumps(finish_task))
            print("✓ finish-task 已发送")

            # 5. 接收音频数据
            audio_data = bytearray()
            task_finished = False

            for _ in range(100):  # 最多等10秒
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.1)

                    if isinstance(msg, bytes):
                        # 音频数据
                        audio_data.extend(msg)
                        print(f"  收到音频块: {len(msg)} bytes (总计: {len(audio_data)})")

                    elif isinstance(msg, str):
                        data = json.loads(msg)
                        event = data.get("header", {}).get("event", "")

                        if event == "task-finished":
                            task_finished = True
                            print("✓ task-finished 收到")

                        elif event == "error":
                            print(f"✗ 错误: {data}")
                            return False

                except asyncio.TimeoutError:
                    if task_finished:
                        break

            print(f"\n========== 结果 ==========")
            print(f"任务启动: {'✓' if task_started else '✗'}")
            print(f"任务完成: {'✓' if task_finished else '✗'}")
            print(f"音频数据: {len(audio_data)} bytes ({len(audio_data)//1024} KB)")
            print(f"状态: {'✅ 成功' if len(audio_data) > 0 else '❌ 失败'}")

            # 保存音频文件
            if len(audio_data) > 0:
                output_file = "/tmp/test_tts.mp3"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                print(f"音频已保存到: {output_file}")

            return len(audio_data) > 0

    except websockets.exceptions.InvalidStatus as e:
        print(f"✗ 连接失败 (HTTP {e.status_code}):")
        print(f"   请检查 API Key")
        print(f"   可能原因: API Key 已过期、被禁用或格式不正确")
        return False
    except Exception as e:
        print(f"✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("CosyVoice TTS API 测试")
    print("=" * 50)

    success = asyncio.run(test_tts())

    print("\n" + "=" * 50)
    if success:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
    print("=" * 50)
