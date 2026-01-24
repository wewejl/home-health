"""
测试 Qwen TTS Realtime - 检查模型参数传递方式
"""
import os
import websockets
import json
import base64
import asyncio

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-61e2b328d6614408867ac61240423740")
TEXT = "你好你好"

async def test_with_url_params():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "X-DashScope-DataInspection": "enable"
    }

    # 尝试在 URL 中添加模型参数
    url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-tts-flash-realtime"

    print(f"连接 URL: {url}")

    async with websockets.connect(url, additional_headers=headers) as ws:
        print("✓ WebSocket 已连接")

        # 等待 session.created
        msg = await asyncio.wait_for(ws.recv(), timeout=2)
        data = json.loads(msg)
        print(f"\n[收到] {json.dumps(data, ensure_ascii=False, indent=2)}")

        if data.get('type') == 'session.created':
            print(f"✓ session 模型: {data['session'].get('model')}")

        # 发送 session.update
        session_update = {
            "type": "session.update",
            "session": {
                "voice": "Cherry",
                "response_format": "pcm",  # 简化为 "pcm"
                "mode": "server_commit"
            }
        }
        await ws.send(json.dumps(session_update))
        print(f"\n[发送] session.update")

        # 等待 session.updated
        msg = await asyncio.wait_for(ws.recv(), timeout=2)
        data = json.loads(msg)
        print(f"\n[收到] {json.dumps(data, ensure_ascii=False, indent=2)}")

        # 发送文本
        append_text = {
            "type": "input_text_buffer.append",
            "text": TEXT
        }
        await ws.send(json.dumps(append_text))
        print(f"\n[发送] input_text_buffer.append")

        # 发送 finish
        finish = {
            "type": "session.finish"
        }
        await ws.send(json.dumps(finish))
        print(f"\n[发送] session.finish")

        # 接收音频
        audio_count = 0
        for _ in range(20):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                data = json.loads(msg)

                if data.get('type') == 'response.audio.delta':
                    audio_count += 1
                    b64 = data.get('delta', '')
                    audio_data = base64.b64decode(b64)
                    print(f"  音频块: {len(audio_data)} bytes")

                elif data.get('type') == 'session.finished':
                    print(f"\n✓ session.finished")
                    break

                elif data.get('type') == 'error':
                    print(f"\n✗ Error: {data}")
                    break

            except asyncio.TimeoutError:
                break

        print(f"\n音频块数: {audio_count}")


if __name__ == '__main__':
    asyncio.run(test_with_url_params())
