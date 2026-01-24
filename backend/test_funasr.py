"""
测试阿里云 FunASR API 连接
"""
import asyncio
import os
import websockets
import json
import uuid

# API Key
API_KEY = "sk-61e2b328d6614408867ac61240423740"
WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"


async def test_funasr():
    """测试 FunASR 连接"""
    task_id = uuid.uuid4().hex[:32]

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    print(f"[FunASR] 正在连接阿里云...")
    print(f"[FunASR] Task ID: {task_id}")

    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            print("[FunASR] ✅ WebSocket 连接成功!")

            # 发送 run-task 指令
            run_task = {
                "header": {
                    "action": "run-task",
                    "task_id": task_id,
                    "streaming": "duplex"
                },
                "payload": {
                    "task_group": "audio",
                    "task": "asr",
                    "function": "recognition",
                    "model": "fun-asr-realtime",
                    "parameters": {
                        "format": "pcm",
                        "sample_rate": 16000,
                        "semantic_punctuation_enabled": False,  # VAD 断句
                        "max_sentence_silence": 1300
                    },
                    "input": {}
                }
            }

            await ws.send(json.dumps(run_task))
            print("[FunASR] 已发送 run-task 指令")

            # 等待响应
            timeout = 10
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                data = json.loads(response)
                event = data.get("header", {}).get("event")

                print(f"[FunASR] 收到事件: {event}")

                if event == "task-started":
                    print("[FunASR] ✅ 任务启动成功!")
                    print("[FunASR] 内置 FSMN-VAD 语音活动检测已启用")
                    print("[FunASR] max_sentence_silence: 1300ms (VAD 静音阈值)")

                    # 发送 finish-task
                    finish_task = {
                        "header": {
                            "action": "finish-task",
                            "task_id": task_id,
                            "streaming": "duplex"
                        },
                        "payload": {"input": {}}
                    }
                    await ws.send(json.dumps(finish_task))
                    print("[FunASR] 已发送 finish-task 指令")

                elif event == "task-finished":
                    print("[FunASR] ✅ 任务完成!")
                    break

                elif event == "task-failed":
                    error = data.get("header", {}).get("error_message", "未知错误")
                    print(f"[FunASR] ❌ 任务失败: {error}")
                    break

            print("\n[FunASR] 测试完成!")

    except Exception as e:
        print(f"[FunASR] ❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_funasr())
