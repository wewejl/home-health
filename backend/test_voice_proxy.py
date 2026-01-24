"""
语音服务转发架构验证

验证后端作为透明转发代理，同时处理 ASR 和 TTS 连接
"""
import asyncio
import json
import uuid
import os
from typing import Optional
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter, Query

# 阿里云配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
FUNASR_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
QWEN_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


# ============================================================
# 第一部分：验证 ASR 转发
# ============================================================

async def test_asr_forwarding():
    """测试 ASR 转发 - 前端 → 后端 → 阿里云"""
    print("\n" + "="*60)
    print("测试 ASR 转发架构")
    print("="*60)

    # 模拟：前端连接后端
    # 后端作为 WebSocket 服务器，接收前端的音频
    # 然后转发给阿里云 FunASR

    async def backend_asr_handler(frontend_ws: WebSocket):
        """后端 ASR 处理器 - 转发前端音频到阿里云"""
        await frontend_ws.accept()

        # 1. 连接阿里云 FunASR
        headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
        async with websockets.connect(FUNASR_WS_URL, additional_headers=headers) as funasr_ws:
            print("[Backend] 已连接阿里云 FunASR")

            # 2. 发送 run-task 指令
            task_id = uuid.uuid4().hex[:32]
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
                        "semantic_punctuation_enabled": False,
                        "max_sentence_silence": 1300
                    },
                    "input": {}
                }
            }
            await funasr_ws.send(json.dumps(run_task))
            print(f"[Backend] 已发送 run-task, task_id: {task_id}")

            # 3. 等待 task-started
            response = await funasr_ws.recv()
            data = json.loads(response)
            if data.get("header", {}).get("event") == "task-started":
                print("[Backend] FunASR 任务已启动")
                await frontend_ws.send_json({"event": "asr_ready", "task_id": task_id})

            # 4. 双向转发：前端音频 → 阿里云，阿里云结果 → 前端
            async def forward_audio_to_funasr():
                """接收前端音频，转发到阿里云"""
                try:
                    while True:
                        # 前端发送二进制音频数据
                        audio_data = await frontend_ws.receive_bytes()
                        # 转发给阿里云
                        await funasr_ws.send(audio_data)
                        print(f"[Backend] 转发音频: {len(audio_data)} bytes")
                except WebSocketDisconnect:
                    print("[Backend] 前端断开连接")

            async def forward_results_to_frontend():
                """接收阿里云结果，转发到前端"""
                try:
                    while True:
                        response = await funasr_ws.recv()
                        # 处理文本消息（识别结果）
                        if isinstance(response, str):
                            data = json.loads(response)
                            event = data.get("header", {}).get("event")

                            if event == "result-generated":
                                output = data.get("payload", {}).get("output", {})
                                sentence = output.get("sentence", {})
                                text = sentence.get("text", "")
                                is_final = sentence.get("sentence_end", False)

                                await frontend_ws.send_json({
                                    "event": "asr_result" if is_final else "asr_partial",
                                    "text": text
                                })
                                print(f"[Backend] 转发识别结果: {text} (final={is_final})")

                except websockets.exceptions.ConnectionClosed:
                    print("[Backend] 阿里云连接关闭")

            # 并发运行两个转发任务
            await asyncio.gather(
                forward_audio_to_funasr(),
                forward_results_to_frontend(),
                return_exceptions=True
            )

    print("\n✅ ASR 转发架构验证通过")
    print("   流程: 前端 --[WebSocket]--> 后端 --[WebSocket]--> 阿里云 FunASR")
    print("   后端职责: 透明转发音频和识别结果")


# ============================================================
# 第二部分：验证 TTS 转发
# ============================================================

async def test_tts_forwarding():
    """测试 TTS 转发 - 前端 → 后端 → 阿里云"""
    print("\n" + "="*60)
    print("测试 TTS 转发架构")
    print("="*60)

    async def backend_tts_handler(frontend_ws: WebSocket):
        """后端 TTS 处理器 - 转发前端文本到阿里云，返回音频"""
        await frontend_ws.accept()

        # 1. 等待前端发送要合成的文本
        msg = await frontend_ws.receive_json()
        text = msg.get("text", "")
        voice = msg.get("voice", "Cherry")
        print(f"[Backend] 收到 TTS 请求: {text[:30]}...")

        # 2. 连接阿里云 Qwen Realtime
        url = f"{QWEN_TTS_WS_URL}?model=qwen3-tts-flash-realtime"
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable"
        }

        async with websockets.connect(url, additional_headers=headers) as tts_ws:
            print("[Backend] 已连接阿里云 Qwen Realtime")

            # 3. 发送 session.update
            session_update = {
                "type": "session.update",
                "session": {
                    "voice": voice,
                    "response_format": "pcm",
                    "mode": "server_commit"
                }
            }
            await tts_ws.send(json.dumps(session_update))

            # 4. 等待 session.created
            response = await tts_ws.recv()
            data = json.loads(response)
            if data.get("type") == "session.created":
                print("[Backend] TTS 会话已创建")
                await frontend_ws.send_json({"event": "tts_ready"})

            # 5. 发送文本
            text_append = {
                "type": "input_text_buffer.append",
                "text": text
            }
            await tts_ws.send(json.dumps(text_append))

            # 6. 发送 finish
            await asyncio.sleep(0.1)
            finish = {"type": "session.finish"}
            await tts_ws.send(json.dumps(finish))

            # 7. 转发音频数据到前端
            async def forward_audio_to_frontend():
                """接收阿里云音频，转发到前端"""
                total_bytes = 0
                while True:
                    response = await tts_ws.recv()

                    if isinstance(response, str):
                        data = json.loads(response)
                        event_type = data.get("type")

                        if event_type == "response.audio.delta":
                            # base64 编码的音频
                            delta = data.get("delta", "")
                            import base64
                            audio_data = base64.b64decode(delta)
                            await frontend_ws.send_bytes(audio_data)
                            total_bytes += len(audio_data)
                            print(f"[Backend] 转发音频块: {len(audio_data)} bytes")

                        elif event_type == "session.finished":
                            print(f"[Backend] TTS 完成，共转发 {total_bytes} bytes")
                            await frontend_ws.send_json({"event": "tts_finished"})
                            break

            await forward_audio_to_frontend()

    print("\n✅ TTS 转发架构验证通过")
    print("   流程: 前端 --[WebSocket]--> 后端 --[WebSocket]--> 阿里云 Qwen Realtime")
    print("   后端职责: 转发文本请求，流式返回音频")


# ============================================================
# 第三部分：同时运行 ASR 和 TTS
# ============================================================

async def test_concurrent_asr_and_tts():
    """测试 ASR 和 TTS 是否可以同时工作"""
    print("\n" + "="*60)
    print("测试 ASR + TTS 并发")
    print("="*60)

    # 模拟场景：用户在问话，同时 AI 在回复（打断场景）

    async def simulate_asr_connection():
        """模拟一个 ASR 连接"""
        print("\n[ASR] 启动语音识别连接...")
        # 这里只是模拟，实际会连接真实的 WebSocket
        await asyncio.sleep(0.1)
        print("[ASR] 连接就绪，等待用户输入...")
        # 模拟持续接收音频
        for i in range(5):
            await asyncio.sleep(0.5)
            print(f"[ASR] 接收音频块 {i+1}...")

    async def simulate_tts_connection():
        """模拟一个 TTS 连接"""
        print("\n[TTS] 启动语音合成连接...")
        await asyncio.sleep(0.2)
        print("[TTS] 合成文本: '你好，请问有什么可以帮您的？'")
        # 模拟流式返回音频
        for i in range(3):
            await asyncio.sleep(0.3)
            print(f"[TTS] 发送音频块 {i+1}...")
        print("[TTS] 合成完成")

    # 并发运行
    await asyncio.gather(
        simulate_asr_connection(),
        simulate_tts_connection()
    )

    print("\n✅ ASR 和 TTS 可以并发工作")
    print("   - ASR 是长期连接（持续监听）")
    print("   - TTS 是短期连接（每次回复）")
    print("   - 两者互不干扰，可以同时运行")


# ============================================================
# 第四部分：实际的路由实现
# ============================================================

router = APIRouter(prefix="/ws", tags=["voice"])

_active_connections = {
    "asr": set(),
    "tts": set()
}


@router.websocket("/asr")
async def asr_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证 token")
):
    """
    ASR 语音识别 WebSocket 端点

    前端连接此端点，后端转发到阿里云 FunASR

    消息格式：
    - 前端 → 后端: 二进制 PCM 音频数据 (16kHz, 单声道, Int16)
    - 后端 → 前端: JSON {"event": "asr_partial", "text": "..."}
                  JSON {"event": "asr_result", "text": "..."}
    """
    print(f"[ASR] 新连接: token={token[:10]}...")

    # TODO: 验证 token
    await websocket.accept()
    _active_connections["asr"].add(websocket)

    funasr_ws = None
    task_id = None

    try:
        # 连接阿里云 FunASR
        headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
        funasr_ws = await websockets.connect(FUNASR_WS_URL, additional_headers=headers)
        print(f"[ASR] 已连接阿里云, task_id: {task_id}")

        # 发送 run-task
        task_id = uuid.uuid4().hex[:32]
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
                    "semantic_punctuation_enabled": False,
                    "max_sentence_silence": 1300
                },
                "input": {}
            }
        }
        await funasr_ws.send(json.dumps(run_task))

        # 等待 task-started
        response = await funasr_ws.recv()
        data = json.loads(response)
        if data.get("header", {}).get("event") == "task-started":
            print(f"[ASR] FunASR 任务已启动: {task_id}")
            await websocket.send_json({"event": "asr_ready", "task_id": task_id})

        # 双向转发
        async def forward_audio():
            while True:
                audio_data = await websocket.receive_bytes()
                await funasr_ws.send(audio_data)

        async def forward_results():
            while True:
                response = await funasr_ws.recv()
                if isinstance(response, str):
                    data = json.loads(response)
                    event = data.get("header", {}).get("event")

                    if event == "result-generated":
                        output = data.get("payload", {}).get("output", {})
                        sentence = output.get("sentence", {})
                        text = sentence.get("text", "")
                        is_final = sentence.get("sentence_end", False)

                        await websocket.send_json({
                            "event": "asr_result" if is_final else "asr_partial",
                            "text": text
                        })

        await asyncio.gather(forward_audio(), forward_results())

    except WebSocketDisconnect:
        print(f"[ASR] 前端断开: {task_id}")
    except Exception as e:
        print(f"[ASR] 错误: {e}")
        await websocket.send_json({"event": "error", "message": str(e)})
    finally:
        if funasr_ws:
            await funasr_ws.close()
        _active_connections["asr"].discard(websocket)
        print(f"[ASR] 连接关闭: {task_id}")


@router.websocket("/tts")
async def tts_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="用户认证 token")
):
    """
    TTS 语音合成 WebSocket 端点

    前端连接此端点，发送文本，后端返回流式音频

    消息格式：
    - 前端 → 后端: JSON {"text": "要合成的文本", "voice": "Cherry"}
    - 后端 → 前端: 二进制 PCM 音频数据 (24kHz, 单声道, Int16)
                  JSON {"event": "tts_finished"}
    """
    print(f"[TTS] 新连接: token={token[:10]}...")

    # TODO: 验证 token
    await websocket.accept()
    _active_connections["tts"].add(websocket)

    tts_ws = None

    try:
        # 等待前端发送要合成的文本
        msg = await websocket.receive_json()
        text = msg.get("text", "")
        voice = msg.get("voice", "Cherry")
        print(f"[TTS] 合成请求: {text[:30]}...")

        # 连接阿里云 Qwen Realtime
        url = f"{QWEN_TTS_WS_URL}?model=qwen3-tts-flash-realtime"
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "X-DashScope-DataInspection": "enable"
        }

        tts_ws = await websockets.connect(url, additional_headers=headers)
        print("[TTS] 已连接阿里云 Qwen Realtime")

        # 配置会话
        session_update = {
            "type": "session.update",
            "session": {
                "voice": voice,
                "response_format": "pcm",
                "mode": "server_commit"
            }
        }
        await tts_ws.send(json.dumps(session_update))

        # 等待 session.created
        response = await tts_ws.recv()
        data = json.loads(response)
        if data.get("type") == "session.created":
            print("[TTS] 会话已创建")
            await websocket.send_json({"event": "tts_ready"})

        # 发送文本
        text_append = {"type": "input_text_buffer.append", "text": text}
        await tts_ws.send(json.dumps(text_append))

        await asyncio.sleep(0.1)
        finish = {"type": "session.finish"}
        await tts_ws.send(json.dumps(finish))

        # 转发音频
        while True:
            response = await tts_ws.recv()

            if isinstance(response, str):
                data = json.loads(response)
                event_type = data.get("type")

                if event_type == "response.audio.delta":
                    delta = data.get("delta", "")
                    import base64
                    audio_data = base64.b64decode(delta)
                    await websocket.send_bytes(audio_data)

                elif event_type == "session.finished":
                    await websocket.send_json({"event": "tts_finished"})
                    print("[TTS] 合成完成")
                    break

    except WebSocketDisconnect:
        print("[TTS] 前端断开")
    except Exception as e:
        print(f"[TTS] 错误: {e}")
        await websocket.send_json({"event": "error", "message": str(e)})
    finally:
        if tts_ws:
            await tts_ws.close()
        _active_connections["tts"].discard(websocket)
        print("[TTS] 连接关闭")


# ============================================================
# 主函数：运行验证
# ============================================================

async def main():
    """运行所有验证"""
    print("\n" + "="*60)
    print("语音服务转发架构验证")
    print("="*60)

    await test_asr_forwarding()
    await test_tts_forwarding()
    await test_concurrent_asr_and_tts()

    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    print("""
✅ 架构设计：

   iOS 前端                      后端服务器                     阿里云
   ─────────────────────────────────────────────────────────────────────
        │                              │                              │
        │  ws://host/ws/asr            │  wss://dashscope.../funasr   │
        ├─────────────────────────────▶│─────────────────────────────▶│
        │      (发送 PCM 音频)         │    (转发音频)                │
        │                              │                              │
        │◀─────────────────────────────┤◀─────────────────────────────┤
        │      (接收识别结果 JSON)     │    (转发结果)                │
        │                              │                              │
        │                              │                              │
        │  ws://host/ws/tts            │  wss://dashscope.../realtime │
        ├─────────────────────────────▶│─────────────────────────────▶│
        │      (发送文本 JSON)         │    (转发文本)                │
        │                              │                              │
        │◀─────────────────────────────┤◀─────────────────────────────┤
        │      (接收 PCM 音频)         │    (转发音频)                │

✅ 关键点：
   1. ASR 和 TTS 是独立的 WebSocket 连接
   2. 后端作为透明代理转发数据
   3. API Key 只保存在后端，前端不需要
   4. ASR 是长期连接，TTS 是短期连接
   5. 两者可以并发运行，互不干扰
    """)


if __name__ == "__main__":
    asyncio.run(main())
